"""Read-only, PID-scoped window capture for the next network-trigger blocker."""
import ctypes as c
from ctypes import wintypes as w
import json
import time


def capture(pid,run):
    from PIL import Image
    user=c.WinDLL('user32',use_last_error=True)
    gdi=c.WinDLL('gdi32',use_last_error=True)
    def api(lib,name,restype,*args):
        fn=getattr(lib,name);fn.restype=restype;fn.argtypes=list(args);return fn
    callback=c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
    enum=api(user,'EnumWindows',w.BOOL,callback,w.LPARAM)
    getpid=api(user,'GetWindowThreadProcessId',w.DWORD,w.HWND,c.POINTER(w.DWORD))
    visible=api(user,'IsWindowVisible',w.BOOL,w.HWND)
    title=api(user,'GetWindowTextW',c.c_int,w.HWND,w.LPWSTR,c.c_int)
    rect=api(user,'GetWindowRect',w.BOOL,w.HWND,c.POINTER(w.RECT))
    getdc=api(user,'GetWindowDC',w.HDC,w.HWND)
    releasedc=api(user,'ReleaseDC',c.c_int,w.HWND,w.HDC)
    createdc=api(gdi,'CreateCompatibleDC',w.HDC,w.HDC)
    bitmap=api(gdi,'CreateCompatibleBitmap',w.HBITMAP,w.HDC,c.c_int,c.c_int)
    select=api(gdi,'SelectObject',w.HANDLE,w.HDC,w.HANDLE)
    blt=api(gdi,'BitBlt',w.BOOL,w.HDC,c.c_int,c.c_int,c.c_int,c.c_int,w.HDC,c.c_int,c.c_int,w.DWORD)
    bits=api(gdi,'GetDIBits',c.c_int,w.HDC,w.HBITMAP,w.UINT,w.UINT,c.c_void_p,c.c_void_p,w.UINT)
    delete=api(gdi,'DeleteObject',w.BOOL,w.HANDLE)
    deletedc=api(gdi,'DeleteDC',w.BOOL,w.HDC)
    rows=[]
    @callback
    def visit(hwnd,param):
        owner=w.DWORD();tid=getpid(hwnd,c.byref(owner))
        if owner.value!=pid or not visible(hwnd):return True
        name=c.create_unicode_buffer(1024);title(hwnd,name,1024)
        r=w.RECT()
        if not rect(hwnd,c.byref(r)):return True
        row={'pid':pid,'tid':tid,'hwnd':hwnd,'title':name.value,'timestamp':time.time(),
             'rect':[r.left,r.top,r.right,r.bottom]}
        rows.append(row)
        width=r.right-r.left;height=r.bottom-r.top
        if not(0<width<=4096 and 0<height<=4096):return True
        dc=getdc(hwnd);memory=createdc(dc);bmp=bitmap(dc,width,height);old=select(memory,bmp)
        try:
            if not blt(memory,0,0,width,height,dc,0,0,0x00cc0020):raise c.WinError(c.get_last_error())
            select(memory,old)
            import struct
            header=c.create_string_buffer(struct.pack('<IiiHHIIiiII',40,width,-height,1,32,0,0,0,0,0,0))
            pixels=c.create_string_buffer(width*height*4)
            if bits(memory,bmp,0,height,pixels,header,0)!=height:raise RuntimeError('Incomplete window bitmap')
            path=run/f'window-{time.time_ns()}-{len(rows):02}.png'
            Image.frombytes('RGB',(width,height),pixels.raw,'raw','BGRX').save(path)
            row['image']=path.name
        except Exception as error:row['error']=repr(error)
        finally:select(memory,old);delete(bmp);deletedc(memory);releasedc(hwnd,dc)
        return True
    enum(visit,0)
    (run/'windows.json').write_text(json.dumps(rows,ensure_ascii=True,indent=2),encoding='utf-8')
    return rows


