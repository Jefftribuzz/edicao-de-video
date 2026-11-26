"""Roteiro da edição: gera legendas (ASS), timeline de efeitos e mixagem de áudio.

Uso: python3 build.py <work_dir>
"""
import json, os, re, subprocess, sys

WORK = sys.argv[1]
TR = json.load(open(f"{WORK}/transcript_final.json"))
DUR = 62.96

# ---------------- palavras (com correções de vocabulário) ----------------
words = []
for s in TR["segments"]:
    for w in s["words"]:
        words.append(dict(w=w["word"].strip(), s=w["start"], e=w["end"]))

# ---------------- destaques no centro (com fundo desfocado) ----------------
# texto com {chave} = palavra em amarelo; '\N' quebra a linha
HIGHLIGHTS = [
    dict(start=2.85, end=5.20, text="ESSA É A SUA\\N{MELHOR}\\N{OPORTUNIDADE}", blur=True),
    dict(start=16.30, end=18.70, text="A SELA VAI\\N{COMPLETA}\\NPRA VOCÊ", blur=True),
    dict(start=25.55, end=28.20, text="LINDA\\N{BARRIGUEIRA}\\NEM {NEOPRENE}", blur=True),
    dict(start=41.65, end=43.00, text="MAS...", blur=True, size=190),
    dict(start=43.00, end=44.05, text="NA {BLACK}\\N{FRIDAY}", blur=True, size=170),
    dict(start=46.30, end=48.30, text="DESCONTO DE\\N{R$ 250}", blur=True, size=150),
    dict(start=55.50, end=57.25, text="A {MAIS VENDIDA}\\NDO MERCADO", blur=True),
    dict(start=60.50, end=DUR, text="CHAMA AQUI\\NNO {ZAP} QUE\\NDÁ {NEGÓCIO}", blur=True),
]

# ---------------- elementos gráficos (overlays) ----------------
# x,y = centro do elemento em 1080x1920
OV = []
def ov(file, start, end, x, y, **kw):
    OV.append(dict(file=file, start=start, end=end, x=x, y=y, **kw))

# abertura: selo grande -> pequeno no canto pelo resto do vídeo
ov("bf_badge.png", 0.55, 2.80, 540, 1080, width=860, pop=0.45)
ov("txt_selaria.png", 1.45, 2.80, 540, 1440, pop=0.3)
ov("bf_badge_small.png", 2.80, DUR, 200, 165, width=330, pop=0.35)
# selo grande de novo no "na Black Friday"
ov("bf_badge.png", 43.00, 44.05, 540, 560, width=760, pop=0.3, rot=-6)

ov("tag_pronta.png", 7.30, 8.30, 540, 1200, pop=0.3)

# cores: etiquetas empilhadas à direita
COLORS = [("c_preta.png", 9.18), ("c_marrom.png", 10.30), ("c_marrom2.png", 10.94),
          ("c_art1.png", 13.70), ("c_art2.png", 15.15)]
for i, (f, t0) in enumerate(COLORS):
    ov(f, t0, 16.20, 1080 - 30, 470 + i * 118, pop=0.35, slide_from=(1400, 470 + i * 118), anchor="right")

# itens que acompanham a sela (esquerda)
ITEMS_A = [("i_peitoral.png", 18.82), ("i_lategos.png", 20.26), ("i_paralama.png", 21.48), ("i_estribos.png", 22.58)]
for i, (f, t0) in enumerate(ITEMS_A):
    ov(f, t0, 24.40, 30, 470 + i * 118, pop=0.3, slide_from=(-400, 470 + i * 118), anchor="left")
ITEMS_B = [("i_nobuck.png", 29.84), ("i_couro.png", 31.16), ("i_suador.png", 32.56), ("i_inox.png", 36.30)]
for i, (f, t0) in enumerate(ITEMS_B):
    ov(f, t0, 39.00, 30, 470 + i * 118, pop=0.3, slide_from=(-400, 470 + i * 118), anchor="left")

# preço
ov("price_old.png", 40.15, 41.60, 540, 1060, pop=0.35)
ov("price_new.png", 48.30, 52.40, 540, 1040, width=1000, pop=0.45, pulse=True)
ov("tag_envio.png", 50.30, 52.40, 540, 1450, pop=0.3)
ov("tag_brinde.png", 54.60, 55.50, 540, 1150, pop=0.3)
ov("tag_tempo.png", 57.30, 60.45, 540, 1160, pop=0.3, pulse=True)
ov("btn_zap.png", 61.30, DUR, 540, 1440, width=820, pop=0.35, pulse=True)

