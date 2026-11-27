"""Etapa 2: monta o vídeo a partir de um projeto.json.

Uso: python3 make.py projeto.json [--skip-fx] [--no-render]
  --skip-fx    reaproveita fx.mp4 (use quando só mudou áudio, legenda ou destaque de texto)
  --no-render  só gera gráficos/legendas/timeline (para conferir tempos antes de renderizar)

Todo campo de tempo aceita:
  12.3                          -> segundos
  "desconto de"                 -> início da 1ª ocorrência da frase na transcrição
  {"at": "na sela", "n": 2, "edge": "end", "off": 0.2}
                                -> fim da 2ª ocorrência + 0,2 s
A busca ignora acentos, pontuação e maiúsculas, e roda DEPOIS das correções de "fixes".
Veja assets/exemplo-projeto.json (o anúncio Pet Prime Black Friday 2026) para todos os campos.
"""
import argparse, json, os, re, subprocess, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("project")
ap.add_argument("--skip-fx", action="store_true")
ap.add_argument("--no-render", action="store_true")
args = ap.parse_args()
P = json.load(open(args.project))
WORK = os.path.abspath(P["work"])
GFX = f"{WORK}/gfx"; SFXD = f"{WORK}/sfx"
os.makedirs(GFX, exist_ok=True)
DUR = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                            f"{WORK}/base.mov"], capture_output=True, text=True).stdout)


# ---------------- transcrição + correções ----------------
def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^\w$]", "", s)


TR = json.load(open(f"{WORK}/{P.get('transcript', 'transcript.json')}"))
words = [dict(w=w["word"].strip(), s=w["start"], e=w["end"]) for seg in TR["segments"] for w in seg["words"]]

# fixes: "errado" -> "certo"; a chave pode ter várias palavras ("a sinox": "em inox")
for wrong, right in sorted(P.get("fixes", {}).items(), key=lambda kv: -len(kv[0].split())):
    toks = [norm(t) for t in wrong.split()]
    i = 0
    while i <= len(words) - len(toks):
        if [norm(w["w"]) for w in words[i:i + len(toks)]] == toks:
            punct = re.findall(r"[.,!?]+$", words[i + len(toks) - 1]["w"])
            words[i] = dict(w=right + (punct[0] if punct else ""), s=words[i]["s"], e=words[i + len(toks) - 1]["e"])
            del words[i + 1:i + len(toks)]
        i += 1

# junta tokens de preço quebrados pelo Whisper ("R" "$1" ".899" ",00,")
merged = []
for w in words:
    if merged and re.match(r"^[\$\.,]\d|^\$", w["w"]) and re.search(r"[R\d$]$", merged[-1]["w"].rstrip(",.")):
        merged[-1]["w"] += w["w"]; merged[-1]["e"] = w["e"]
    else:
        merged.append(dict(w))
words = merged
for w in words:
    w["w"] = re.sub(r"R\$(\d)", r"R$ \1", w["w"]).replace(",00,", ",").replace(",00", "")
NW = [norm(w["w"]) for w in words]
def find(phrase, n=1):
    """Acha a n-ésima ocorrência da frase (comparando o texto concatenado sem espaços/acentos)."""
    goal = "".join(norm(t) for t in phrase.split())
    hits = 0
    for i in range(len(words)):
        buf, j = "", i
        while j < len(words) and len(buf) < len(goal):
            buf += NW[j]; j += 1
        if buf == goal:
            hits += 1
            if hits == n:
                return words[i], words[j - 1]
    ctx = " ".join(w["w"] for w in words)
    sys.exit(f'Frase não encontrada na transcrição: "{phrase}" (ocorrência {n}).\nTranscrição: {ctx}')


def T(spec, edge="start"):
    if spec is None:
        return None
    if isinstance(spec, (int, float)):
        return float(spec)
    if isinstance(spec, str):
        spec = {"at": spec}
    a, b = find(spec["at"], spec.get("n", 1))
    t = (b["e"] if spec.get("edge", edge) == "end" else a["s"]) + spec.get("off", 0)
    return max(0.0, min(DUR, t))


# ---------------- coleções ----------------
OV, PILLS, SFX, ZOOMS, FLASHES, SHAKES, NO_CAP = [], [], [], [], [], [], []
GAIN = P.get("sfx_gain", 0.19)  # 0.19 = nível aprovado pelo cliente (efeitos bem abaixo da voz)