def enter_game(pid,run,reference):
    """One physical mouse click, only on the visually verified main menu."""
    from PIL import Image,ImageChops,ImageStat
    rows=capture(pid,run)
    matches=[r for r in rows if r.get('image') and r['title']=='XianJieZhuan / Build - Jan 11 2017 Ver 2.40.83']
    result={'event_type':'ENTER_GAME_ACTION','pid':pid,'timestamp':time.time(),'sent':False}
    if len(matches)!=1:
        result['reason']='WINDOW_NOT_UNIQUE';return result
    target=matches[0]
    with Image.open(run/target['image']) as actual,Image.open(reference) as expected:
        if actual.size!=expected.size or actual.size!=(816,639):
            result['reason']='WINDOW_DIMENSIONS_CHANGED';return result
        # Fixed button region observed in network-strike-03, not a guessed UI target.
        delta=ImageChops.difference(actual.convert('RGB').crop((434,474,606,516)),
                                  expected.convert('RGB').crop((434,474,606,516)))
        result['button_mean_difference']=sum(ImageStat.Stat(delta).mean)/3
        hover=reference.parents[1]/'network-strike-login-01/window-1789765088414591400-01.png'
        if hover.exists():
            with Image.open(hover) as hovered:
                delta=ImageChops.difference(actual.convert('RGB').crop((434,474,606,516)),hovered.convert('RGB').crop((434,474,606,516)))
                result['button_mean_difference']=min(result['button_mean_difference'],sum(ImageStat.Stat(delta).mean)/3)
        if result['button_mean_difference']>3:
            result['reason']='BUTTON_VISUAL_MISMATCH';return result
    user=c.WinDLL('user32',use_last_error=True)
    user.GetWindowThreadProcessId.argtypes=[w.HWND,c.POINTER(w.DWORD)]
    user.GetClientRect.argtypes=[w.HWND,c.POINTER(w.RECT)]
    user.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
    user.PostMessageW.restype=w.BOOL
    hwnd=target['hwnd'];owner=w.DWORD();user.GetWindowThreadProcessId(hwnd,c.byref(owner))
    rect=w.RECT()
    if owner.value!=pid or not user.GetClientRect(hwnd,c.byref(rect)) or (rect.right,rect.bottom)!=(800,600):
        result['reason']='TARGET_CHANGED';return result
    user.SetForegroundWindow.argtypes=[w.HWND]
    user.GetForegroundWindow.restype=w.HWND
    user.ClientToScreen.argtypes=[w.HWND,c.POINTER(w.POINT)]
    user.WindowFromPoint.argtypes=[w.POINT];user.WindowFromPoint.restype=w.HWND
    user.SetForegroundWindow(hwnd)
    if user.GetForegroundWindow()!=hwnd:
        result['reason']='FOREGROUND_REFUSED';return result
    position=w.POINT(512,464)
    if not user.ClientToScreen(hwnd,c.byref(position)) or user.WindowFromPoint(position)!=hwnd:
        result['reason']='TARGET_OCCLUDED';return result
    if not user.SetCursorPos(position.x,position.y):
        result['reason']='CURSOR_MOVE_FAILED';return result
    class Mouse(c.Structure):
        _fields_=[('dx',w.LONG),('dy',w.LONG),('data',w.DWORD),('flags',w.DWORD),('time',w.DWORD),('extra',c.c_size_t)]
    class Payload(c.Union):
        _fields_=[('mouse',Mouse)]
    class Input(c.Structure):
        _fields_=[('type',w.DWORD),('payload',Payload)]
    user.SendInput.argtypes=[w.UINT,c.POINTER(Input),c.c_int];user.SendInput.restype=w.UINT
    down=Input(0,Payload(mouse=Mouse(0,0,0,2,0,0)))
    up=Input(0,Payload(mouse=Mouse(0,0,0,4,0,0)))
    sent=user.SendInput(1,c.byref(down),c.sizeof(Input))
    try:time.sleep(.10)
    finally:released=user.SendInput(1,c.byref(up),c.sizeof(Input))
    result.update(sent=sent==1 and released==1,hwnd=hwnd,client_point=[512,464],method='SendInput',
                  down_count=sent,up_count=released,win32_error=0 if sent and released else c.get_last_error())
    return result


