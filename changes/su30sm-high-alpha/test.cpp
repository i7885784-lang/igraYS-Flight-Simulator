#include "su30_high_alpha.h"
#include <cassert>
#include <iostream>
using namespace Su30HighAlpha;
int main(){
 for(double v:{0.,40.,80.,166.67,200.,250.})for(double a:{-.8,0.,.4,1.,1.9,2.2})for(double r:{-1.,0.,1.})for(double s:{-1.,0.,1.}){
  double x=acceleration(v,a,r,s,0);assert(std::isfinite(x));assert(std::abs(x)<=140*Pi/180+1e-12);
 }
 assert(acceleration(166.67,0,0,1,0)>0);
 assert(acceleration(166.67,0,0,-1,0)<0);
 assert(acceleration(166.67,1.8,0,0,0)<0);
 assert(acceleration(166.67,2.2,.5,1,0)<0);
 assert(acceleration(0,0,0,1,0)==0);
 assert(acceleration(250,0,0,1,.123)==.123);
 // A simplified fixed-flight-path longitudinal response, not the in-game Cobra proof.
 double a=0,r=0;double peak=0;
 for(int i=0;i<1600;++i){const double dt=.005;double stick=i<400?1:0;r+=acceleration(166.67,a,r,stick,0)*dt;a+=r*dt;peak=std::max(peak,a);}
 std::cout<<"peak="<<peak*180/Pi<<" final="<<a*180/Pi<<std::endl;
 assert(peak>Pi/2 && peak<130*Pi/180 && std::abs(a)<.4);
 std::cout<<"PASS bounded acceleration, sign, damping/restoring, low-speed authority, overspeed normal fallback, recovery; fixed-path peak "<<peak*180/Pi<<"deg\n";
}
