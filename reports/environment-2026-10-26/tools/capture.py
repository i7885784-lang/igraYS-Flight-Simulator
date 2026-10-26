"""Capture real YSFlight rendering. Run after sourcing env.sh and start.sh."""
from pathlib import Path
import os, subprocess, time, re, json, ctypes
from PIL import ImageGrab

d=Path('/workspace/ysflight-dev')
runtime=d/'YSFlight_Su57_Test_2_Engine_Source/build64/main'
out=d/'evidence';out.mkdir(exist_ok=True)
profile=d/'capture-user';(profile/'config').mkdir(parents=True,exist_ok=True)
(profile/'config/option.cfg').write_text('OPENDEMO FALSE\nFONTHEIGHT 18\nLANGUAGE "FILE:ru.uitxt"\n')
(profile/'config/flight.cfg').write_text('DRWSHADOW FALSE\n')
fixture='''YFSVERSI 20180930
FIELDNAM STRAIGHT_TEST 0 0 0 0 0 0 FALSE LOADAIR:FALSE
INITPLYR AIR 1
CANCONTI TRUE
ENVIRONM DAY
EXTENSIO AIRSHOW_V8 CONFIG 0 0 0 16 0.2 0.35
AIRPLANE SU-57_FELON TRUE
IDENTIFY 0
IDANDTAG 1 "ENVIRONMENT_CHECK"
AIRPCMND UNLOADWP
AIRPCMND INITFUEL 50%
AIRPCMND ATTITUDE 0deg 0deg 0deg
AIRPCMND POSITION 0m 1000m 0m
AIRPCMND INITSPED 180m/s
AIRPCMND CTLLDGEA FALSE
AIRPCMND CTLTHROT 0.55
AIRPCMND CTLABRNR FALSE
'''
(out/'pose.yfs').write_text(fixture)
views=[('quarter',140,25,108),('front',180,0,105),('top',180,89,165),('side',90,0,125)]
script='WAITFOR:GUI\nSLEEP:500\n'+'GUI:CLOSEMODAL\n'*4+'SLEEP:18000\nFILE:OPEN Z:'+str(out/'pose.yfs')+'\nGUI:CLICK mainDlg flyNow\nWAITFOR:FLYING\nFLIGHTCMD:TESTADVANCE .1\nBTNFUNC:PAUSESIMULATION\n'
for i,(name,h,p,dist) in enumerate(views):
    script+=f'BTNFUNC:COCKPITVIEW\nFLIGHTCMD:LABVIEW {h} {p} {dist} 0\n'
    if i==0:script+='BTNFUNC:VIEWZOOM\n'*26
    script+=f'FLIGHTCMD:MODELCHECK\nSLEEP:{4000+i}\n'
script+='FLIGHTCMD:LABVIEW 40 -14 100 0\nBTNFUNC:PAUSESIMULATION\nBTNFUNC:LANDINGGEAR\nSLEEP:9999\nFLIGHTCMD:MODELCHECK\nSLEEP:60000\n'
(out/'capture.script').write_text(script)
log=out/'capture.log'
def wait(needle,timeout=120):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        s=log.read_text(errors='replace')
        if needle in s:return s
        if game.poll() is not None:raise RuntimeError(f'Game exited {game.returncode}: '+s[-2500:])
        time.sleep(.2)
    raise RuntimeError('Timeout '+needle+'\n'+log.read_text(errors='replace')[-1500:])

with log.open('w') as f:
    game=subprocess.Popen([os.environ['WINELOADER'],str(runtime/'ysflight64_gl1.exe'),'-userdir','Z:'+str(profile),'-configdir','Z:'+str(profile/'config'),'-script','Z:'+str(out/'capture.script')],cwd=runtime,stdout=f,stderr=f)
try:
    wait('Script>>SLEEP:18000')
    tree=subprocess.check_output(['xwininfo','-root','-tree'],text=True)
    matches=re.findall(r'(0x[0-9a-f]+) "([^"]+)"',tree)
    window=next(int(w,16) for w,title in matches if 'YS' in title.upper() and 'FLIGHT' in title.upper())
    x=ctypes.CDLL('libX11.so.6');x.XOpenDisplay.restype=ctypes.c_void_p
    display=x.XOpenDisplay(b':99')
    x.XMoveResizeWindow.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_int,ctypes.c_int,ctypes.c_uint,ctypes.c_uint]
    x.XMoveResizeWindow(display,window,0,0,1280,960)
    x.XFlush.argtypes=[ctypes.c_void_p];x.XFlush(display)
    for i,(name,*_) in enumerate(views):
        wait(f'Script>>SLEEP:{4000+i}');time.sleep(.4)
        ImageGrab.grab(xdisplay=':99').save(out/(name+'.png'))
        print('Captured',name,flush=True)
    wait('Script>>SLEEP:9999')
    # Pillow reads X11 without FFmpeg MIT-SHM assumptions across sandbox namespaces.
    encoder=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1280x960','-framerate','15','-i','-','-an','-c:v','libx264','-pix_fmt','yuv420p',str(out/'live-flight.mp4')],stdin=subprocess.PIPE)
    began=time.monotonic()
    for frame in range(90):
        encoder.stdin.write(ImageGrab.grab(xdisplay=':99').convert('RGB').tobytes())
        time.sleep(max(0,began+(frame+1)/15-time.monotonic()))
    encoder.stdin.close();assert encoder.wait(timeout=20)==0
    wait('Script>>SLEEP:60000')
    text=log.read_text(errors='replace')
    states=[dict(re.findall(r'(\w+)=(-?[0-9.]+)',line)) for line in text.splitlines() if line.startswith('MODELCHECK ')]
    assert len(states)==5 and all(s['active']=='1' for s in states)
    assert float(states[-1]['t'])>float(states[0]['t'])+5
    assert float(states[-1]['gear'])>.9
    (out/'capture-checks.json').write_text(json.dumps({'passed':True,'frames':[v[0] for v in views],'states':states,'video':'live-flight.mp4','renderer':'Win64 validation build, Wine 10, Xvfb; actual game rendering'},indent=2))
finally:
    game.terminate()
    try:game.wait(timeout=10)
    except subprocess.TimeoutExpired:game.kill();game.wait()
