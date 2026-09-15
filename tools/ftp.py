#!/usr/bin/env python3
"""FTP mínimo para o pós-exploit. Ideia vinda de mansoor0x/m0ftp_ps, sem GUI.

Só stdlib (ftplib). Payloads FTP de PS4 costumam escutar em 1337.
Útil pós-jailbreak: conferir /data/hen, criar as pastas anti-update em
/update, subir payloads.
  python tools/ftp.py 192.168.1.50 ls /data
  python tools/ftp.py 192.168.1.50 put payload.bin /data/payload.bin
  python tools/ftp.py 192.168.1.50 get /data/log.txt log.txt
  python tools/ftp.py 192.168.1.50 mkdir /update/PS4UPDATE.PUP
"""
import ftplib
import sys
from pathlib import Path

PORT = 1337

def usage():
    print(__doc__.strip())
    return 2

def main(argv):
    if len(argv) < 3:
        return usage()
    ip, cmd = argv[1], argv[2].lower()
    ftp = ftplib.FTP()
    try:
        ftp.connect(ip, PORT, timeout=10)
        ftp.login()
    except OSError as e:
        print("conexão falhou: %s (FTP ativo no console?)" % e)
        return 1
    try:
        if cmd == "ls":
            path = argv[3] if len(argv) > 3 else "/"
            for name in ftp.nlst(path):
                print(name)
        elif cmd == "put":
            if len(argv) < 4:
                return usage()
            local = Path(argv[3])
            remote = argv[4] if len(argv) > 4 else "/" + local.name
            with local.open("rb") as fh:
                ftp.storbinary("STOR " + remote, fh)
            print("ok: %s -> %s" % (local, remote))
        elif cmd == "get":
            if len(argv) < 4:
                return usage()
            remote = argv[3]
            local = Path(argv[4]) if len(argv) > 4 else Path(remote).name
            with local.open("wb") as fh:
                ftp.retrbinary("RETR " + remote, fh.write)
            print("ok: %s -> %s" % (remote, local))
        elif cmd == "mkdir":
            if len(argv) < 4:
                return usage()
            ftp.mkd(argv[3])
            print("ok: pasta %s" % argv[3])
        else:
            return usage()
    except (ftplib.error_perm, OSError) as e:
        print("erro: %s" % e)
        return 1
    finally:
        try:
            ftp.quit()
        except OSError:
            pass
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