def sfx(name, t, v=0.7):
    SFX.append((name, round(t, 3), round(v * GAIN, 4)))


def ov(file, start, end, x, y, **kw):
    OV.append(dict(file=file, start=round(start, 3), end=round(end, 3), x=x, y=y, **kw))


def pill(file, text, style, **kw):
    PILLS.append(dict(file=file, text=text, style=style, **kw))
    return file


# ---------------- selo da campanha ----------------
B = P.get("badge")
if B:
    subprocess.run([sys.executable, f"{HERE}/badge.py", GFX, B.get("top", "BLACK"), B.get("band", "FRIDAY"),
                    B.get("tag", "")], check=True, stdout=subprocess.DEVNULL)
    t0 = T(B.get("intro_at", 0.5)); t1 = T(B.get("intro_end")) or t0 + 2.3
    ov("bf_badge.png", t0, t1, 540, 1080, width=860, pop=0.45)
    sfx("impact", t0 - 0.05, 0.9); sfx("whoosh", max(0, t0 - 0.25), 0.5)
    FLASHES.append(dict(t=t0 + 0.03)); SHAKES.append(dict(start=t0 + 0.05, amp=14))
    ZOOMS.append(dict(start=t0, end=t0 + 0.6, to=1.12, punch=True))
    NO_CAP.append((t0, t1))
    if P.get("brand"):
        ov(pill("txt_brand.png", P["brand"], "white", size=60), t0 + 0.9, t1, 540, 1440, pop=0.3)
    if B.get("corner", True):
        ov("bf_badge_small.png", t1, DUR, 200, 165, width=330, pop=0.35)
    for r in B.get("repeat", []):
        a = T(r); b = a + 1.05
        ov("bf_badge.png", a, b, 540, 560, width=760, pop=0.3, rot=-6)
        sfx("impact", a - 0.05, 1.0); FLASHES.append(dict(t=a)); SHAKES.append(dict(start=a, amp=22, dur=0.45))
        ZOOMS.append(dict(start=a, end=a + 0.6, to=1.14, punch=True))

# ---------------- destaques no centro (fundo desfocado) ----------------
HL = []
for h in P.get("highlights", []):
    a = T(h.get("start", h["at"])) + (0 if "start" in h else -0.1)
    b = T(h.get("end", h["at"]), "end") + (0 if "end" in h else 0.3)
    b = max(b, a + 1.2)
    HL.append(dict(start=a, end=b, text=h["text"], size=h.get("size", 132), blur=h.get("blur", True)))
# encolhe a fonte do destaque se a linha mais larga não couber.
# No libass o \fs é a altura da linha (ascendente+descendente ~1,21 em na Inter), por isso divide por 1,21;
# 1,06 = escala final da animação.
from PIL import ImageFont
def fit_size(text, size, maxw=1030):
    lines = re.sub(r"[{}]", "", text).split(r"\N")
    while size > 60:
        f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Black.otf", int(size / 1.21))
        if max(f.getlength(l) for l in lines) * 1.06 + 2 * 9 <= maxw:
            break
        size -= 4
    return size
for h in HL:
    h["size"] = fit_size(h["text"], h["size"])
HL.sort(key=lambda h: h["start"])
for i in range(len(HL) - 1):
    HL[i]["end"] = min(HL[i]["end"], HL[i + 1]["start"])
for h in HL:
    sfx("whoosh", h["start"] - 0.15, 0.7)
    ZOOMS.append(dict(start=h["start"], end=h["end"], **{"from": 1.0}, to=1.06))
    FLASHES.append(dict(t=h["start"], amp=0.35))
if HL:
    HL[-1]["end"] = min(HL[-1]["end"], DUR)

# ---------------- listas laterais (cores, itens) ----------------
for li, L in enumerate(P.get("lists", [])):
    side = L.get("side", "left")
    end = T(L["end"]) if "end" in L else None
    for j, it in enumerate(L["items"]):
        f = pill(f"list{li}_{j}.png", it["text"], L.get("style", "dark"),
                 icon=None if it.get("swatch") else L.get("icon", "check"), swatch=it.get("swatch"),
                 size=L.get("size", 46))
        t0 = T(it["at"]) + it.get("off", 0)
        y = L.get("y0", 470) + j * L.get("step", 118)
        x_edge = 1080 - 30 if side == "right" else 30
        OV.append(dict(file=f, start=t0, end=end or DUR, x=x_edge, y=y, pop=0.3,
                       slide_from=(1400 if side == "right" else -400, y), anchor=side))
        sfx(L.get("sfx", "pop"), t0 - 0.03, L.get("sfx_vol", 0.6))
        if L.get("punch"):
            ZOOMS.append(dict(start=t0, end=t0 + 0.55, to=1.09, punch=True))

