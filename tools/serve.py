#!/usr/bin/env python3
"""Serve o host na rede local para abrir no navegador do PS4. Só stdlib.

  python tools/serve.py [porta]     (padrão 8000)

Por que existe: módulos ES (.mjs) exigem Content-Type: text/javascript.
Servidores genéricos no Windows servem .mjs como octet-stream e o chain
quebra no PS4. Este força o MIME certo + no-store no HTML.

No PS4 (com DNS 62.210.38.117, que bloqueia updates da Sony):
  1. Ajustes > Rede > Configurar conexão > Personalizada > Automático
  2. DNS manual: primário 62.210.38.117, secundário em branco
  3. MTU automático, Proxy não usar. Testar (falha na PSN = normal)
  4. Navegador > abrir a URL abaixo > exploit roda
"""
import functools
import http.server
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".mjs": "text/javascript",
        ".bin": "application/octet-stream",
    }

    def end_headers(self):
        path = getattr(self, "path", "") or ""
        if path.split("?")[0].endswith((".html", "/")):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *a):
        pass

def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        if ip and not ip.startswith("127."):
            return ip
    except OSError:
        pass
    finally:
        s.close()
    try:
        ip = socket.gethostbyname(socket.gethostname())
        if ip and not ip.startswith("127."):
            return ip
    except OSError:
        pass
    return "127.0.0.1"

def main():
    try:
        port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    except ValueError:
        print("porta inválida: %s" % sys.argv[1])
        return
    srv = http.server.ThreadingHTTPServer(
        ("0.0.0.0", port), functools.partial(Handler, directory=str(ROOT)))
    print("host no ar: http://%s:%d/" % (lan_ip(), port))
    print("no PS4: DNS 62.210.38.117 + abrir a URL acima no navegador")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
