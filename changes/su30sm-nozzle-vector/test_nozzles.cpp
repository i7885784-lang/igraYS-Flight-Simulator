#include "su30_nozzles.h"
#include <cassert>
#include <random>
#include <iostream>
using namespace Su30Nozzles;
void settle(State &s,double throttle,bool ab,double p=0,double r=0,double y=0,double speed=80)
{for(int i=0;i<2000;++i)s.update(.01,throttle,ab,true,speed,0,p,r,y,0,0,0);}
int main()
{
 State s;settle(s,.08,false);const double idle=s.opening;
 settle(s,1,false);const double dry=s.opening;assert(dry<.07 && idle>.90);
 assert(!s.readyAfterburner());
 double waiting=0;while(!s.readyAfterburner() && waiting<5){s.update(.01,1,true,true,80,0,0,0,0,0,0,0);waiting+=.01;}assert(waiting>.5 && waiting<3 && s.opening>.70);
 settle(s,1,true);assert(s.opening>.99);
 settle(s,1,false);assert(s.opening<.07);
 settle(s,1,false,1);assert(s.angle[0]>0 && std::abs(s.angle[0]-s.angle[1])<1e-12);
 auto v=s.meanDirection(),m=s.moment(200000);assert(std::abs(v[0])<1e-12 && v[1]<0 && m[0]<0);assert(std::abs(m[1])<1e-9 && std::abs(m[2])<1e-9);
 settle(s,1,false,0,1);m=s.moment(200000);assert(s.angle[0]<0 && s.angle[1]>0 && m[2]>0);
 settle(s,1,false,0,0,1);m=s.moment(200000);assert(s.angle[0]>0 && s.angle[1]<0 && m[1]<0);
 settle(s,1,false,0,0,0);assert(std::abs(s.angle[0])+std::abs(s.angle[1])<1e-12);
 State high;settle(high,1,false,1,0,0,400);State low;settle(low,1,false,1,0,0,40);assert(std::abs(high.angle[0])<std::abs(low.angle[0]));
 State cold;cold.update(.1,0,false,false,0,0,1,1,1,0,0,0);assert(cold.opening==1 && cold.angle[0]==0 && cold.angle[1]==0);
 // Independent analytic force/moment checks for the actual canted geometry.
 State pose;pose.angle={{Limit,-Limit}};
 auto f=pose.meanDirection();auto torque=pose.moment(200000);
 const double fx=200000*std::sin(Cant)*std::sin(Limit);
 const double loss=200000*(std::cos(Limit)-1);
 assert(std::abs(f[0]*200000-fx)<1e-9 && std::abs(f[1])<1e-12);
 assert(std::abs(f[2]-std::cos(Limit))<1e-12);
 assert(std::abs(torque[0]-(-.50023219*loss))<1e-8);
 assert(std::abs(torque[1]-(-8.34445498*fx))<1e-8);
 const double roll=-200000*1.19030109*std::cos(Cant)*std::sin(Limit)+.50023219*fx;
 assert(std::abs(torque[2]-roll)<1e-8);
 // The two differential axes are physically coupled; do not invent pure yaw.
 assert(std::abs(torque[1])>1000 && std::abs(torque[2])>1000);
 // Match the engine's positive NoseUp / YawLeft / bank-rate conventions.
 for(int axis=0;axis<3;++axis)
 {
  State damp;for(int i=0;i<1000;++i)damp.update(.01,1,false,true,80,0,0,0,0,axis==0?.5:0,axis==1?.5:0,axis==2?.5:0);
  const auto t=damp.moment(200000);
  const double acceleration=axis==0?-t[0]:axis==1?t[2]:-t[1];
  assert(acceleration<0); // opposes the positive angular rate
 }
 State alpha;for(int i=0;i<2000;++i)alpha.update(.01,1,false,true,400,30*Pi/180,1,0,0,0,0,0);
 assert(std::abs(alpha.angle[0]-Limit)<1e-10);
 std::mt19937 rng(1730);std::uniform_real_distribution<double> u(-1,1),t(.001,.15);
 for(int i=0;i<20000;++i)
 {
  const auto old=s.angle;const double dt=t(rng);s.update(dt,(u(rng)+1)*.5,u(rng)>0,true,400*(u(rng)+1)*.5,u(rng)*.7,u(rng),u(rng),u(rng),u(rng),u(rng),u(rng));
  assert(std::isfinite(s.opening) && s.opening>=0 && s.opening<=1);
  for(int j=0;j<2;++j){assert(std::abs(s.angle[j])<=Limit+1e-12);assert(std::abs(s.angle[j]-old[j])<=Slew*dt+1e-12);const auto d=direction(j,s.angle[j]);assert(std::abs(d[0]*d[0]+d[1]*d[1]+d[2]*d[2]-1)<1e-12);const auto f=sample(s.angle[j]);assert(f.low>=0 && f.high<=60 && f.fraction>=0 && f.fraction<=1);}
 }
 std::cout<<"PASS: dry/idle/reheat schedule, axis signs, common/differential moments, neutral, speed authority, 20000 bounded actuator steps\n";
}
