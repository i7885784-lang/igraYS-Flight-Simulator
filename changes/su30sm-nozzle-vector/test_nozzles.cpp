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
 std::mt19937 rng(1730);std::uniform_real_distribution<double> u(-1,1),t(.001,.15);
 for(int i=0;i<20000;++i)
 {
  const auto old=s.angle;const double dt=t(rng);s.update(dt,(u(rng)+1)*.5,u(rng)>0,true,400*(u(rng)+1)*.5,u(rng)*.7,u(rng),u(rng),u(rng),u(rng),u(rng),u(rng));
  assert(std::isfinite(s.opening) && s.opening>=0 && s.opening<=1);
  for(int j=0;j<2;++j){assert(std::abs(s.angle[j])<=Limit+1e-12);assert(std::abs(s.angle[j]-old[j])<=Slew*dt+1e-12);const auto d=direction(j,s.angle[j]);assert(std::abs(d[0]*d[0]+d[1]*d[1]+d[2]*d[2]-1)<1e-12);const auto f=sample(s.angle[j]);assert(f.low>=0 && f.high<=60 && f.fraction>=0 && f.fraction<=1);}
 }
 std::cout<<"PASS: dry/idle/reheat schedule, axis signs, common/differential moments, neutral, speed authority, 20000 bounded actuator steps\n";
}
