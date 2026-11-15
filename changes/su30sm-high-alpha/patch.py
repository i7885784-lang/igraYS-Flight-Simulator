from pathlib import Path
import sys,hashlib
root=Path(sys.argv[1]);stage=Path(__file__).resolve().parent
def patch(rel,a,b):
 p=root/rel;s=p.read_text();assert s.count(a)==1,(rel,a[:80],s.count(a));s=s.replace(a,b);p.unlink();p.write_text(s)
def put(rel,s):
 p=root/rel
 if p.exists():p.unlink()
 p.write_text(s)
patch('YSFLIGHT/src/vehicle/fsairplaneproperty.h','#include "su30_nozzles.h"','#include "su30_nozzles.h"\n#include "su30_high_alpha.h"')
patch('YSFLIGHT/src/vehicle/fsairplaneproperty.h','double GetNozzleOpening() const { return staNozzleOpening; }','double GetNozzleOpening() const { return staNozzleOpening; }\n bool IsSu30HighAlphaMode() const { return su30HighAlphaMode; }\n void SetSu30HighAlphaMode(bool value) {su30HighAlphaMode=value;}')
patch('YSFLIGHT/src/vehicle/fsairplaneproperty.h','    Su30Nozzles::State su30Nozzles;','    bool su30HighAlphaMode=false, su30HaveAoaSample=false;\n    double su30PreviousAoa=0, su30AoaRate=0;\n    Su30Nozzles::State su30Nozzles;')
patch('YSFLIGHT/src/vehicle/fsairplaneproperty.cpp','su30Nozzles.reset();staNozzleOpening=','su30HighAlphaMode=false;su30HaveAoaSample=false;su30AoaRate=0;su30PreviousAoa=0;su30Nozzles.reset();staNozzleOpening=')
patch('YSFLIGHT/src/vehicle/fsairplaneproperty.cpp','\t\t\tstaDVPitch=(inputAOA-staAOA)*kPitch-staVPitch*bPitch;','''\t\t\tstaDVPitch=(inputAOA-staAOA)*kPitch-staVPitch*bPitch;
            if(su30HighAlphaMode && 0==strcmp(GetIdentifier(),"SU-30SM_CUSTOM") && IsOnGround()!=YSTRUE &&
               ctlGControllerSwitch!=YSTRUE && ctlAOAControllerSwitch!=YSTRUE && ctlPitchControllerSwitch!=YSTRUE)
                staDVPitch=Su30HighAlpha::acceleration(staV,staAOA,staVPitch,YsBound(ctlElevator+ctlElvTrim,-1.0,1.0),staDVPitch,su30AoaRate,su30AoaLimitDeg*YsPi/180);''')
patch('YSFLIGHT/src/vehicle/fsairplaneproperty.cpp',
      '                          YsBound(ctlElevator+ctlElvTrim,-1.0,1.0),ctlAileron,GetRudder(),staVPitch,staVRoll,staVYaw);',
      '                          (su30HighAlphaMode && IsOnGround()!=YSTRUE && ctlGControllerSwitch!=YSTRUE && ctlAOAControllerSwitch!=YSTRUE && ctlPitchControllerSwitch!=YSTRUE ? Su30HighAlpha::nozzlePitch(staV,staAOA,su30AoaRate,YsBound(ctlElevator+ctlElvTrim,-1.0,1.0),su30AoaLimitDeg*YsPi/180) : YsBound(ctlElevator+ctlElvTrim,-1.0,1.0)),ctlAileron,GetRudder(),staVPitch,staVRoll,staVYaw);')
patch('YSFLIGHT/src/vehicle/fsairplaneproperty.cpp',
      '        su30Nozzles.update(dt,staThrottle,YSTRUE==ctlAb && staThrottle>.90,running,staV,staAOA,',
      '        su30AoaRate=su30HaveAoaSample?std::remainder(staAOA-su30PreviousAoa,2*YsPi)/dt:staVPitch;\n        su30PreviousAoa=staAOA;su30HaveAoaSample=true;\n        su30Nozzles.update(dt,staThrottle,YSTRUE==ctlAb && staThrottle>.90,running,staV,staAOA,')
patch('YSFLIGHT/src/core/fssimulation.cpp','                if(mainWindowViewmode==FSCOCKPITVIEW && rawKey==FSKEY_SPACE)continue;','''                if(rawKey==FSKEY_L && FsGetKeyState(FSKEY_CTRL)==YSTRUE && GetPlayerAirplane() &&
                   0==strcmp(GetPlayerAirplane()->Prop().GetIdentifier(),"SU-30SM_CUSTOM"))
                {
                    if(subMenu.GetSubMenu()==FSSUBMENU_INFLTCONFIG)subMenu.SetSubMenu(this,FSSUBMENU_NONE);
                    auto &p=GetPlayerAirplane()->Prop();
                    if(p.IsSu30HighAlphaMode() && fabs(p.GetAOA())>YsDegToRad(25.0))
                    {AddTimedMessage("Reduce AOA below 25 deg before re-engaging limiter");SetIgnoreThisKeyHolding(rawKey);continue;}
                    if(!p.IsSu30HighAlphaMode() && (p.IsOnGround()==YSTRUE || p.GetVelocity()>200.0))
                    {AddTimedMessage("AOA override: airborne below 720 km/h only");SetIgnoreThisKeyHolding(rawKey);continue;}
                    p.SetSu30HighAlphaMode(!p.IsSu30HighAlphaMode());
                    AddTimedMessage(p.IsSu30HighAlphaMode()?"Su-30: AOA limiter RELEASED (Ctrl+L)":"Su-30: normal AOA control (Ctrl+L)");
                    printf("SU30_HIGH_ALPHA enabled=%d\\n",int(p.IsSu30HighAlphaMode()));fflush(stdout);
                    SetIgnoreThisKeyHolding(rawKey);continue;
                }
                if(mainWindowViewmode==FSCOCKPITVIEW && rawKey==FSKEY_SPACE)continue;''')
