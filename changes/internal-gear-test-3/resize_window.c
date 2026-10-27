#include <windows.h>
#include <string.h>
#include <stdio.h>
BOOL CALLBACK find(HWND hwnd,LPARAM data){
 char title[512];GetWindowTextA(hwnd,title,sizeof(title));
 if(strstr(title,"YS FLIGHT")!=NULL){
  SetWindowLongPtrA(hwnd,GWL_STYLE,WS_POPUP|WS_VISIBLE);
  SetWindowPos(hwnd,HWND_TOP,0,0,1280,960,SWP_FRAMECHANGED|SWP_SHOWWINDOW);
  SetForegroundWindow(hwnd);RECT r;GetClientRect(hwnd,&r);
  SendMessage(hwnd,WM_SIZE,SIZE_RESTORED,MAKELPARAM(r.right,r.bottom));
  printf("CAPTURE_CLIENT %ld %ld\n",r.right,r.bottom);return FALSE;
 }
 return TRUE;
}
int main(void){EnumWindows(find,0);return 0;}
