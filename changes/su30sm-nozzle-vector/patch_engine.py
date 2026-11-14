"""Patch only the accepted test3 engine; never overwrite hard-linked originals."""
from pathlib import Path
import sys,hashlib,json
root=Path(sys.argv[1]);stage=Path(__file__).resolve().parent
cpp=root/'YSFLIGHT/src/vehicle/fsairplaneproperty.cpp';header=cpp.with_suffix('.h');log=root/'YSFLIGHT/src/ui/fsrunloop.cpp'
def put(p,data):
 if p.exists():p.unlink()
 p.write_text(data)
def replace(s,a,b):
 assert s.count(a)==1,(a[:80],s.count(a));return s.replace(a,b)
h=header.read_text();h=replace(h,'#include "fsrealprop.h"','#include "fsrealprop.h"\n#include "su30_nozzles.h"')
h=replace(h,'double GetNozzleOpening() const { return staNozzleOpening; }','double GetNozzleOpening() const { return staNozzleOpening; }\n double GetSu30NozzleAngle(int engine) const { return su30Nozzles.angle[engine==0?0:1]; }')
h=replace(h,'    bool intakeProtectionCommand=false;','    Su30Nozzles::State su30Nozzles;\n    bool intakeProtectionCommand=false;');h=replace(h,'double GetSu30NozzleAngle(int engine) const { return su30Nozzles.angle[engine==0?0:1]; }','double GetSu30NozzleAngle(int engine) const { return su30Nozzles.angle[engine==0?0:1]; }\n#ifdef V861_VALIDATION\n void SetSu30NozzleTestPose(double left,double right,double opening)\n {\n  su30Nozzles.angle[0]=Su30Nozzles::bound(left,-Su30Nozzles::Limit,Su30Nozzles::Limit);\n  su30Nozzles.angle[1]=Su30Nozzles::bound(right,-Su30Nozzles::Limit,Su30Nozzles::Limit);\n  staNozzleOpening=su30Nozzles.opening=Su30Nozzles::bound(opening,0,1);\n }\n#endif\n');put(header,h)
s=cpp.read_text();s=replace(s,'staNozzleOpening=1.0;staIntakeProtection=', 'su30Nozzles.reset();staNozzleOpening=1.0;staIntakeProtection=')
s=replace(s,'    approach(staNozzleOpening,target,.45);', '''    if(su30)
    {
        const bool running=(GetFuelLeft()>0.0 && IsActive()==YSTRUE && staPowerLoss!=YSTRUE);
        su30Nozzles.update(dt,staThrottle,YSTRUE==ctlAb && staThrottle>.90,running,staV,staAOA,
                          YsBound(ctlElevator+ctlElvTrim,-1.0,1.0),ctlAileron,GetRudder(),staVPitch,staVRoll,staVYaw);
        staNozzleOpening=su30Nozzles.opening;
    }
    else approach(staNozzleOpening,target,.45);''')
s=replace(s,'\tYsVec3 vThrust;\n\tif(chHasThrustVector!=YSTRUE)', '''\tYsVec3 vThrust;
    if(0==strcmp(GetIdentifier(),"SU-30SM_CUSTOM"))
    {
        const auto d=su30Nozzles.meanDirection();vThrust.Set(d[0],d[1],d[2]);
    }
\telse if(chHasThrustVector!=YSTRUE)''')
s=replace(s,'\t\t\tstaMatrix.Mul(vThrTfm,vThrust,0.0);','''            YsVec3 unitThrust=vThrust;if(0==strcmp(GetIdentifier(),"SU-30SM_CUSTOM"))unitThrust.Normalize();
\t\t\tstaMatrix.Mul(vThrTfm,unitThrust,0.0);''')
s=replace(s,'\t\tstaDVRoll=(inputROLL-staVRoll)*kRoll;', '''\t\tstaDVRoll=(inputROLL-staVRoll)*kRoll;
        // Only the incremental nozzle moment; retain the original neutral trim.
        if(0==strcmp(GetIdentifier(),"SU-30SM_CUSTOM") && IsOnGround()!=YSTRUE && staThrust>0.0)
        {
            const auto m=su30Nozzles.moment(staThrust);
            const double mass=YsGreater(1.0,GetTotalWeight());
            // Radius-of-gyration estimates, not measured factory inertia data.
            const double iPitch=mass*(.26*21.94)*(.26*21.94),iRoll=mass*(.20*14.70)*(.20*14.70);
            staDVPitch-=m[0]/iPitch;staDVYaw-=m[1]/iPitch;staDVRoll+=m[2]/iRoll;
        }''')