# ---------------- preço e desconto ----------------
PR = P.get("price")
if PR:
    if "old_at" in PR:
        a = T(PR["old_at"]); b = T(PR.get("old_end"), "start") or a + 1.6
        ov("price_old.png", a, b, 540, 1060, pop=0.35); NO_CAP.append((a, b)); sfx("cash", a, 0.8)
    if "new_at" in PR:
        a = T(PR["new_at"]); b = T(PR.get("new_end")) or a + 4
        ov("price_new.png", a, b, 540, 1040, pop=0.45, pulse=True, **({} if PR.get("new") else {"width": 1000})); NO_CAP.append((a, b))
        sfx("cash", a, 0.85); FLASHES.append(dict(t=a, amp=0.5))

# ---------------- adesivos e CTA ----------------
for k, st in enumerate(P.get("stickers", [])):
    f = pill(f"st{k}.png", st["text"], st.get("style", "yellow"), icon=st.get("icon"), size=st.get("size", 50))
    a = T(st["at"]) + st.get("off", 0)
    b = T(st["end"]) if "end" in st else a + st.get("dur", 1.5)
    ov(f, a, b, 540, st.get("y", 1200), pop=0.3, pulse=st.get("pulse", False))
    sfx(st.get("sfx", "pop"), a - 0.03, 0.6)
C = P.get("cta")
if C:
    a = T(C["at"])
    f = pill("cta.png", C.get("text", "CHAMA NO ZAP"), C.get("style", "green"), icon=C.get("icon", "chat"),
             size=66, outline=True)
    ov(f, a, DUR, 540, 1440, width=820, pop=0.35, pulse=True)
    sfx("ding", a, 0.8); sfx("impact", DUR - 0.75, 0.7); SHAKES.append(dict(start=DUR - 0.75, amp=12))

# ---------------- extras manuais ----------------
for z in P.get("zooms", []):
    ZOOMS.append(dict(start=T(z["start"]), end=T(z["end"]), **{k: v for k, v in z.items() if k not in ("start", "end")}))
for f in P.get("flashes", []):
    FLASHES.append(dict(f, t=T(f["t"])))
for s in P.get("shakes", []):
    SHAKES.append(dict(s, start=T(s["start"])))
for name, t, v in P.get("sfx", []):
    sfx(name, T(t), v)
for z in P.get("slow_zooms", []):  # aproximação lenta num trecho
    ZOOMS.append({"start": T(z["start"]), "end": T(z["end"]), "from": 1.0, "to": z.get("to", 1.07)})
NO_CAP += [(T(a), T(b)) for a, b in P.get("no_captions", [])]

# ---------------- gráficos ----------------
gcfg = dict(pills=PILLS)
if PR:
    gcfg["price"] = dict(old=PR["old"], discount=PR.get("discount"), new=PR.get("new"),
                         label=PR.get("label", "A SELA CUSTA"))
json.dump(gcfg, open(f"{WORK}/gfxcfg.json", "w"), ensure_ascii=False)
subprocess.run([sys.executable, f"{HERE}/gfx.py", GFX, f"{WORK}/gfxcfg.json"], check=True, stdout=subprocess.DEVNULL)
if not os.path.exists(f"{SFXD}/impact.wav"):
    os.makedirs(SFXD, exist_ok=True)
    subprocess.run([sys.executable, f"{HERE}/sfx.py", SFXD], check=True, stdout=subprocess.DEVNULL)

from PIL import Image
for o in OV:
    a = o.pop("anchor", None)
    if a:
        w = Image.open(f"{GFX}/{o['file']}").width
        o["x"] = o["x"] - w / 2 if a == "right" else o["x"] + w / 2

tl = dict(gfx_dir=GFX, zoom_focus_y=P.get("zoom_focus_y", 0.40), overlays=OV, zooms=ZOOMS, flashes=FLASHES,
          shakes=SHAKES, blurs=[dict(start=h["start"], end=h["end"]) for h in HL if h["blur"]],
          color_fx=P.get("color_fx", []), stars=P.get("stars", False))
