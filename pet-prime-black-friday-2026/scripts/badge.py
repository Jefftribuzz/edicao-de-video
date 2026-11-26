"""Gera o selo 'BLACK FRIDAY 2026' em PNG transparente (design próprio)."""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = sys.argv[1]
BLACK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
BLACK_IT = "/usr/share/fonts/opentype/inter/Inter-BlackItalic.otf"
YEL = (255, 212, 0, 255)
RED = (230, 30, 45, 255)


def font(p, s):
    return ImageFont.truetype(p, s)


def text_w(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[2] - b[0], b[3] - b[1], b[0], b[1]


def badge(scale=1.0):
    W, H = int(900 * scale), int(520 * scale)
    pad = int(70 * scale)
    img = Image.new("RGBA", (W + pad * 2, H + pad * 2), (0, 0, 0, 0))
    # sombra
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 14 * scale, pad + W, pad + H + 14 * scale], 48 * scale, fill=(0, 0, 0, 170))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(18 * scale)))
    d = ImageDraw.Draw(img)
    # placa preta com borda amarela
    d.rounded_rectangle([pad, pad, pad + W, pad + H], 48 * scale, fill=(12, 12, 12, 255), outline=YEL, width=int(12 * scale))
    # BLACK
    f1 = font(BLACK_IT, int(205 * scale))
    w, h, ox, oy = text_w(d, "BLACK", f1)
    x = pad + (W - w) / 2 - ox; y = pad + 62 * scale - oy
    d.text((x, y), "BLACK", font=f1, fill=(255, 255, 255, 255))
    # faixa amarela inclinada com FRIDAY
    band_h = int(150 * scale)
    band = Image.new("RGBA", (int(W * 0.94), band_h), YEL)
    bd = ImageDraw.Draw(band)
    f2 = font(BLACK_IT, int(128 * scale))
    w2, h2, ox2, oy2 = text_w(bd, "FRIDAY", f2)
    bd.text(((band.width - w2) / 2 - ox2, (band_h - h2) / 2 - oy2), "FRIDAY", font=f2, fill=(12, 12, 12, 255))
    band = band.rotate(-3, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(band, (int(pad + (W - band.width) / 2), int(pad + 300 * scale)))
    # selo 2026 vermelho
    d = ImageDraw.Draw(img)
    cx, cy, r = pad + W - 30 * scale, pad + 20 * scale, 78 * scale
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED, outline=(255, 255, 255, 255), width=int(8 * scale))
    f3 = font(BLACK, int(52 * scale))
    w3, h3, ox3, oy3 = text_w(d, "2026", f3)
    d.text((cx - w3 / 2 - ox3, cy - h3 / 2 - oy3), "2026", font=f3, fill=(255, 255, 255, 255))
    return img


big = badge(1.0)
big.save(f"{OUT}/bf_badge.png")
small = badge(0.36)
small.save(f"{OUT}/bf_badge_small.png")
print(big.size, small.size)