s=replace(s,'   const double actuatorStep=YsBound(staSpoiler,0.0,1.0)*20.0;', '''   for(int engine=0;engine<2;++engine)
   {
       const auto frame=Su30Nozzles::sample(su30Nozzles.angle[engine]);
       vis.SetState(280+engine,frame.low,frame.high,frame.fraction);
   }
   const double actuatorStep=YsBound(staSpoiler,0.0,1.0)*20.0;''')
s=replace(s,'void FsAirplaneProperty::GetThrustDirection(YsVec3 &dir) const\n{', '''void FsAirplaneProperty::GetThrustDirection(YsVec3 &dir) const
{
    if(0==strcmp(GetIdentifier(),"SU-30SM_CUSTOM"))
    {
        const auto d=su30Nozzles.meanDirection();dir.Set(d[0],d[1],d[2]);dir.Normalize();return;
    }''');s=replace(s,'\tCalculateCurrentState();\n\tCalculateFuelConsumption(dt);','    // Su-30 reheat admission waits for the variable-area nozzle to open.\n    if(0==strcmp(GetIdentifier(),"SU-30SM_CUSTOM") && staAb==YSTRUE &&\n       (staThrottle<.90 || !su30Nozzles.readyAfterburner()))staAb=YSFALSE;\n\tCalculateCurrentState();\n\tCalculateFuelConsumption(dt);');put(cpp,s)
# Actual angle telemetry in the existing validation-only MODELCHECK command.
s=log.read_text();assert 'tvLdeg=' not in s;s=s.replace('nozzle=%.6f intake=%.6f','nozzle=%.6f tvLdeg=%.6f tvRdeg=%.6f intake=%.6f').replace('p.GetNozzleOpening(),p.GetIntakeProtection()', 'p.GetNozzleOpening(),p.GetSu30NozzleAngle(0)*180.0/YsPi,p.GetSu30NozzleAngle(1)*180.0/YsPi,p.GetIntakeProtection()');assert 'tvLdeg=' in s;s=replace(s,' if(labSim && labArgs.GetN()>=7 && 0==labArgs[0].STRCMP("MODELPOSE"))',' if(labSim && labArgs.GetN()>=4 && 0==labArgs[0].STRCMP("NOZZLEPOSE")){\n  if(auto a=labSim->GetPlayerAirplane()){a->Prop().SetSu30NozzleTestPose(atof(labArgs[1])*YsPi/180.0,atof(labArgs[2])*YsPi/180.0,atof(labArgs[3]));}return;\n }\n if(labSim && labArgs.GetN()>=7 && 0==labArgs[0].STRCMP("MODELPOSE"))');put(log,s)
put(root/'YSFLIGHT/src/vehicle/su30_nozzles.h',(stage/'su30_nozzles.h').read_text())
print('Patched isolated engine',root)

render=root/'public/src/ysgebl/src/shellrender/ysvisual.cpp'
s=render.read_text()
s=replace(s,'114==node->dnmClassType || 115==node->dnmClassType)\n    {','114==node->dnmClassType || 115==node->dnmClassType || 284==node->dnmClassType || 285==node->dnmClassType)\n    {')
s=replace(s,'((114==node->dnmClassType || 115==node->dnmClassType)?(.94/1.56):1.0)','((114==node->dnmClassType || 115==node->dnmClassType)?(.94/1.56):((284==node->dnmClassType || 285==node->dnmClassType)?(.94/1.08):1.0))')
s=replace(s,'        renderTfm.Scale(p.sx,p.sy,1.0);','        // The existing lining lip was 1.08 times the open exit radius.\n        // Seat it beneath the metal lip throughout aperture changes.\n        if(284==node->dnmClassType || 285==node->dnmClassType)\n            renderTfm.Scale(p.sx*(1.01/1.08),p.sy*(1.01/1.08),1.0);\n        else renderTfm.Scale(p.sx,p.sy,1.0);')
put(render,s)