# âncoras esquerda/direita -> centro
GFX = f"{WORK}/gfx"
from PIL import Image
for o in OV:
    a = o.pop("anchor", None)
    if a:
        w = Image.open(f"{GFX}/{o['file']}").width
        o["x"] = o["x"] - w / 2 if a == "right" else o["x"] + w / 2
        sx, sy = o["slide_from"]
        o["slide_from"] = (sx, sy)

# ---------------- zooms, flashes, tremidas, cor ----------------
ZOOMS = [
    dict(start=0.0, end=2.8, frm=1.0, to=1.08),
    dict(start=0.62, end=1.2, to=1.12, punch=True),
    dict(start=5.83, end=8.2, frm=1.0, to=1.07),
    dict(start=16.3, end=18.7, frm=1.0, to=1.06),
    dict(start=24.4, end=28.2, frm=1.0, to=1.08),
    dict(start=39.0, end=41.6, frm=1.0, to=1.07),
    dict(start=43.0, end=43.6, to=1.14, punch=True),
    dict(start=47.5, end=48.1, to=1.12, punch=True),
    dict(start=57.3, end=60.5, frm=1.0, to=1.1),
    dict(start=60.5, end=DUR, frm=1.0, to=1.06),
]
# punch-in em cada cor citada
for _, t0 in [("preta", 9.18), ("marrom", 10.30), ("m2", 10.94), ("art", 12.76), ("a1", 13.70), ("hav", 15.60)]:
    ZOOMS.append(dict(start=t0, end=t0 + 0.55, to=1.09, punch=True))
for z in ZOOMS:
    if "frm" in z:
        z["from"] = z.pop("frm")

FLASHES = [dict(t=0.58), dict(t=5.83, amp=0.6), dict(t=8.5, amp=0.35), dict(t=16.25, amp=0.4),
           dict(t=39.0, amp=0.6), dict(t=43.0), dict(t=47.5, amp=0.7), dict(t=48.3, amp=0.5),
           dict(t=60.5, amp=0.45)]
# flashes leves coloridos nas cores (brancos curtos)
for t0 in (9.18, 10.30, 10.94, 12.76, 13.70, 15.60):
    FLASHES.append(dict(t=t0, amp=0.35, dur=0.12))
SHAKES = [dict(start=0.6, amp=14), dict(start=43.0, amp=22, dur=0.45), dict(start=47.5, amp=18), dict(start=62.2, amp=12)]
COLOR_FX = [dict(start=8.45, end=16.2), dict(start=25.6, end=28.2)]

tl = dict(gfx_dir=GFX, zoom_focus_y=0.40, overlays=OV, zooms=ZOOMS, flashes=FLASHES, shakes=SHAKES,
          blurs=[dict(start=h["start"], end=h["end"]) for h in HIGHLIGHTS if h.get("blur")],
          color_fx=COLOR_FX)
json.dump(tl, open(f"{WORK}/timeline.json", "w"), indent=1)

