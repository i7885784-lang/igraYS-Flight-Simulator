#include <windows.h>
#include <wchar.h>
#include <stdio.h>
static BOOL CALLBACK Resize(HWND w,LPARAM p){
 wchar_t title[512];GetWindowTextW(w,title,512);
 if(!IsWindowVisible(w) || !wcsstr(title,L"YS") || !wcsstr(title,L"FLIGHT"))return TRUE;
 ShowWindow(w,SW_RESTORE);LONG_PTR style=GetWindowLongPtrW(w,GWL_STYLE);SetWindowLongPtrW(w,GWL_STYLE,style&~(WS_CAPTION|WS_THICKFRAME));
 SetWindowPos(w,HWND_TOP,0,0,1024,768,SWP_FRAMECHANGED|SWP_SHOWWINDOW);SendMessageW(w,WM_SIZE,SIZE_RESTORED,MAKELPARAM(1024,768));SetForegroundWindow(w);
 RECT r;GetClientRect(w,&r);printf("capture client %ld x %ld\n",r.right,r.bottom);return FALSE;
}
int main(void){EnumWindows(Resize,0);return 0;}
