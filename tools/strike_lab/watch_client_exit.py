"""Read-only short-lived process and TCP lifetime trace for local playtests."""

import ipaddress
import json
import sys
import time

import psutil


def emit(**event):
    print(json.dumps(dict(at=time.time(), **event), separators=(",", ":")), flush=True)


def main(pid: int, seconds: int) -> None:
    process = psutil.Process(pid)
    deadline = time.monotonic() + seconds
    last = None
    emit(event="attached", pid=pid)
    while time.monotonic() < deadline:
        if not process.is_running() or process.status() == psutil.STATUS_ZOMBIE:
            emit(event="exit", code=process.wait(timeout=0))
            return
        try:
            connections = tuple(sorted((connection.raddr.port,
                                        ipaddress.ip_address(connection.raddr.ip).is_loopback,
                                        connection.status)
                                       for connection in process.net_connections(kind="tcp")
                                       if connection.raddr))
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            connections = ()
        if connections != last:
            emit(event="connections", entries=connections)
            last = connections
        time.sleep(0.1)
    emit(event="deadline", alive=process.is_running())


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