# ---------------- legendas ASS ----------------
def ts(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

YEL = "&H0000D4FF&"
ass = ["""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Black,86,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,7,4,2,60,60,400,1
Style: Hi,Inter Black,132,&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,0,0,0,0,100,100,0,0,1,9,8,5,50,50,0,1
Style: Sub,Inter ExtraBold,58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,1,0,1,6,3,5,50,50,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""]


NO_CAP = [(0.55, 2.80), (40.15, 41.60), (48.30, 52.40)]


def busy(t0, t1):
    """Legenda escondida quando há destaque central ou cartão de preço."""
    for a, b in [(h["start"], h["end"]) for h in HIGHLIGHTS] + NO_CAP:
        if t0 < b - 0.05 and t1 > a + 0.05:
            return True
    return False


# Correções de vocabulário ("errado" -> "certo"), aplicadas palavra a palavra
FIX = json.load(open(f"{WORK}/fixes.json"))
for w in words:
    key = re.sub(r"[.,!?]", "", w["w"]).lower()
    if key in FIX:
        punct = re.findall(r"[.,!?]+$", w["w"])
        w["w"] = FIX[key] + (punct[0] if punct else "")

# "a sinox" -> "em inox"
for i in range(len(words) - 1):
    if words[i]["w"].lower() == "a" and words[i + 1]["w"].startswith("inox"):
        words[i]["w"] = "em"

# junta tokens de preço quebrados ("R" "$1" ".899" ",00,")
merged = []
for w in words:
    if merged and (re.match(r"^[\$\.,]", w["w"]) and re.search(r"[R\d]$", merged[-1]["w"].rstrip(",."))):
        merged[-1]["w"] += w["w"]; merged[-1]["e"] = w["e"]
    else:
        merged.append(dict(w))
words = [w for w in merged if w["w"]]
for w in words:
    w["w"] = re.sub(r"R\$(\d)", r"R$ \1", w["w"]).replace(",00,", ",").replace(",00", "")

# grupos de até 3 palavras / 18 caracteres, quebrando em pontuação e pausas
groups, cur = [], []
for i, w in enumerate(words):
    if cur and len(" ".join(x["w"] for x in cur + [w]).rstrip(",.")) > 17:
        groups.append(cur); cur = []
    cur.append(w)
    text = " ".join(x["w"] for x in cur)
    nxt = words[i + 1] if i + 1 < len(words) else None
    gap = (nxt["s"] - w["e"]) if nxt else 9
    if len(cur) >= 3 or len(text) >= 16 or re.search(r"[.,!?]$", w["w"]) or gap > 0.35:
        groups.append(cur); cur = []
if cur:
    groups.append(cur)

flat = [w for g in groups for w in g]
nxt_start = {id(w): (flat[k + 1]["s"] if k + 1 < len(flat) else 99) for k, w in enumerate(flat)}
for g in groups:
    for j, w in enumerate(g):
        t0 = w["s"]
        t1 = nxt_start[id(w)] if j + 1 < len(g) else min(nxt_start[id(w)], w["e"] + 0.3)
        if busy(t0, t1):
            continue
        parts = []
        for k, x in enumerate(g):
            txt = x["w"].upper().rstrip(",.")
            if k == j:
                parts.append(r"{\c" + YEL + r"\fscx112\fscy112}" + txt + r"{\c&H00FFFFFF&\fscx100\fscy100}")
            else:
                parts.append(txt)
        pre = r"{\fad(60,0)}" if j == 0 else ""
        ass.append(f"Dialogue: 0,{ts(t0)},{ts(t1)},Cap,,0,0,0,,{pre}{' '.join(parts)}")


def hi_text(h):
    t = h["text"]
    t = re.sub(r"\{([^}]*)\}", lambda m: r"{\c" + YEL + "}" + m.group(1) + r"{\c&H00FFFFFF&}", t)
    size = h.get("size", 132)
    anim = (r"{\fs%d\fad(80,140)\fscx40\fscy40\t(0,160,\fscx114\fscy114)\t(160,280,\fscx100\fscy100)"
            r"\t(280,%d,\fscx106\fscy106)}" % (size, int((h["end"] - h["start"]) * 1000)))
    return anim + t


for h in HIGHLIGHTS:
    y = 960
    ass.append(f"Dialogue: 1,{ts(h['start'])},{ts(h['end'])},Hi,,0,0,0,,{{\\pos(540,{y})}}{hi_text(h)}")

open(f"{WORK}/captions.ass", "w").write("\n".join(ass) + "\n")

# ---------------- efeitos sonoros ----------------
SFX = [
    ("impact", 0.50, 0.9), ("whoosh", 0.30, 0.5),
    ("whoosh", 2.70, 0.7), ("pop", 4.14, 0.6),
    ("swish", 5.78, 0.6), ("pop", 7.30, 0.6),
    ("whoosh", 8.35, 0.6),
    ("sparkle", 9.15, 0.75), ("sparkle", 10.27, 0.7), ("sparkle", 10.91, 0.7),
    ("sparkle", 12.73, 0.75), ("sparkle", 13.67, 0.7), ("sparkle", 15.12, 0.75), ("sparkle", 15.57, 0.6),
    ("whoosh", 16.15, 0.7), ("pop", 17.00, 0.5),
    ("pop", 18.82, 0.6), ("pop", 20.26, 0.6), ("pop", 21.48, 0.6), ("pop", 22.58, 0.6),
    ("whoosh", 25.40, 0.7), ("sparkle", 25.90, 0.7), ("sparkle", 26.84, 0.55),
    ("pop", 29.84, 0.6), ("pop", 31.16, 0.6), ("pop", 32.56, 0.6), ("pop", 36.30, 0.6),
    ("swish", 38.95, 0.6), ("cash", 40.15, 0.8),
    ("riser", 41.45, 0.6), ("impact", 42.95, 1.0),
    ("whoosh", 46.15, 0.7), ("impact", 47.45, 0.85), ("cash", 48.30, 0.85),
    ("pop", 50.30, 0.5), ("ding", 54.60, 0.7), ("sparkle", 54.70, 0.5),
    ("whoosh", 55.35, 0.7), ("pop", 55.80, 0.5),
    ("swish", 57.25, 0.6),
    ("whoosh", 60.35, 0.7), ("ding", 61.30, 0.8), ("impact", 62.20, 0.7),
]
json.dump(SFX, open(f"{WORK}/sfx.json", "w"))
print("captions:", sum(1 for l in ass if l.startswith("Dialogue")), "overlays:", len(OV), "sfx:", len(SFX))
