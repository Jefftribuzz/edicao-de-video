"""Aplica efeitos visuais quadro a quadro.

Uso: python3 render_fx.py timeline.json entrada.mov saida.mp4

Lê os quadros com ffmpeg (rgb24), aplica zoom/punch-in, tremida, desfoque de
fundo nos destaques, flashes, realce de cor com brilhos, selos e cartões de
preço, e grava o vídeo (sem áudio) de volta com ffmpeg.
"""
import json, math, random, subprocess, sys
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

W, H, FPS = 1080, 1920, 30
tl = json.load(open(sys.argv[1]))
SRC, DST = sys.argv[2], sys.argv[3]
T0 = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
TDUR = sys.argv[5] if len(sys.argv) > 5 else None
GFX = tl["gfx_dir"]


def ease_out_back(x):
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def ease_in_out(x):
    return 0.5 - 0.5 * math.cos(math.pi * max(0, min(1, x)))


def window(t, a, b, fade_in=0.15, fade_out=0.2):
    """0..1 dentro de [a,b] com rampas suaves."""
    if t < a or t > b:
        return 0.0
    return min(1.0, (t - a) / fade_in if fade_in else 1, (b - t) / fade_out if fade_out else 1)


def comp_clip(frame, im, x, y):
    """alpha_composite que aceita posições parcialmente fora do quadro."""
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(im.width, W - x), min(im.height, H - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    frame.alpha_composite(im, (x + sx0, y + sy0), (sx0, sy0, sx1, sy1))


# ---------- recursos ----------
overlays = []
for o in tl["overlays"]:
    im = Image.open(f"{GFX}/{o['file']}").convert("RGBA")
    if "width" in o:
        r = o["width"] / im.width
        im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    overlays.append(im)

# brilhos: partículas fixas por sementes (estrelas de 4 pontas)
def star(size, color):
    s = size * 4
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = s / 2
    d.polygon([(c, 0), (c + s * 0.08, c - s * 0.08), (s, c), (c + s * 0.08, c + s * 0.08),
               (c, s), (c - s * 0.08, c + s * 0.08), (0, c), (c - s * 0.08, c - s * 0.08)], fill=color)
    glow = im.filter(ImageFilter.GaussianBlur(s * 0.08))
    im = Image.alpha_composite(glow, im)
    return im.resize((size * 2, size * 2), Image.LANCZOS)

STAR_COLORS = [(255, 255, 255, 255), (255, 230, 120, 255), (120, 200, 255, 255), (255, 120, 140, 255)]
random.seed(3)
stars = []
for i in range(46):
    stars.append(dict(x=random.uniform(40, W - 40), y=random.uniform(150, H - 200),
                      ph=random.uniform(0, 1), sp=random.uniform(0.9, 1.8),
                      img=star(random.randint(14, 34), random.choice(STAR_COLORS))))

# luz colorida (light leak) – gradiente radial pré-calculado
def radial(color, rad):
    im = Image.new("RGBA", (rad * 2, rad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for r in range(rad, 0, -6):
        a = int(150 * (1 - r / rad) ** 1.6)
        d.ellipse([rad - r, rad - r, rad + r, rad + r], fill=color[:3] + (a,))
    return im.filter(ImageFilter.GaussianBlur(20))

LEAKS = [radial((255, 60, 60), 520), radial((40, 110, 255), 520), radial((255, 200, 0), 460)]


# ---------- curvas por tempo ----------
def zoom_at(t):
    z = 1.0
    for zm in tl["zooms"]:
        a, b, z0, z1 = zm["start"], zm["end"], zm.get("from", 1.0), zm["to"]
        if a <= t <= b:
            k = (t - a) / (b - a)
            k = ease_out_back(min(1, k * 4)) if zm.get("punch") else ease_in_out(k)
            z = max(z, z0 + (z1 - z0) * k)
            if zm.get("punch") and k > 0.75:  # solta no fim
                z = max(1.0, z - (z1 - z0) * ease_in_out((k - 0.75) / 0.25))
    return z


def shake_at(t):
    for s in tl["shakes"]:
        if s["start"] <= t <= s["start"] + s.get("dur", 0.35):
            k = 1 - (t - s["start"]) / s.get("dur", 0.35)
            amp = s.get("amp", 18) * k
            return (math.sin(t * 93) * amp, math.cos(t * 71) * amp)
    return (0, 0)


def flash_at(t):
    a = 0.0
    for f in tl["flashes"]:
        d = t - f["t"]
        if 0 <= d <= f.get("dur", 0.18):
            a = max(a, f.get("amp", 0.85) * (1 - d / f.get("dur", 0.18)))
    return a


def blur_at(t):
    return max([window(t, b["start"], b["end"], 0.18, 0.22) for b in tl["blurs"]] + [0])


def color_at(t):
    return max([window(t, c["start"], c["end"], 0.3, 0.4) for c in tl["color_fx"]] + [0])


def paste_anim(frame, im, o, t):
    a, b = o["start"], o["end"]
    if not (a <= t <= b):
        return
    pin = o.get("pop", 0.35)
    k = (t - a) / pin if pin else 1
    s = ease_out_back(min(1.0, k)) if k < 1 else 1.0
    if o.get("pulse"):
        s *= 1 + 0.035 * math.sin((t - a) * 2 * math.pi * 1.6)
    out_k = (b - t) / 0.25
    alpha = min(1.0, k * 2, out_k)
    if out_k < 1:
        s *= 0.85 + 0.15 * out_k
    s = max(0.05, s)
    rot = o.get("rot", 0)
    img = im
    if abs(s - 1) > 0.01:
        img = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
    if rot:
        img = img.rotate(rot * min(1.0, k), expand=True, resample=Image.BILINEAR)
    if alpha < 1:
        r, g, bb, al = img.split()
        al = al.point(lambda v: int(v * alpha))
        img = Image.merge("RGBA", (r, g, bb, al))
    cx, cy = o["x"], o["y"]
    if "slide_from" in o and k < 1:
        sx, sy = o["slide_from"]
        e = ease_out_back(min(1, k))
        cx = sx + (cx - sx) * e; cy = sy + (cy - sy) * e
    comp_clip(frame, img, int(cx - img.width / 2), int(cy - img.height / 2))


# ---------- pipeline ----------
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(T0)] + (["-t", TDUR] if TDUR else []) + ["-i", SRC, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                        "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p", DST],
                       stdin=subprocess.PIPE)
white = Image.new("RGB", (W, H), (255, 255, 255))
fsize = W * H * 3
i = 0
while True:
    buf = dec.stdout.read(fsize)
    if len(buf) < fsize:
        break
    t = T0 + i / FPS
    img = Image.frombuffer("RGB", (W, H), buf, "raw", "RGB", 0, 1)

    # zoom + tremida
    z = zoom_at(t)
    dx, dy = shake_at(t)
    if z > 1.001 or dx or dy:
        z = max(z, 1.04) if (dx or dy) else z
        cw, ch = W / z, H / z
        cx = W / 2 + dx; cy = H * tl.get("zoom_focus_y", 0.42) + dy
        x0 = min(max(0, cx - cw / 2), W - cw); y0 = min(max(0, cy - ch / 2), H - ch)
        img = img.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))

    # realce de cor (trecho das cores)
    c = color_at(t)
    if c > 0:
        img = ImageEnhance.Color(img).enhance(1 + 0.55 * c)
        img = ImageEnhance.Contrast(img).enhance(1 + 0.12 * c)

    # fundo desfocado nos destaques
    b = blur_at(t)
    if b > 0:
        bl = img.resize((W // 6, H // 6), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3.2)).resize((W, H), Image.BILINEAR)
        bl = ImageEnhance.Brightness(bl).enhance(0.55)
        img = Image.blend(img, bl, b)

    frame = img.convert("RGBA")

    # luzes coloridas e brilhos no trecho das cores
    if c > 0:
        for j, lk in enumerate(LEAKS):
            ang = t * 0.9 + j * 2.1
            px = W / 2 + math.cos(ang) * 420 - lk.width / 2
            py = H * 0.45 + math.sin(ang * 1.3) * 650 - lk.height / 2
            l = lk
            if c < 1:
                r_, g_, b_, a_ = lk.split(); a_ = a_.point(lambda v: int(v * c)); l = Image.merge("RGBA", (r_, g_, b_, a_))
            comp_clip(frame, l, int(px), int(py))
        for s in (stars if tl.get("stars", False) else []):  # estrelinhas: desligadas por padrão (cliente não gostou)
            v = (math.sin((t * s["sp"] + s["ph"]) * 2 * math.pi) + 1) / 2
            v = v ** 3 * c
            if v < 0.05:
                continue
            im = s["img"]
            sc = 0.4 + 0.8 * v
            im2 = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BILINEAR)
            r_, g_, b_, a_ = im2.split(); a_ = a_.point(lambda q, v=v: int(q * v)); im2 = Image.merge("RGBA", (r_, g_, b_, a_))
            comp_clip(frame, im2, int(s["x"] - im2.width / 2), int(s["y"] - im2.height / 2))

    # selos, preço, cartões
    for o, im in zip(tl["overlays"], overlays):
        paste_anim(frame, im, o, t)

    out = frame.convert("RGB")
    fa = flash_at(t)
    if fa > 0:
        out = Image.blend(out, white, fa)
    # vinheta de entrada/saída
    if t < 0.25:
        out = Image.blend(Image.new("RGB", (W, H)), out, t / 0.25)
    enc.stdin.write(out.tobytes())
    i += 1
    if i % 150 == 0:
        print(f"{t:.1f}s", flush=True)

enc.stdin.close(); enc.wait(); dec.wait()
print("frames", i)
