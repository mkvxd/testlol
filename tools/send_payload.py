#!/usr/bin/env python3
"""Envia payload.bin ao PS4 e confere se subiu.

Adaptado de saudid0s/WebRTE send.py para este host (multi-firmware):
  python tools/send_payload.py 192.168.1.50
  python tools/send_payload.py 192.168.1.50 --payload payload.bin --no-wait

Só stdlib. O receiver do GoldHEN escuta em 9090; o payload abre a 771.
"""
import argparse
import socket
import sys
import time
from pathlib import Path

PAYLOAD_PORT = 9090
CHECK_PORT = 771
DEFAULT_PAYLOAD = Path(__file__).resolve().parent.parent / "payload.bin"

def send(ip, path):
    data = Path(path).read_bytes()
    print("payload : %s (%d bytes)" % (path, len(data)))
    print("enviando: %s:%d" % (ip, PAYLOAD_PORT))
    s = socket.create_connection((ip, PAYLOAD_PORT), timeout=10)
    try:
        s.sendall(data)
    finally:
        s.close()
    print("enviado, olhe o klog\n")

def wait(ip, seconds=40):
    print("aguardando porta %d (até %ds)..." % (CHECK_PORT, seconds))
    t0 = time.time()
    while time.time() - t0 < seconds:
        try:
            socket.create_connection((ip, CHECK_PORT), timeout=2).close()
            print("porta %d aberta após %.1fs" % (CHECK_PORT, time.time() - t0))
            return True
        except OSError:
            time.sleep(1)
    return False

def check(ip):
    s = socket.create_connection((ip, CHECK_PORT), timeout=10)
    try:
        s.sendall(b"GET /list HTTP/1.1\r\nHost: h\r\nConnection: close\r\n\r\n")
        buf = b""
        s.settimeout(10)
        try:
            while True:
                d = s.recv(8192)
                if not d:
                    break
                buf += d
        except socket.timeout:
            pass
    finally:
        s.close()
    return buf.partition(b"\r\n\r\n")[2].count(b'"pid"')

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ip", help="IP do console (Ajustes > Rede)")
    ap.add_argument("--payload", default=str(DEFAULT_PAYLOAD))
    ap.add_argument("--no-wait", action="store_true", help="envia e sai")
    a = ap.parse_args()
    try:
        send(a.ip, a.payload)
    except FileNotFoundError:
        print("arquivo não existe: %s" % a.payload)
        return 2
    except OSError as e:
        print("falha no envio: %s" % e)
        print("  Console ligado, jailbreak ativo e receiver em %d?" % PAYLOAD_PORT)
        return 2
    if a.no_wait:
        return 0
    time.sleep(3)
    if not wait(a.ip):
        print("\nSem resposta. Última linha do klog diz a etapa que falhou:")
        print("  'patching kernel'   -> patches do kernel")
        print("  'loading kdebugger' -> símbolos do kernel deste firmware")
        print("  'loading webrte'    -> offsets de thread do libkernel")
        print("  crash + reboot      -> offsets de thread errados")
        return 1
    try:
        n = check(a.ip)
    except OSError as e:
        print("porta abriu mas /list falhou: %s" % e)
        return 1
    print("/list retornou %d processos" % n)
    return 0

if __name__ == "__main__":
    sys.exit(main())
