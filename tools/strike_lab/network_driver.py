"""Bounded network wait; interrupt only the already-verified debugger child."""
import ctypes
import queue
import re
import time
from trace_qualification.native import NativeDriver


class NetworkDriver(NativeDriver):
    client_pid=None
    interrupted=False

    def command(self,text):
        self.executing_target=text.strip() in ('g','gc')
        unbounded=self.deadline is None
        if unbounded and not self.executing_target:self.deadline=time.monotonic()+30
        try:return super().command(text)
        finally:
            if unbounded and not self.interrupted:self.deadline=None
            self.executing_target=False

    def stop(self):
        data=b''
        while True:
            tick=getattr(self,'gate_tick',None)
            if tick and getattr(self,'executing_target',False):tick()
            action=getattr(self,'idle_action',None)
            if action and time.monotonic()>=self.idle_action_at:
                self.idle_action=None
                action()
            remaining=1 if self.deadline is None else self.deadline-time.monotonic()
            if remaining<=0:
                if self.interrupted or not self.client_pid:
                    raise TimeoutError('Network capture deadline')
                if getattr(self,'capture_window',None):
                    self.capture_window(self.client_pid)
                kernel=ctypes.WinDLL('kernel32',use_last_error=True)
                kernel.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong]
                kernel.OpenProcess.restype=ctypes.c_void_p
                kernel.DebugBreakProcess.argtypes=[ctypes.c_void_p]
                kernel.DebugBreakProcess.restype=ctypes.c_int
                kernel.CloseHandle.argtypes=[ctypes.c_void_p]
                kernel.QueryFullProcessImageNameW.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_ulong)]
                handle=kernel.OpenProcess(0x1fffff,False,self.client_pid)
                if not handle:raise ctypes.WinError(ctypes.get_last_error())
                try:
                    from lab import CLIENT
                    image=ctypes.create_unicode_buffer(32768);length=ctypes.c_ulong(32768)
                    if not kernel.QueryFullProcessImageNameW(handle,0,image,ctypes.byref(length)):
                        raise ctypes.WinError(ctypes.get_last_error())
                    if image.value.casefold()!=str(CLIENT/'God2.exe').casefold():
                        raise RuntimeError('Timeout target identity changed')
                    if not kernel.DebugBreakProcess(handle):raise ctypes.WinError(ctypes.get_last_error())
                finally:kernel.CloseHandle(handle)
                self.interrupted=True
                self.deadline=time.monotonic()+10
                remaining=10
            try:item=self.q.get(timeout=min(remaining,1))
            except queue.Empty:continue
            if item is None:raise RuntimeError('Debugger exited before prompt')
            data+=item
            if re.search(rb'\d+:\d+(?::x86)?>\s*$',data):
                return data.decode('ascii',errors='replace')
