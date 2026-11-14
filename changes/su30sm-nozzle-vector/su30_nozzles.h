#ifndef SU30_NOZZLES_INCLUDED
#define SU30_NOZZLES_INCLUDED
#include <array>
#include <algorithm>
#include <cmath>
// Local game approximation, not a factory FADEC/FCS implementation.
namespace Su30Nozzles
{
constexpr double Pi=3.14159265358979323846,Limit=15*Pi/180,Cant=32*Pi/180;
constexpr double Slew=15*Pi/180;
inline double bound(double x,double a,double b){return std::max(a,std::min(b,x));}
inline double smooth(double x){x=bound(x,0,1);return x*x*(3-2*x);}
inline double toward(double x,double target,double rate,double dt){return x+bound(target-x,-rate*dt,rate*dt);}
inline std::array<double,3> pivot(int i){return {{i==0?1.19030109:-1.19030109,-.50023219,-8.34445498}};}
inline std::array<double,3> direction(int i,double a)
{
 const double s=(i==0?1.0:-1.0);
 return {{s*std::sin(Cant)*std::sin(a),-std::cos(Cant)*std::sin(a),std::cos(a)}};
}
struct State
{
 double spool=.58,opening=1,afterburner=0;
 std::array<double,2> angle{{0,0}};
 void reset(){*this=State();}
 bool readyAfterburner() const {return spool>.90 && opening>.70;}
 void update(double dt,double throttle,bool ab,bool running,double speed,double aoa,
             double pitch,double roll,double yaw,double pitchRate,double rollRate,double yawRate)
 {
  if(!(dt>0) || !std::isfinite(dt))return;
  throttle=bound(throttle,0,1);const double power=running?(.58+.42*throttle):0;
  spool=power+(spool-power)*std::exp(-dt/(power>spool?1.15:.8));
  afterburner=toward(afterburner,(ab&&running&&spool>.90)?1.0:0.0,ab?2.0:1.2,dt);
  if(running)
  {
   // Open at idle, contract progressively on dry power, reopen on reheat.
   const double load=bound((spool-.58)/.42,0,1);
   const double dry=.95-.89*smooth((load-.08)/.92);
   const double target=dry+(1.0-dry)*afterburner;
   opening=toward(opening,target,target>opening?.75:.45,dt);
  }
  const double pressure=smooth((spool-.20)/.35);
  const double speedGain=.20+.80/(1.0+(speed/160.0)*(speed/160.0));
  const double highAlpha=smooth((std::abs(aoa)*180/Pi-12)/13);
  const double authority=pressure*(speedGain+(1-speedGain)*highAlpha);
  // Two canted, single-axis nozzles: common pitch + differential roll/yaw.
  const double p=bound(pitch-.08*pitchRate,-1,1);
  const double d=bound(-.60*(roll-.08*rollRate)+.40*(yaw-.08*yawRate),-1,1);
  double commands[2]={p+d,p-d};const double scale=std::max(1.0,std::max(std::abs(commands[0]),std::abs(commands[1])));
  for(int i=0;i<2;++i)
  {
   const double target=running?Limit*authority*commands[i]/scale:0;
   angle[i]=toward(angle[i],target,Slew*pressure,dt);
   angle[i]=bound(angle[i],-Limit,Limit);
  }
  opening=bound(opening,0,1);
 }
 std::array<double,3> meanDirection() const
 {
  const auto a=direction(0,angle[0]),b=direction(1,angle[1]);
  return {{(a[0]+b[0])*.5,(a[1]+b[1])*.5,(a[2]+b[2])*.5}};
 }
 // Incremental r x F, relative to the old neutral axial-thrust trim.
 std::array<double,3> moment(double totalThrust) const
 {
  std::array<double,3> m{{0,0,0}};
  for(int i=0;i<2;++i)
  {
   const auto r=pivot(i),d=direction(i,angle[i]);
   const double fx=d[0]*totalThrust*.5,fy=d[1]*totalThrust*.5,fz=(d[2]-1)*totalThrust*.5;
   m[0]+=r[1]*fz-r[2]*fy;m[1]+=r[2]*fx-r[0]*fz;m[2]+=r[0]*fy-r[1]*fx;
  }
  return m;
 }
};
struct Sample {int low,high;double fraction;};
inline Sample sample(double angle)
{
 const double u=std::abs(bound(angle,-Limit,Limit))/Limit*30;
 const int i=std::min(29,int(u));
 return angle>=0?Sample{i,i+1,u-i}:Sample{i==0?0:30+i,31+i,u-i};
}
}
#endif
