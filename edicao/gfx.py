"""Primitivas gráficas sobre PIL, com anti-aliasing por supersampling.

Tudo trabalha com imagens RGBA. Sprites estáticos ficam em cache; o que muda
por quadro (contadores, setas sendo desenhadas) é desenhado em telas locais.
"""
import math
from functools import lru_cache

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

FONTES = {
    "black": "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf",
    "extrabold": "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf",
    "bold": "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
    "semibold": "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
}
FONTE_EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
ALTURA_CAPS = 0.727  # altura das maiúsculas da Inter, em em

SS = 3  # fator de supersampling


# ---------------------------------------------------------------- básicos

def nova(w, h):
    return Image.new("RGBA", (max(1, int(round(w))), max(1, int(round(h)))), (0, 0, 0, 0))


def rgba(cor, a=255):
    return cor if len(cor) == 4 else (*cor, a)


def com_alpha(img, a):
    if a >= 0.999:
        return img
    img = img.copy()
    img.putalpha(img.getchannel("A").point(lambda v: int(v * a + 0.5)))
    return img


def colocar(dst, img, x, y, s=1.0, a=1.0, ax=0.5, ay=0.5, rot=0.0):
    """Compõe `img` em `dst` com âncora (ax, ay) no ponto (x, y)."""
    if img is None or a <= 0.004 or s <= 0.01:
        return
    if abs(s - 1) > 1e-3:
        img = img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.BICUBIC)
    if abs(rot) > 0.05:
        img = img.rotate(rot, Image.BICUBIC, expand=True)
    img = com_alpha(img, a)
    px = round(x - img.width * ax)
    py = round(y - img.height * ay)
    sx0, sy0 = max(0, -px), max(0, -py)
    sx1, sy1 = min(img.width, dst.width - px), min(img.height, dst.height - py)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    if (sx0, sy0, sx1, sy1) != (0, 0, img.width, img.height):
        img = img.crop((sx0, sy0, sx1, sy1))
    dst.alpha_composite(img, (px + sx0, py + sy0))


class Tela:
    """Tela supersampled: desenhe em coordenadas finais, ela escala por SS."""

    def __init__(self, w, h, ss=SS):
        self.w, self.h, self.ss = int(w), int(h), ss
        self.img = nova(self.w * ss, self.h * ss)
        self.d = ImageDraw.Draw(self.img)

    def p(self, *xy):
        return [v * self.ss for v in xy]

    def linha(self, pts, cor, larg, curva=True):
        flat = [c * self.ss for pt in pts for c in pt]
        self.d.line(flat, fill=rgba(cor), width=int(larg * self.ss), joint="curve" if curva else None)
        if curva:  # pontas arredondadas
            r = larg * self.ss / 2
            for x, y in (pts[0], pts[-1]):
                self.d.ellipse([x * self.ss - r, y * self.ss - r, x * self.ss + r, y * self.ss + r], fill=rgba(cor))

    def poligono(self, pts, cor):
        self.d.polygon([c * self.ss for pt in pts for c in pt], fill=rgba(cor))

    def elipse(self, cx, cy, rx, ry, cor=None, borda=None, larg=0):
        box = self.p(cx - rx, cy - ry, cx + rx, cy + ry)
        self.d.ellipse(box, fill=rgba(cor) if cor else None,
                       outline=rgba(borda) if borda else None, width=int(larg * self.ss))

    def arco(self, cx, cy, rx, ry, a0, a1, cor, larg):
        if a1 - a0 < 0.5:
            return
        box = self.p(cx - rx, cy - ry, cx + rx, cy + ry)
        self.d.arc(box, a0, a1, fill=rgba(cor), width=int(larg * self.ss))

    def ret(self, x0, y0, x1, y1, r, cor):
        if x1 - x0 < 1 or y1 - y0 < 1:
            return
        r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
        self.d.rounded_rectangle(self.p(x0, y0, x1, y1), radius=r * self.ss, fill=rgba(cor))

    def final(self):
        return self.img.resize((self.w, self.h), Image.LANCZOS)


# ---------------------------------------------------------------- texto

@lru_cache(maxsize=None)
def fonte(nome, tam):
    return ImageFont.truetype(FONTES[nome], int(tam))


def largura_texto(txt, nome, tam, tracking=0):
    f = fonte(nome, tam)
    if not tracking:
        return f.getlength(txt)
    # com tracking cada letra é desenhada isolada, sem kerning
    return sum(f.getlength(ch) for ch in txt) + tracking * max(0, len(txt) - 1)


def tam_que_cabe(txt, nome, tam_max, largura, tracking=0, tam_min=20):
    tam = tam_max
    while tam > tam_min and largura_texto(txt, nome, tam, tracking) > largura:
        tam -= 2
    return tam


def topo_caps(nome, tam):
    """Distância do topo do sprite de texto até o topo das maiúsculas."""
    asc, _ = fonte(nome, tam).getmetrics()
    return asc - ALTURA_CAPS * tam


@lru_cache(maxsize=1024)
def texto(txt, nome, tam, cor, tracking=0):
    """Sprite de texto; a altura é ascendente+descendente da fonte."""
    f = fonte(nome, tam)
    asc, desc = f.getmetrics()
    img = nova(math.ceil(largura_texto(txt, nome, tam, tracking)) + 6, asc + desc)
    d = ImageDraw.Draw(img)
    if not tracking:
        d.text((3, 0), txt, font=f, fill=rgba(cor))
    else:
        x = 3
        for ch in txt:
            d.text((x, 0), ch, font=f, fill=rgba(cor))
            x += f.getlength(ch) + tracking
    return img


