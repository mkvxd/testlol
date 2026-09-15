#!/usr/bin/env python3
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
fails = []
warns = []

def fail(msg):
    fails.append(msg)
    print("FALHA: " + msg)

def warn(msg):
    warns.append(msg)
    print("AVISO: " + msg)

def keys_of(body):
    return set(re.findall(r"(?<![\w$])([A-Za-z_][\w$]*)\s*:", body))

def brace_span(text, open_idx):
    depth = 0
    i = open_idx
    while True:
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return open_idx, i
        i += 1

src = (ROOT / "ps4_offsets.mjs").read_text(encoding="utf-8")
m = re.search(r"REQUIRED_KEYS\s*=\s*\[(.*?)\]", src, re.S)
if not m:
    fail("REQUIRED_KEYS nao encontrado em ps4_offsets.mjs")
    required = []
else:
    required = re.findall(r'"([^"]+)"', m.group(1))
m = re.search(r"OPTIONAL_KEYS\s*=\s*\[(.*?)\]", src, re.S)
optional = set(re.findall(r'"([^"]+)"', m.group(1))) if m else set()

bodies = {}
for em in re.finditer(r'"(\d+\.\d+)"\s*:\s*\{', src):
    o, c = brace_span(src, em.end() - 1)
    bodies[em.group(1)] = src[o + 1:c]

sm = re.search(r"function _stub\(ver, note\) \{\n    return \{", src)
template = ""
if sm:
    o, c = brace_span(src, src.index("{", sm.start()))
    template = src[o + 1:c]

direct_re = re.compile(r'PS4\["(\d+\.\d+)"\]\s*=\s*\{', re.S)
for em in direct_re.finditer(src):
    key = em.group(1)
    if key in bodies:
        continue
    o, c = brace_span(src, em.end() - 1)
    bodies[key] = src[o + 1:c]

assign_re = re.compile(
    r'PS4\["(\d+\.\d+)"\]\s*=\s*(?:Object\.assign\(\{\},\s*PS4\["([\d.]+)"\]|(_stub)\()',
    re.S)
for em in assign_re.finditer(src):
    key = em.group(1)
    if key in bodies:
        continue
    if em.group(3):
        bodies[key] = template
    else:
        o, c = brace_span(src, src.index("{", em.end()))
        bodies[key] = src[o + 1:c]
        bodies[key + "\x00base"] = em.group(2)

entries = {}
eff = {}
def resolve(key, stack=()):
    if key in eff:
        return eff[key]
    if key in stack or key not in bodies or key.endswith("\x00base"):
        return set()
    keys = keys_of(bodies[key])
    bk = bodies.get(key + "\x00base")
    if bk:
        keys |= resolve(bk, stack + (key,))
    eff[key] = keys
    return keys

for key, body in bodies.items():
    if key.endswith("\x00base"):
        continue
    entries[key] = (resolve(key), body)

if not entries:
    fail("nenhum bloco de firmware encontrado em ps4_offsets.mjs")

used = set()
for chain in ("chain_poops.mjs", "chain_lapse.mjs"):
    text = (ROOT / chain).read_text(encoding="utf-8")
    used |= set(re.findall(r"(?:off|KOFF)\.(\w+)", text))
used -= {"kpatch"}
print("firmwares: %d  chaves obrigatorias: %d  chaves usadas pelos chains: %d"
      % (len(entries), len(required), len(used)))

for key in sorted(entries):
    keys, body = entries[key]
    for rk in required:
        if rk not in keys:
            fail("chave obrigatoria ausente em %s: %s" % (key, rk))
    for uk in sorted(used):
        if uk not in keys and uk not in optional:
            fail("chain usa chave ausente em %s: %s" % (key, uk))
        elif uk not in keys:
            warn("opcional ausente em %s: %s" % (key, uk))
    mk = re.search(r'kpatch:\s*"([^"]+)"', body)
    if mk and not (ROOT / "patches" / mk.group(1)).is_file():
        fail("kpatch em falta em %s: patches/%s" % (key, mk.group(1)))

payload = ROOT / "payload.bin"
if not payload.is_file() or payload.stat().st_size == 0:
    fail("payload.bin ausente ou vazio")

sw = (ROOT / "sw.js").read_text(encoding="utf-8")
cached = re.findall(r'"(\./[^"]+)"', sw)
for entry in cached:
    if not (ROOT / entry[2:]).is_file():
        fail("sw.js referencia arquivo inexistente: " + entry)
need = {"./index.html", "./poops.html", "./lapse.html",
        "./chain_poops.mjs", "./chain_lapse.mjs", "./ps4_offsets.mjs",
        "./rpc_worker.mjs", "./payload.bin"}
for entry in sorted(need - set(cached)):
    fail("sw.js nao inclui: " + entry)
for blob in sorted((ROOT / "patches").glob("*.bin")):
    if ("./patches/" + blob.name) not in cached:
        fail("sw.js nao inclui: ./patches/" + blob.name)

print("%d firmware(s), %d em cache, %d falha(s), %d aviso(s)"
      % (len(entries), len(cached), len(fails), len(warns)))
sys.exit(1 if fails else 0)
