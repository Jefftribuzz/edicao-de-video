"""Gera cartões, etiquetas e adesivos (PNG transparente) para a edição."""
import json, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = sys.argv[1]
CFG = json.load(open(sys.argv[2]))
FB = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FBI = "/usr/share/fonts/opentype/inter/Inter-BlackItalic.otf"
FX = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
YEL = (255, 212, 0, 255); RED = (226, 28, 44, 255); WHITE = (255, 255, 255, 255)
INK = (14, 14, 14, 255); GREEN = (37, 190, 90, 255)


def F(p, s):
    return ImageFont.truetype(p, s)


def bbox(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[2] - b[0], b[3] - b[1], b[0], b[1]


def shadowed(im, blur=14, off=10, a=150):
    pad = blur * 3
    out = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    alpha = im.split()[3].point(lambda v: v * a // 255)
    sh.paste((0, 0, 0, 255), (pad, pad + off), alpha)
    out = Image.alpha_composite(out, sh.filter(ImageFilter.GaussianBlur(blur)))
    out.alpha_composite(im, (pad, pad))
    return out


def pill(text, bg, fg, size=46, font=FB, icon=None, pad_x=34, h=None, radius=None, outline=None):
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    f = F(font, size)
    tw, th, ox, oy = bbox(tmp, text, f)
    h = h or int(size * 1.9)
    icon_w = int(h * 0.62) + 18 if icon else 0
    w = tw + pad_x * 2 + icon_w
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius or h // 2, fill=bg,
                        outline=outline, width=5 if outline else 0)
    x = pad_x
    if icon:
        icon(d, x, h, im)
        x += icon_w
    d.text((x - ox, (h - th) / 2 - oy), text, font=f, fill=fg)
    return shadowed(im)


def swatch_icon(color):
    def draw(d, x, h, im):
        r = int(h * 0.31)
        cy = h // 2
        d.ellipse([x, cy - r, x + 2 * r, cy + r], fill=color, outline=(255, 255, 255, 255), width=4)
    return draw


def check_icon(d, x, h, im):
    r = int(h * 0.31); cy = h // 2
    d.ellipse([x, cy - r, x + 2 * r, cy + r], fill=YEL)
    s = r / 20
    pts = [(x + r - 10 * s, cy + 0 * s), (x + r - 3 * s, cy + 8 * s), (x + r + 11 * s, cy - 8 * s)]
    d.line(pts, fill=INK, width=max(3, int(5 * s)), joint="curve")


def gift_icon(d, x, h, im):
    r = int(h * 0.31); cy = h // 2
    d.rounded_rectangle([x, cy - r + 6, x + 2 * r, cy + r], 6, fill=WHITE)
    d.rectangle([x + r - 5, cy - r + 6, x + r + 5, cy + r], fill=RED)
    d.rectangle([x - 4, cy - r + 2, x + 2 * r + 4, cy - r + 16], fill=WHITE)
    d.ellipse([x + r - 18, cy - r - 12, x + r - 2, cy - r + 6], outline=WHITE, width=5)
    d.ellipse([x + r + 2, cy - r - 12, x + r + 18, cy - r + 6], outline=WHITE, width=5)


def truck_icon(d, x, h, im):
    r = int(h * 0.31); cy = h // 2
    d.rectangle([x, cy - r + 4, x + int(1.25 * r), cy + r - 10], fill=INK)
    d.polygon([(x + int(1.3 * r), cy - r + 14), (x + int(1.75 * r), cy - r + 14), (x + 2 * r + 2, cy), (x + 2 * r + 2, cy + r - 10), (x + int(1.3 * r), cy + r - 10)], fill=INK)
    for cx in (x + int(0.45 * r), x + int(1.6 * r)):
        d.ellipse([cx - 9, cy + r - 20, cx + 9, cy + r - 2], fill=INK, outline=YEL, width=3)


def clock_icon(d, x, h, im):
    r = int(h * 0.31); cy = h // 2; cx = x + r
    d.ellipse([x, cy - r, x + 2 * r, cy + r], outline=WHITE, width=6)
    d.line([(cx, cy), (cx, cy - r + 10)], fill=WHITE, width=6)
    d.line([(cx, cy), (cx + r - 12, cy)], fill=WHITE, width=6)


def chat_icon(d, x, h, im):
    r = int(h * 0.33); cy = h // 2; cx = x + r
    d.ellipse([x, cy - r, x + 2 * r, cy + r], outline=WHITE, width=6)
    d.polygon([(x + 4, cy + r + 4), (x + 10, cy + r - 22), (x + 28, cy + r - 6)], fill=WHITE)
    for dx in (-13, 0, 13):
        d.ellipse([cx + dx - 5, cy - 5, cx + dx + 5, cy + 5], fill=WHITE)


ICONS = dict(check=check_icon, gift=gift_icon, truck=truck_icon, clock=clock_icon, chat=chat_icon)
STY = dict(
    yellow=(YEL, INK), red=(RED, WHITE), white=((255, 255, 255, 240), INK),
    dark=((15, 15, 15, 225), WHITE), green=(GREEN, WHITE),
)


def price_card(old, new=None, off=None, label="A SELA CUSTA"):
    W, H = 860, 470 if new else 300
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, W - 1, H - 1], 40, fill=(12, 12, 12, 238), outline=YEL, width=10)
    if not new:
        f1 = F(FX, 54); f2 = F(FBI, 150)
        s1 = label; w1, h1, ox, oy = bbox(d, s1, f1)
        d.text(((W - w1) / 2 - ox, 40 - oy), s1, font=f1, fill=(230, 230, 230, 255))
        s2 = f"R$ {old}"; w2, h2, ox, oy = bbox(d, s2, f2)
        d.text(((W - w2) / 2 - ox, 115 - oy), s2, font=f2, fill=WHITE)
        return shadowed(im, 20, 14, 170)
    # Sem preço final: mostra o preço cheio e o valor do desconto.
    f1 = F(FX, 56); f2 = F(FBI, 168); f3 = F(FB, 58)
    s1 = f"{label} R$ {old}"; w1, h1, ox, oy = bbox(d, s1, f1)
    d.text(((W - w1) / 2 - ox, 44 - oy), s1, font=f1, fill=(225, 225, 225, 255))
    s3 = "GANHE"; w3, h3, ox, oy = bbox(d, s3, f3)
    d.text(((W - w3) / 2 - ox, 135 - oy), s3, font=f3, fill=WHITE)
    s2 = f"R$ {new}"; w2, h2, ox, oy = bbox(d, s2, f2)
    d.text(((W - w2) / 2 - ox, 205 - oy), s2, font=f2, fill=YEL)
    s4 = "DE DESCONTO"; w4, h4, ox, oy = bbox(d, s4, f3)
    d.text(((W - w4) / 2 - ox, 385 - oy), s4, font=f3, fill=YEL)
    card = shadowed(im, 20, 14, 170)
    if off:
        st = Image.new("RGBA", (330, 330), (0, 0, 0, 0))
        sd = ImageDraw.Draw(st)
        sd.ellipse([10, 10, 320, 320], fill=RED, outline=WHITE, width=10)
        fa = F(FB, 50); fb = F(FBI, 92)
        for s, f, y in (("-R$", fa, 95), (off, fb, 150)):
            w, h, ox, oy = bbox(sd, s, f)
            sd.text(((330 - w) / 2 - ox, y - oy), s, font=f, fill=WHITE)
        w, h, ox, oy = bbox(sd, "OFF", fa)
        sd.text(((330 - w) / 2 - ox, 250 - oy), "OFF", font=fa, fill=WHITE)
        st = st.rotate(14, expand=True, resample=Image.BICUBIC)
        st = shadowed(st, 12, 8, 140)
        big = Image.new("RGBA", (card.width + st.width // 3, card.height + st.height // 3), (0, 0, 0, 0))
        big.alpha_composite(card, (0, 0))
        big.alpha_composite(st, (big.width - st.width, big.height - st.height))
        card = big
    return card


for item in CFG["pills"]:
    bg, fg = STY[item["style"]]
    icon = ICONS.get(item.get("icon")) if item.get("icon") else None
    if item.get("swatch"):
        icon = swatch_icon(tuple(item["swatch"]) + (255,))
    im = pill(item["text"], bg, fg, size=item.get("size", 46), icon=icon,
              outline=WHITE if item.get("outline") else None)
    im.save(f"{OUT}/{item['file']}")

p = CFG.get("price")
if p:
    lb = p.get("label", "A SELA CUSTA")
    price_card(p["old"], label=lb).save(f"{OUT}/price_old.png")
    price_card(p["old"], p["discount"], p["discount"], label=lb).save(f"{OUT}/price_new.png")
print("ok")