patch('YSFLIGHT/src/ui/fsrunloop.cpp','nozzle=%.6f tvLdeg=','aoaDeg=%.6f pitchRate=%.6f highAlpha=%d nozzle=%.6f tvLdeg=')
patch('YSFLIGHT/src/ui/fsrunloop.cpp','p.GetNozzleOpening(),p.GetSu30NozzleAngle(0)','p.GetAOA()*180.0/YsPi,([&](){YsAtt3 r;p.GetRotationSpeed(r);return r.p()*180.0/YsPi;})(),int(p.IsSu30HighAlphaMode()),p.GetNozzleOpening(),p.GetSu30NozzleAngle(0)')
put('YSFLIGHT/src/vehicle/su30_high_alpha.h',(stage/'su30_high_alpha.h').read_text())

patch('YSFLIGHT/src/vehicle/fsairplaneproperty.h',
 ' void SetSu30HighAlphaMode(bool value) {su30HighAlphaMode=value;}',
 ' void SetSu30HighAlphaMode(bool value) {su30HighAlphaMode=value;}\n bool su30AoaPanel=false;\n double su30AoaLimitDeg=65.0;\n void SetSu30AoaLimit(double value) {su30AoaLimitDeg=YsBound(value,30.0,110.0);}')
patch('YSFLIGHT/src/vehicle/fsairplaneproperty.cpp',
 'su30HighAlphaMode=false;su30HaveAoaSample=false;',
 'su30AoaPanel=false;su30AoaLimitDeg=65.0;su30HighAlphaMode=false;su30HaveAoaSample=false;')
patch('YSFLIGHT/src/core/fssimulation.cpp',
 '                if(rawKey==FSKEY_L && FsGetKeyState(FSKEY_CTRL)==YSTRUE && GetPlayerAirplane() &&',
 '                if(GetPlayerAirplane() && 0==strcmp(GetPlayerAirplane()->Prop().GetIdentifier(),"SU-30SM_CUSTOM"))\n                {\n                    auto &p=GetPlayerAirplane()->Prop();\n                    if(rawKey==FSKEY_L && FsGetKeyState(FSKEY_CTRL)==YSTRUE && FsGetKeyState(FSKEY_SHIFT)==YSTRUE)\n                    {\n                        p.su30AoaPanel=!p.su30AoaPanel;\n                        printf("SU30_AOA_PANEL open=%d limit=%.0f\\n",int(p.su30AoaPanel),p.su30AoaLimitDeg);fflush(stdout);\n                        SetIgnoreThisKeyHolding(rawKey);continue;\n                    }\n                    if(p.su30AoaPanel && (rawKey==FSKEY_F7 || rawKey==FSKEY_F8 || rawKey==FSKEY_F9))\n                    {\n                        p.SetSu30AoaLimit(rawKey==FSKEY_F9?65.0:p.su30AoaLimitDeg+(rawKey==FSKEY_F8?5.0:-5.0));\n                        printf("SU30_AOA_PANEL open=1 limit=%.0f\\n",p.su30AoaLimitDeg);fflush(stdout);\n                        SetIgnoreThisKeyHolding(rawKey);continue;\n                    }\n                }\n                if(rawKey==FSKEY_L && FsGetKeyState(FSKEY_CTRL)==YSTRUE && GetPlayerAirplane() &&')
patch('YSFLIGHT/src/core/fssimulation.cpp',
 ' if(Su27Cockpit(GetPlayerAirplane()) && mainWindowViewmode==FSCOCKPITVIEW){',
 ' if(GetPlayerAirplane() && 0==strcmp(GetPlayerAirplane()->Prop().GetIdentifier(),"SU-30SM_CUSTOM") && GetPlayerAirplane()->Prop().su30AoaPanel && YSTRUE==FsIsMainWindowActive())\n {\n  FsSet2DDrawing();int w,h;FsGetWindowSize(w,h);const auto &p=GetPlayerAirplane()->Prop();\n  const int x=YsGreater(4,w-370),y=80;\n  FsDrawRect(x,y,x+360,y+130,YsBlack(),YSTRUE);\n  FsDrawRect(x,y,x+360,y+130,YsWhite(),YSFALSE);\n  FsDrawString(x+10,y+22,L"Су-30СМ: настройка пилотажа",YsWhite());\n  wchar_t text[160];swprintf(text,160,L"Предел: %.0f° | Сейчас: %.1f°",p.su30AoaLimitDeg,p.GetAOA()*180/YsPi);FsDrawString(x+10,y+47,text,YsWhite());\n  FsDrawString(x+10,y+72,p.IsSu30HighAlphaMode()?L"Ctrl+L: манёвренный режим":L"Ctrl+L: обычный режим",YsWhite());\n  FsDrawString(x+10,y+97,L"F7 −5° | F8 +5° | F9 сброс 65°",YsWhite());\n  FsDrawString(x+10,y+120,L"Ctrl+Shift+L: закрыть | Диапазон 30–110°",YsWhite());\n }\n if(Su27Cockpit(GetPlayerAirplane()) && mainWindowViewmode==FSCOCKPITVIEW){')
print('Patched high-alpha manual control; no geometry/aircraft DAT changes')
