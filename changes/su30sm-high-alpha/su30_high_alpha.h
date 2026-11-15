#ifndef SU30_HIGH_ALPHA_INCLUDED
#define SU30_HIGH_ALPHA_INCLUDED
#include <cmath>
#include <algorithm>
// Explicit manual limiter override. Game model, not factory Su-30 flight software.
namespace Su30HighAlpha {
constexpr double Pi=3.14159265358979323846;
inline double clamp(double x,double a,double b){return std::max(a,std::min(b,x));}
inline double smooth(double x){x=clamp(x,0,1);return x*x*(3-2*x);}
inline double acceleration(double speed,double alpha,double rate,double stick,double normal)
{
 const double entry=smooth((220.0-speed)/40.0);
 const double recovery=smooth((std::abs(alpha)*180/Pi-25)/20);
 const double blend=std::max(entry,recovery);
 const double aero=clamp(speed*speed/(80.0*80.0),0,1);
 stick=clamp(stick,-1,1);
 // Stick commands rotation rate after limiter release, rather than a 23deg AOA target.
 double demand=stick*65*Pi/180;
 if(stick>0)demand*=1-smooth((alpha*180/Pi-105)/20);
 if(stick<0)demand*=1-smooth((-alpha*180/Pi-30)/15);
 // Neutral stick retains a bounded aerodynamic restoring tendency.
 demand+=(1-std::abs(stick))*(1-std::abs(stick))*clamp(-1.2*alpha,-.9,.9);
 const double direct=aero*clamp(4.0*(demand-rate),-140*Pi/180,140*Pi/180);
 return normal+(direct-normal)*blend;
}
}
#endif
