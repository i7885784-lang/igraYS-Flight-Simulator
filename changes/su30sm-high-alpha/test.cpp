#include "su30_high_alpha.h"
#include "../su30sm-nozzle-vector/su30_nozzles.h"
#include <cassert>
#include <iostream>
using namespace Su30HighAlpha;
double exercise(double speed,double dt,bool release,double flowRate=0,double limit=PositiveLimit){
 Su30Nozzles::State nozzles;double alpha=0,rate=0,peak=0;
 for(int i=0;i<int(18/dt);++i){
  const double stick=release&&i*dt>10?0:1;
  nozzles.update(dt,.9,false,true,speed,alpha,nozzlePitch(speed,alpha,rate-flowRate,stick,limit),0,0,rate,0,0);
  const auto m=nozzles.moment(200000);
  const double torque=-m[0]/(26000*(.26*21.94)*(.26*21.94));
  rate+=(acceleration(speed,alpha,rate,stick,0,rate-flowRate,limit)+torque)*dt;
  alpha+=(rate-flowRate)*dt;peak=std::max(peak,alpha);
 }
 assert(peak>limit-10*Pi/180 && peak<=limit+.5*Pi/180);
 if(release)assert(std::abs(alpha)<10*Pi/180);
 return peak*180/Pi;
}
int main(){
 double rate=0,angle=0;const double dt=.01;
 for(int i=0;i<250;++i){double t=i*dt;double stick=t<.5?2*t:(t<.72?1-(t-.5)*4.5:0);rate+=rollAcceleration(stick,rate,1)*dt;angle+=rate*dt;}
 assert(std::abs(rate)<.001 && angle>10*Pi/180 && angle<45*Pi/180);
 for(double z:{-1e-8,0.,1e-8})assert(std::abs(sideslip(.001,-1,z))<.002);
 assert(rollAcceleration(0,.5,1)<0 && rollDemand(.2)<10*Pi/180);
 std::cout<<"PASS manual roll pulse/release and sideslip across vertical/backwards flow\n";
 double peak=0;
 for(double speed:{80.,166.67})for(double dt:{.005,.02,.04}){peak=std::max(peak,exercise(speed,dt,false));peak=std::max(peak,exercise(speed,dt,false,-3*Pi/180));}
 assert(nozzlePitch(166.67,112*Pi/180,.3,1)<0);
 std::cout<<"PASS 1: held full pitch including TVC; maximum "<<peak<<" deg\n";
 for(double dt:{.005,.02,.04})exercise(166.67,dt,true);
 assert(acceleration(250,0,0,1,.123,0)==.123);
 assert(acceleration(166.67,0,0,-1,0,0)<0);
 for(double limit:{30.,65.,110.})exercise(166.67,.02,true,0,limit*Pi/180);
 std::cout<<"PASS 2: recovery on release; negative command and normal overspeed path preserved\n";
}
