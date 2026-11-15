#ifndef SU30_HIGH_ALPHA_INCLUDED
#define SU30_HIGH_ALPHA_INCLUDED
#include <cmath>
#include <algorithm>
// Explicit manual limiter override. Game model, not factory Su-30 flight software.
namespace Su30HighAlpha {
constexpr double Pi=3.14159265358979323846;
inline double clamp(double x,double a,double b){return std::max(a,std::min(b,x));}
inline double smooth(double x){x=clamp(x,0,1);return x*x*(3-2*x);}
constexpr double PositiveLimit=110*Pi/180;
constexpr double PositiveSoftStart=95*Pi/180;
// Reserve stopping distance and input/actuator response time before the AOA boundary.
inline double positiveGate(double speed,double alpha,double rate)
{
 const double aero=clamp(speed*speed/(80.0*80.0),0,1);
 const double up=std::max(0.0,rate);
 const double stopping=up*.25+up*up/(2*std::max(.15,aero*140*Pi/180));
 return 1-smooth((alpha+stopping-PositiveSoftStart)/(PositiveLimit-PositiveSoftStart));
}
inline double nozzlePitch(double speed,double alpha,double rate,double stick)
{
 double command=stick>0?stick*positiveGate(speed,alpha,rate):stick;
 const double boundary=smooth((alpha-(PositiveLimit-4*Pi/180))/(4*Pi/180));
 // A held nose-up stick must not keep adding TVC pitch torque past the boundary.
 if(rate>0 || alpha>PositiveLimit)command=std::min(command,-boundary*clamp(.8*std::max(0.0,rate)+.2,0,1));
 return clamp(command,-1,1);
}
inline double acceleration(double speed,double alpha,double rate,double stick,double normal,double alphaRate)
{
 const double entry=smooth((220.0-speed)/40.0);
 const double recovery=smooth((std::abs(alpha)*180/Pi-25)/20);
 const double blend=std::max(entry,recovery);
 const double aero=clamp(speed*speed/(80.0*80.0),0,1);
 stick=clamp(stick,-1,1);
 // Stick commands rotation rate after limiter release, rather than a 23deg AOA target.
 double demand=stick*65*Pi/180;
 if(stick>0)demand=std::min(demand,65*Pi/180*positiveGate(speed,alpha,alphaRate)+rate-alphaRate);
 if(stick<0)demand*=1-smooth((-alpha*180/Pi-30)/15);
 // Neutral stick retains a bounded aerodynamic restoring tendency.
 demand+=(1-std::abs(stick))*(1-std::abs(stick))*clamp(-1.2*alpha,-.9,.9);
 double direct=aero*clamp(4.0*(demand-rate),-140*Pi/180,140*Pi/180);
 if(alpha>PositiveLimit-2*Pi/180 && alphaRate>0)
  direct=std::min(direct,-aero*140*Pi/180*smooth((alpha-(PositiveLimit-2*Pi/180))/(2*Pi/180)));
 return normal+(direct-normal)*blend;
}
}
#endif