def colocar_texto_caps(dst, txt, nome, tam, cor, x, y_centro, ax=0.0, a=1.0, tracking=0):
    """Posiciona texto pelo centro vertical das maiúsculas."""
    img = texto(txt, nome, tam, cor, tracking)
    topo = y_centro - ALTURA_CAPS * tam / 2 - topo_caps(nome, tam)
    colocar(dst, img, x, topo, a=a, ax=ax, ay=0.0)
    return img.width


@lru_cache(maxsize=None)
def emoji(ch, tam):
    f = ImageFont.truetype(FONTE_EMOJI, 109)
    img = nova(200, 200)
    ImageDraw.Draw(img).text((100, 100), ch, font=f, embedded_color=True, anchor="mm")
    img = img.crop(img.getbbox())
    s = tam / max(img.size)
    return img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)


# ---------------------------------------------------------------- formas

@lru_cache(maxsize=256)
def ret_arredondado(w, h, r, cor):
    t = Tela(w, h)
    t.ret(0, 0, w, h, r, cor)
    return t.final()


@lru_cache(maxsize=256)
def circulo(d, cor, borda=0, cor_borda=None):
    t = Tela(d, d)
    t.elipse(d / 2, d / 2, d / 2, d / 2, cor=cor_borda or cor)
    if borda and cor_borda:
        t.elipse(d / 2, d / 2, d / 2 - borda, d / 2 - borda, cor=cor)
    return t.final()


def sombra(img, desfoque=24, opac=0.5, dy=12):
    """Devolve (imagem com sombra projetada, margem acrescentada em cada lado)."""
    m = desfoque * 2 + abs(dy)
    out = nova(img.width + 2 * m, img.height + 2 * m)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 255))
    sh.putalpha(img.getchannel("A").point(lambda v: int(v * opac)))
    out.paste(sh, (m, m + dy))
    out = out.filter(ImageFilter.GaussianBlur(desfoque))
    out.alpha_composite(img, (m, m))
    return out, m


def com_sombra(img, desfoque=24, opac=0.5, dy=12):
    return sombra(img, desfoque, opac, dy)[0]


def faixa_listrada(w, h, listras):
    img = nova(w, h)
    d = ImageDraw.Draw(img)
    x, i = 0, 0
    while x < w:
        cor, lw = listras[i % len(listras)]
        d.rectangle([x, 0, x + lw - 1, h], fill=rgba(cor))
        x += lw
        i += 1
    return img


def recortar_com_mascara(img, mascara):
    """Aplica a máscara (canal L) multiplicando o alpha de img."""
    img = img.copy()
    img.putalpha(ImageChops.multiply(img.getchannel("A"), mascara))
    return img


def polilinha_parcial(pts, frac):
    """Pontos da polilinha até a fração `frac` do comprimento total."""
    if frac >= 1:
        return list(pts)
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    alvo = sum(seg) * max(0.0, frac)
    out = [pts[0]]
    for i, s in enumerate(seg):
        if alvo <= s:
            k = alvo / s if s else 0
            out.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * k,
                        pts[i][1] + (pts[i + 1][1] - pts[i][1]) * k))
            return out
        alvo -= s
        out.append(pts[i + 1])
    return out


def ponta_seta(t, x, y, ang, tam, cor):
    """Desenha a cabeça de seta triangular apontando no ângulo `ang` (rad)."""
    ca, sa = math.cos(ang), math.sin(ang)
    p1 = (x + ca * tam * 0.55, y + sa * tam * 0.55)
    base = (x - ca * tam * 0.45, y - sa * tam * 0.45)
    p2 = (base[0] - sa * tam * 0.55, base[1] + ca * tam * 0.55)
    p3 = (base[0] + sa * tam * 0.55, base[1] - ca * tam * 0.55)
    t.poligono([p1, p2, p3], cor)


def gradiente_vertical(w, h, cor, a0, a1, curva=lambda x: x):
    alpha = np.array([int(255 * (a0 + (a1 - a0) * curva(y / max(1, h - 1)))) for y in range(h)], dtype=np.uint8)
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = cor
    arr[..., 3] = alpha[:, None]
    return Image.fromarray(arr, "RGBA")


def brilho_diagonal(img, pos, largura=0.18, intensidade=0.85):
    """Passa uma faixa de brilho diagonal sobre os pixels opacos de img.

    `pos` vai de 0 (antes da borda esquerda) a 1 (depois da direita).
    """
    w, h = img.size
    yy, xx = np.mgrid[0:h, 0:w]
    u = (xx + yy * 0.45) / (w + h * 0.45)
    centro = -largura + pos * (1 + 2 * largura)
    banda = np.clip(1 - np.abs(u - centro) / largura, 0, 1) ** 2
    a = np.asarray(img.getchannel("A"), dtype=np.float32) / 255
    luz = (banda * a * intensidade * 255).astype(np.uint8)
    camada = Image.new("RGBA", img.size, (255, 255, 255, 0))
    camada.putalpha(Image.fromarray(luz, "L"))
    out = img.copy()
    out.alpha_composite(camada)
    return out