def submit_test_login(pid,run,reference,lab_case=None):
    """One synthetic lab login; never read or log a real user's credentials."""
    from PIL import Image,ImageChops,ImageStat
    import secrets
    if lab_case not in (None,'A','B'):raise ValueError('Unknown controlled input case')
    rows=capture(pid,run)
    candidates=[r for r in rows if r.get('image') and r['title']=='XianJieZhuan / Build - Jan 11 2017 Ver 2.40.83']
    result={'event_type':'TEST_LOGIN_ACTION','pid':pid,'timestamp':time.time(),'sent':False,'account':'codexlab'}
    if len(candidates)!=1:result['reason']='WINDOW_NOT_UNIQUE';return result
    target=candidates[0]
    with Image.open(run/target['image']) as actual,Image.open(reference) as expected:
        if actual.size!=expected.size or actual.size!=(816,639):
            result['reason']='WINDOW_DIMENSIONS_CHANGED';return result
        delta=ImageChops.difference(actual.convert('RGB').crop((270,200,545,374)),expected.convert('RGB').crop((270,200,545,374)))
        result['panel_mean_difference']=sum(ImageStat.Stat(delta).mean)/3
        if result['panel_mean_difference']>3:result['reason']='LOGIN_PANEL_MISMATCH';return result
    user=c.WinDLL('user32',use_last_error=True);hwnd=target['hwnd']
    user.SetForegroundWindow.argtypes=[w.HWND];user.GetForegroundWindow.restype=w.HWND
    user.GetWindowThreadProcessId.argtypes=[w.HWND,c.POINTER(w.DWORD)]
    user.ClientToScreen.argtypes=[w.HWND,c.POINTER(w.POINT)]
    user.WindowFromPoint.argtypes=[w.POINT];user.WindowFromPoint.restype=w.HWND
    class Mouse(c.Structure):
        _fields_=[('dx',w.LONG),('dy',w.LONG),('data',w.DWORD),('flags',w.DWORD),('time',w.DWORD),('extra',c.c_size_t)]
    class Keyboard(c.Structure):
        _fields_=[('vk',w.WORD),('scan',w.WORD),('flags',w.DWORD),('time',w.DWORD),('extra',c.c_size_t)]
    class Payload(c.Union):
        _fields_=[('mouse',Mouse),('key',Keyboard)]
    class Input(c.Structure):
        _fields_=[('type',w.DWORD),('payload',Payload)]
    user.SendInput.argtypes=[w.UINT,c.POINTER(Input),c.c_int];user.SendInput.restype=w.UINT
    def send(event):
        if user.SendInput(1,c.byref(event),c.sizeof(Input))!=1:raise RuntimeError('Input rejected')
    def click(x,y):
        owner=w.DWORD();user.GetWindowThreadProcessId(hwnd,c.byref(owner))
        if owner.value!=pid or user.GetForegroundWindow()!=hwnd:raise RuntimeError('Target focus changed')
        p=w.POINT(x,y)
        if not user.ClientToScreen(hwnd,c.byref(p)) or user.WindowFromPoint(p)!=hwnd:raise RuntimeError('Target occluded')
        if not user.SetCursorPos(p.x,p.y):raise RuntimeError('Cursor move rejected')
        send(Input(0,Payload(mouse=Mouse(round(p.x*65535/(user.GetSystemMetrics(0)-1)),
            round(p.y*65535/(user.GetSystemMetrics(1)-1)),0,0x8001,0,0))))
        time.sleep(.15)
        send(Input(0,Payload(mouse=Mouse(0,0,0,2,0,0))))
        try:time.sleep(.1)
        finally:send(Input(0,Payload(mouse=Mouse(0,0,0,4,0,0))))
        time.sleep(.15)
    def type_ascii(value):
        for char in value:
            if user.GetForegroundWindow()!=hwnd:raise RuntimeError('Target focus changed')
            send(Input(1,Payload(key=Keyboard(0,ord(char),4,0,0))))
            send(Input(1,Payload(key=Keyboard(0,ord(char),6,0,0))))
    try:
        user.SetForegroundWindow(hwnd)
        click(437,232);type_ascii('codexmap' if lab_case=='B' else 'codexlab')
        click(437,263);type_ascii('labtest2345' if lab_case else ''.join(secrets.choice('abcdefghjkmnpqrstuvwxyz23456789') for _ in range(10)))
        click(452,304)
        result.update(sent=True,method='SendInput',synthetic_credentials=True)
        if lab_case:result.update(account='REDACTED',controlled_case=lab_case)
    except Exception as error:result['reason']=str(error)
    return result