json.dump(tl, open(f"{WORK}/timeline.json", "w"), indent=1)

# ---------------- legendas ASS ----------------
def ts(t):
    t = max(0, t); return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"

YEL = "&H0000D4FF&"
ass = [f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Black,{P.get('caption_size', 86)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,7,4,2,60,60,{P.get('caption_margin', 400)},1
Style: Hi,Inter Black,132,&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,0,0,0,0,100,100,0,0,1,9,8,5,50,50,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""]
busy_w = [(h["start"], h["end"]) for h in HL] + NO_CAP
busy = lambda a, b: any(a < y - 0.05 and b > x + 0.05 for x, y in busy_w)

groups, cur = [], []
MAXC = P.get("caption_max_chars", 17)
for i, w in enumerate(words):
    if cur and len(" ".join(x["w"] for x in cur + [w]).rstrip(",.")) > MAXC:
        groups.append(cur); cur = []
    cur.append(w)
    nxt = words[i + 1] if i + 1 < len(words) else None
    if len(cur) >= 3 or re.search(r"[.,!?]$", w["w"]) or (nxt and nxt["s"] - w["e"] > 0.35):
        groups.append(cur); cur = []
if cur:
    groups.append(cur)
flat = [w for g in groups for w in g]
nxt = {id(w): (flat[k + 1]["s"] if k + 1 < len(flat) else DUR) for k, w in enumerate(flat)}
for g in groups:
    for j, w in enumerate(g):
        t0 = w["s"]; t1 = nxt[id(w)] if j + 1 < len(g) else min(nxt[id(w)], w["e"] + 0.3)
        if busy(t0, t1):
            continue
        parts = [(r"{\c" + YEL + r"\fscx112\fscy112}" + x["w"].upper().rstrip(",.") + r"{\c&H00FFFFFF&\fscx100\fscy100}")
                 if k == j else x["w"].upper().rstrip(",.") for k, x in enumerate(g)]
        fade = r"{\fad(60,0)}" if j == 0 else ""
        ass.append(f"Dialogue: 0,{ts(t0)},{ts(t1)},Cap,,0,0,0,,{fade}{' '.join(parts)}")
for h in HL:
    t = re.sub(r"\{([^}]*)\}", lambda m: r"{\c" + YEL + "}" + m.group(1) + r"{\c&H00FFFFFF&}", h["text"])
    anim = (r"{\pos(540,960)\fs%d\fad(80,140)\fscx40\fscy40\t(0,160,\fscx114\fscy114)\t(160,280,\fscx100\fscy100)"
            r"\t(280,%d,\fscx106\fscy106)}" % (h["size"], int((h["end"] - h["start"]) * 1000)))
    ass.append(f"Dialogue: 1,{ts(h['start'])},{ts(h['end'])},Hi,,0,0,0,,{anim}{t}")
open(f"{WORK}/captions.ass", "w").write("\n".join(ass) + "\n")
json.dump(sorted(SFX, key=lambda s: s[1]), open(f"{WORK}/sfx.json", "w"))

print(f"duração {DUR:.2f}s | destaques {len(HL)} | overlays {len(OV)} | efeitos sonoros {len(SFX)}")
for h in HL:
    print(f"  destaque {h['start']:6.2f}-{h['end']:6.2f}  fonte {h['size']}  {re.sub(r'[{}]', '', h['text']).replace(chr(92) + 'N', ' ')}")
if args.no_render:
    sys.exit(0)

# ---------------- render ----------------
if not (args.skip_fx and os.path.exists(f"{WORK}/fx.mp4")):
    subprocess.run([sys.executable, f"{HERE}/render_fx.py", f"{WORK}/timeline.json", f"{WORK}/base.mov", f"{WORK}/fx.mp4"],
                   check=True, stdout=subprocess.DEVNULL)
out = os.path.abspath(P["output"])
os.makedirs(os.path.dirname(out), exist_ok=True)
M = P.get("music")
cmd = [sys.executable, f"{HERE}/final.py", WORK, out]
if M:
    cmd += [os.path.abspath(M["file"]), str(M.get("start", 0)), str(M.get("db", -13))]
subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
size = os.path.getsize(out) / 1e6
print(f"pronto: {out} ({size:.1f} MB)")
