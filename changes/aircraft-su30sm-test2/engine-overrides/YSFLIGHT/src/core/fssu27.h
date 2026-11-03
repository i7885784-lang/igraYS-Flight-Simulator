#ifndef FS_SU27_DETAIL_INCLUDED
#define FS_SU27_DETAIL_INCLUDED
// Local, intentionally simplified cockpit systems. Not a real Su-27 checklist.
namespace {
struct Su27ClickCache {const FsAirplane *air=nullptr;double clock=-100;YsVec2 center[6];double radius[6]={0};bool click=false,dragging=false;int lastX=0,lastY=0,restoreX=0,restoreY=0;} su27Ui;
bool Su27Aircraft(const FsAirplane *a){return a && 0==strcmp(a->Prop().GetIdentifier(),"SU-27_FLANKER");}
bool Su27Cockpit(const FsAirplane *){return false;} // Test6: native open cockpit, no custom start panel.
bool DetailedAircraft(const FsAirplane *a){return Su27Aircraft(a) || (a && (0==strcmp(a->Prop().GetIdentifier(),"MIG-29_FULCRUM") || 0==strcmp(a->Prop().GetIdentifier(),"SU-57_FELON") || 0==strcmp(a->Prop().GetIdentifier(),"SU-47_BERKUT") || 0==strcmp(a->Prop().GetIdentifier(),"SU-34_FULLBACK") || 0==strcmp(a->Prop().GetIdentifier(),"SU-30SM_CUSTOM")));}
YsVec3 Su27Button(int i){return YsVec3(-.535,1.466-i*.105,5.838);}
void Su27Action(FsSimulation *sim,int id)
{
 auto a=sim->GetPlayerAirplane();if(!DetailedAircraft(a) || a->isPlayingRecord==YSTRUE)return;auto &p=a->Prop();
 if(id!=4)return;
 switch(id){
 case 0:p.su27Battery=!p.su27Battery;break;
 case 1:p.su27Pumps=!p.su27Pumps;if(!p.su27Pumps)p.su27Left=p.su27Right=false;break;
 case 2:case 3:
  if(!p.su27Battery || !p.su27Pumps || p.GetFuelLeft()<=0){sim->AddTimedMessage(L"Для запуска включи АКБ и насосы. Проверь топливо.");return;}
  if(id==2)p.su27Left=!p.su27Left;else p.su27Right=!p.su27Right;break;
 case 4:if(0==strcmp(p.GetIdentifier(),"SU-34_FULLBACK")){sim->AddTimedMessage(L"Су-34: остекление кабины неподвижное.");return;}if(p.GetVelocity()>35.0 && p.su27CanopyTarget<.5){sim->AddTimedMessage(L"Открывай фонарь на стоянке или при медленном рулении.");return;}p.su27CanopyTarget=p.su27CanopyTarget>.5 ? 0.0:1.0;break;
 case 5:p.su27Parking=!p.su27Parking;if(!p.su27Parking){p.SetBrake(YSFALSE);p.su27ParkingRelease=true;}break;
 }
 const wchar_t *name[]={L"АКБ",L"Топливные насосы",L"Левый двигатель",L"Правый двигатель",L"Фонарь",L"Стояночный тормоз"};
 sim->AddTimedMessage(name[YsBound(id,0,5)]);
 if(auto show=FsGetAirshow(sim))show->RecordSu27(sim,*a);
 printf("SU27ACTION id=%d battery=%d pumps=%d left=%d right=%d canopy=%.2f parking=%d\n",id,int(p.su27Battery),int(p.su27Pumps),int(p.su27Left),int(p.su27Right),p.su27CanopyTarget,int(p.su27Parking));
}
void Su27Tick(FsAirplane &a,FsSimulation *sim,double dt)
{
 if(!DetailedAircraft(&a) || dt<=0 || a.isPlayingRecord==YSTRUE)return;
 auto &p=a.Prop();
 // Both aircraft start ready. Preserve native engine/fuel/throttle behaviour.
 if(!p.su27Managed){p.su27Managed=true;p.su27Battery=p.su27Pumps=p.su27Left=p.su27Right=true;p.su27Parking=false;p.su27SpoolLeft=p.su27SpoolRight=1.0;if(auto show=FsGetAirshow(sim))show->RecordSu27(sim,a);}
 p.su27ThrustFactor=1.0;
 if(p.GetVelocity()>(0==strcmp(p.GetIdentifier(),"SU-34_FULLBACK")?5.0:40.0) && p.su27CanopyTarget!=0){p.su27CanopyTarget=0;if(auto show=FsGetAirshow(sim))show->RecordSu27(sim,a);}
 const double amount=dt*.4;p.su27Canopy=p.su27Canopy<p.su27CanopyTarget?YsSmaller(p.su27CanopyTarget,p.su27Canopy+amount):YsGreater(p.su27CanopyTarget,p.su27Canopy-amount);

}
void Su27Look(FsAirplane &a,bool right,bool middle,int x,int y)
{
 auto &p=a.Prop();
 if(right && !su27Ui.dragging){su27Ui.restoreX=x;su27Ui.restoreY=y;}
 if(right && su27Ui.dragging){p.su27LookH+=(x-su27Ui.lastX)*YsDegToRad(.28);p.su27LookP=YsBound(p.su27LookP+(y-su27Ui.lastY)*YsDegToRad(.28),-YsPi*.47,YsPi*.47);}
 if(!right && su27Ui.dragging){FsSetMousePosition(su27Ui.restoreX,su27Ui.restoreY);x=su27Ui.restoreX;y=su27Ui.restoreY;}
 if(middle){p.su27LookH=0;p.su27LookP=.16;}
 su27Ui.dragging=right;su27Ui.lastX=x;su27Ui.lastY=y;
}
// Shared free look for every aircraft, independent of the optional Su27 panel.
struct CockpitLookInput {const FsAirplane *air=nullptr;bool dragging=false,spaceDown=false;int x=0,y=0,restoreX=0,restoreY=0;unsigned long long spaceTime=0;} cockpitLook;
void CockpitFreeLook(FsSimulation *sim,bool down,int x,int y){
 auto a=sim->GetPlayerAirplane();if(!a)return;auto &p=a->Prop();
 if(cockpitLook.air!=a){cockpitLook=CockpitLookInput();cockpitLook.air=a;p.su27LookH=p.su27LookP=0;
#ifdef V861_VALIDATION
 const auto eye=p.GetCockpitPosition();printf("COCKPITLOOK eye=%.4f,%.4f,%.4f mesh=%d\n",eye.x(),eye.y(),eye.z(),int(a->cockpit!=nullptr));fflush(stdout);
#endif
}
 if(down && !cockpitLook.dragging){cockpitLook.restoreX=x;cockpitLook.restoreY=y;}
 if(down && cockpitLook.dragging){p.su27LookH=YsBound(p.su27LookH-YsDegToRad(.25)*(x-cockpitLook.x),-YsPi*.94,YsPi*.94);p.su27LookP=YsBound(p.su27LookP+YsDegToRad(.25)*(y-cockpitLook.y),-YsPi*.46,YsPi*.46);}
 if(!down && cockpitLook.dragging){printf("COCKPITLOOK drag h=%.5f p=%.5f\n",p.su27LookH,p.su27LookP);fflush(stdout);FsSetMousePosition(cockpitLook.restoreX,cockpitLook.restoreY);x=cockpitLook.restoreX;y=cockpitLook.restoreY;}
 cockpitLook.dragging=down;cockpitLook.x=x;cockpitLook.y=y;
 const bool space=(FsGetKeyState(FSKEY_SPACE)==YSTRUE);
 if(space && !cockpitLook.spaceDown){
  const auto now=FsSubSecondTimer();
  if(cockpitLook.spaceTime!=0 && now-cockpitLook.spaceTime<=400){p.su27LookH=p.su27LookP=0;cockpitLook.spaceTime=0;printf("COCKPITLOOK reset=1\n");fflush(stdout);}
  else cockpitLook.spaceTime=now;
 }
 cockpitLook.spaceDown=space;
}
void Su27Mouse(FsSimulation *sim,bool lb,int mx,int my)
{
 auto a=sim->GetPlayerAirplane();bool down=lb && FsGetKeyState(FSKEY_ALT)==YSTRUE;
 if(!Su27Cockpit(a)){su27Ui.click=down;return;}
 if(down && !su27Ui.click && a==su27Ui.air && fabs(sim->GetClock()-su27Ui.clock)<.5){
  for(int i=0;i<6;++i)if((su27Ui.center[i]-YsVec2(mx,my)).GetLength()<su27Ui.radius[i]){Su27Action(sim,i);break;}
 }
 su27Ui.click=down;
}
void Su27Draw(const FsAirplane &a,const FsSimulation *sim,const YsMatrix4x4 &view,const FsProjection &proj)
{
 if(!Su27Cockpit(&a))return;const auto &p=a.Prop();
 YsMatrix4x4 model;model.Translate(a.GetPosition());model.Rotate(a.GetAttitude());auto transform=proj.GetMatrix()*view*model;
 int viewport[]={0,0,proj.viewportDim.x(),proj.viewportDim.y()};int ww,hh;FsGetWindowSize(ww,hh);
 const bool main=ww==viewport[2] && hh==viewport[3];
 if(main){su27Ui.air=&a;su27Ui.clock=sim->GetClock();}

 if(p.su27Battery){YsVec3 a1,a2;auto hudLine=[&](YsVec3 x,YsVec3 y){a.GetAttitude().Mul(a1,x);a.GetAttitude().Mul(a2,y);YsColor c;c.SetIntRGB(80,230,112);FsDrawLine3d(a1,a2,c);};hudLine(YsVec3(-.10,1.79,6.21),YsVec3(.10,1.79,6.21));hudLine(YsVec3(0,1.74,6.21),YsVec3(0,1.84,6.21));}

 if(p.su27Battery){
  auto line=[&](YsVec3 x,YsVec3 y,YsColor color){YsVec3 xx,yy;a.GetAttitude().Mul(xx,x);a.GetAttitude().Mul(yy,y);FsDrawLine3d(xx,yy,color);};
  YsColor green;green.SetIntRGB(90,218,124);
  for(int e=0;e<2;++e){double x=e==0?-.24:.04;double level=e==0?p.su27SpoolLeft:p.su27SpoolRight;double angle=YsDegToRad(-130+260*level);line(YsVec3(x,.76,5.972),YsVec3(x+.057*sin(angle),.76+.057*cos(angle),5.972),YsWhite());}
  for(int k=0;k<32;++k){double x=.40+.090*cos(k*YsPi/16),y=.76+.090*sin(k*YsPi/16);double xx=.40+.090*cos((k+1)*YsPi/16),yy=.76+.090*sin((k+1)*YsPi/16);line(YsVec3(x,y,5.972),YsVec3(xx,yy,5.972),green);}
  line(YsVec3(.31,.76,5.972),YsVec3(.49,.76,5.972),green);line(YsVec3(.40,.67,5.972),YsVec3(.40,.85,5.972),green);
  for(auto other=sim->FindNextAirplane(nullptr);other;other=sim->FindNextAirplane(other))if(other!=&a && other->iff==a.iff && other->Prop().IsActive()==YSTRUE){
   auto rel=other->GetPosition()-a.GetPosition();YsAtt3 yaw=a.GetAttitude();yaw.SetP(0);yaw.SetB(0);yaw.MulInverse(rel,rel);
   if(rel.x()*rel.x()+rel.z()*rel.z()<1000000){double x=.40+rel.x()*.00009,y=.76+rel.z()*.00009;line(YsVec3(x-.003,y,5.97),YsVec3(x+.003,y,5.97),green);line(YsVec3(x,y-.003,5.97),YsVec3(x,y+.003,5.97),green);}
  }
 }
 bool state[]={p.su27Battery,p.su27Pumps,p.su27Left,p.su27Right,p.su27CanopyTarget>.5,p.su27Parking};
 for(int i=0;i<6;++i){
  auto c=Su27Button(i);YsVec3 camera;view.Mul(camera,model*c,1.0);
  if(main){if(camera.z()>.05){su27Ui.center[i].Set(proj.cx+camera.x()*proj.prjPlnDist/camera.z(),proj.cy-camera.y()*proj.prjPlnDist/camera.z());su27Ui.radius[i]=YsBound(.055*proj.prjPlnDist/camera.z(),10.0,65.0);}else su27Ui.radius[i]=0;}
  auto line=[&](YsVec3 x,YsVec3 y,YsColor color){YsVec3 xx,yy;a.GetAttitude().Mul(xx,x);a.GetAttitude().Mul(yy,y);FsDrawLine3d(xx,yy,color);};
  YsColor color;double ready=i==2?p.su27SpoolLeft:(i==3?p.su27SpoolRight:1.0);
  color.SetIntRGB(state[i]? (ready>.95?66:235):90,state[i]?(ready>.95?223:171):53,state[i]?88:48);
  for(int k=-2;k<=2;++k)line(c+YsVec3(.043-.008,k*.002,0),c+YsVec3(.043+.008,k*.002,0),color);
  line(c+YsVec3(-.02,-.012,0),c+YsVec3(-.02,state[i]?.012:-.025,-.035),YsWhite());
 }
}
}
#endif
