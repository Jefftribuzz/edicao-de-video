"""Edição: "SR Mantas Quarto de Milha 2" (vertical 1440x2560, 60 fps, 26 s).

Acrescenta ao vídeo (que já vem com legenda) gráficos animados
sincronizados com a fala, punch-ins de câmera e efeitos sonoros.
A minutagem de cada fala está em roteiro.md.

Uso (a partir da raiz do repositório):
    python3 -m projetos.sr_mantas_qm2.editar                    # vídeo final
    python3 -m projetos.sr_mantas_qm2.editar --previa 1 3.2 15.6 --pasta /tmp/previas
"""
import argparse
import math
import tempfile
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

from edicao import anim as a
from edicao import gfx as g
from edicao import sfx
from edicao.render import extrair_quadro, processar_quadro, renderizar

RAIZ = Path(__file__).resolve().parents[2]
ENTRADA = RAIZ / "SR Mantas Quarto de Milha 2.mp4"
SAIDA = RAIZ / "saida" / "SR Mantas Quarto de Milha 2 - Editado.mp4"

W, H = 1440, 2560
CENTRO_ZOOM = (720, 1150)
FILTRO_COR = ("eq=contrast=1.06:saturation=1.10,"
              "colorbalance=rs=0.02:bs=-0.02:rm=0.02:bm=-0.02,vignette=angle=0.5")

# Paleta tirada da própria manta.
TINTA = (20, 13, 10)
PAINEL = (20, 13, 10, 226)
OURO = (255, 200, 46)
OURO_ESC = (190, 128, 20)
CREME = (248, 239, 224)
VERMELHO = (196, 52, 64)
CARAMELO = (214, 176, 134)
MARROM = (80, 45, 30)
LISTRAS = [(VERMELHO, 44), (CREME, 6), (MARROM, 20), (CARAMELO, 30), (MARROM, 8), (CREME, 5),
           (VERMELHO, 16), (TINTA, 9), (CARAMELO, 12), (MARROM, 14)]


# ======================================================== peças reutilizáveis

@lru_cache(maxsize=None)
def fundo_card(w, h, r=34):
    """Painel escuro com barra dourada à esquerda e faixa listrada da manta."""
    painel = g.ret_arredondado(w, h, r, PAINEL).copy()
    mascara = g.ret_arredondado(w, h, r, (255, 255, 255, 255)).getchannel("A")
    deco = g.nova(w, h)
    deco.paste(Image.new("RGBA", (14, h), (*OURO, 255)), (0, 0))
    deco.paste(g.faixa_listrada(w, 12, LISTRAS), (0, h - 12))
    painel.alpha_composite(g.recortar_com_mascara(deco, mascara))
    return g.sombra(painel, 26, 0.55, 14)


def card(f, t, ini, fim, w, h, cx, cy, conteudo, d_in=0.35, d_out=0.22):
    v = a.vida(t, ini, fim, d_in, d_out)
    if not v:
        return
    s, alpha, dy = v
    base, m = fundo_card(w, h)
    img = base.copy()
    conteudo(img, m, t)
    g.colocar(f, img, cx, cy + dy, s=s, a=alpha)


@lru_cache(maxsize=None)
def pilula(txt, tam, fundo=OURO, cor=TINTA, nome="black", padx=36, tracking=2):
    h = int(tam * 1.6)
    w = g.texto(txt, nome, tam, cor, tracking).width + 2 * padx
    img = g.ret_arredondado(w, h, h // 2, fundo).copy()
    g.colocar_texto_caps(img, txt, nome, tam, cor, w / 2, h / 2, ax=0.5, tracking=tracking)
    return g.com_sombra(img, 18, 0.5, 8)


@lru_cache(maxsize=None)
def selo_emoji(ch, d=170, tam=None, fundo=OURO, borda=0, cor_borda=None):
    img = g.circulo(d, fundo, borda, cor_borda).copy()
    g.colocar(img, g.emoji(ch, tam or int(d * 0.64)), d / 2, d / 2)
    return g.com_sombra(img, 16, 0.45, 8)


def texto_trocando(img, antigo, novo, p, nome, tam, cor, x, y, ax=0.0, desloc=46):
    """Troca de texto: o antigo sobe sumindo, o novo sobe entrando."""
    e = a.out_cubic(p)
    if antigo and e < 1:
        g.colocar_texto_caps(img, antigo, nome, tam, cor, x, y - desloc * e, ax=ax, a=1 - e)
    g.colocar_texto_caps(img, novo, nome, tam, cor, x, y + desloc * (1 - e), ax=ax, a=e)


def revelar(img_txt, p):
    """Corta o sprite da esquerda para a direita (efeito de wipe)."""
    if p >= 1:
        return img_txt
    return img_txt.crop((0, 0, max(1, int(img_txt.width * p)), img_txt.height))


def numeral_rolando(caixa, antigo, novo, p, tam, cor):
    w, h = caixa.size
    e = a.in_out_cubic(p)
    if antigo is not None and e < 1:
        g.colocar_texto_caps(caixa, antigo, "black", tam, cor, w / 2, h / 2 - h * e, ax=0.5)
    g.colocar_texto_caps(caixa, novo, "black", tam, cor, w / 2, h / 2 + h * (1 - e), ax=0.5)


# ======================================================== elementos por cena

def el_tamanho(f, t):
    """0.7–2.1 s  "Olha o tamanho": cota de medida atravessando a manta."""
    ini, fim = 0.70, 2.10
    if not ini <= t <= fim:
        return
    y, xc, meia_max = 1440, 720, 600
    sai = a.in_cubic(a.prog(t, fim - 0.2, fim))
    p = a.out_cubic(a.prog(t, 0.72, 1.08))
    meia = meia_max * p
    tela = g.Tela(W, 240, ss=2)
    yy = 120
    if meia > 4:
        tela.linha([(xc - meia, yy), (xc + meia, yy)], OURO, 11)
        g.ponta_seta(tela, xc - meia - 6, yy, math.pi, 50, OURO)
        g.ponta_seta(tela, xc + meia + 6, yy, 0, 50, OURO)
    pt = a.out_back(a.prog(t, 1.02, 1.24))
    if pt > 0:
        for x in (xc - meia_max - 34, xc + meia_max + 34):
            tela.linha([(x, yy - 52 * pt), (x, yy + 52 * pt)], OURO, 9)
    g.colocar(f, g.com_sombra(tela.final(), 10, 0.7, 4), xc, y, a=1 - sai)
    pp = a.prog(t, 0.80, 1.10)
    g.colocar(f, pilula("TAMANHO", 70), xc, y - 120, s=a.lerp(0.6, 1, a.out_back(pp)),
              a=a.out_cubic(pp) * (1 - sai))


def el_grossura(f, t):
    """2.2–4.1 s  "e a grossura": anel destacando a espessura do forro."""
    ini, fim = 2.22, 4.10
    if not ini <= t <= fim:
        return
    sai = a.in_cubic(a.prog(t, fim - 0.2, fim))
    x0, y0, w, h = 800, 600, 640, 1330
    cx, cy, rx, ry = 1120 - x0, 1355 - y0, 280, 520
    tela = g.Tela(w, h, ss=2)
    p = a.in_out_cubic(a.prog(t, 2.25, 2.75))
    tela.arco(cx, cy, rx, ry, -90, -90 + 360 * p, OURO, 12)
    pc = a.out_cubic(a.prog(t, 2.55, 2.75))
    if pc > 0:  # conector do rótulo até o anel
        tela.linha([(cx, 112), (cx, 112 + (cy - ry - 112) * pc)], OURO, 7)
    g.colocar(f, g.com_sombra(tela.final(), 10, 0.7, 4), x0 + w / 2, y0 + h / 2, a=1 - sai)
    pp = a.prog(t, 2.36, 2.66)
    g.colocar(f, pilula("GROSSURA", 66), 1120, y0 + 60, s=a.lerp(0.6, 1, a.out_back(pp)),
              a=a.out_cubic(pp) * (1 - sai))


def el_quarto_de_milha(f, t):
    """4.25–6.95 s  "Você que tem quarto de milha e participa"."""
    w, h = 1200, 250

    def conteudo(img, m, t):
        ps = a.prog(t, 4.35, 4.65)
        g.colocar(img, selo_emoji("🐎"), m + 40 + 85, m + h / 2 - 4, s=a.lerp(0.3, 1, a.out_back(ps)),
                  a=a.out_cubic(ps))
        x = m + 255
        g.colocar_texto_caps(img, "VOCÊ QUE TEM", "bold", 44, OURO, x, m + 70, tracking=5)
        tam = g.tam_que_cabe("QUARTO DE MILHA", "black", 100, w - 255 - 50)
        pr = a.out_cubic(a.prog(t, 5.42, 5.75))
        if pr > 0:
            spr = revelar(g.texto("QUARTO DE MILHA", "black", tam, CREME), pr)
            topo = m + 158 - g.ALTURA_CAPS * tam / 2 - g.topo_caps("black", tam)
            g.colocar(img, spr, x, topo, ax=0, ay=0)

    card(f, t, 4.25, 6.95, w, h, 720, 300, conteudo)


MODALIDADES = [
    (7.55, "01", "PROVAS", "TRÊS TAMBORES", "🏇"),
    (8.70, "02", "PROVAS", "RANCH SORTING", "🐄"),
    (9.45, "03", "PROVAS", "TEAM PENNING", "🤠"),
    (10.20, "+", "E AINDA", "VÁRIAS MODALIDADES", "🏆"),
]


def el_modalidades(f, t):
    """7.4–11.75 s  lista contada das provas."""
    w, h = 1240, 270
    larg_txt = w - 270 - 150

    def conteudo(img, m, t):
        k = max(0, max(i for i, it in enumerate(MODALIDADES) if t >= it[0] or i == 0))
        _, num, kicker, item, ico = MODALIDADES[k]
        p = 1.0 if k == 0 else a.prog(t, MODALIDADES[k][0], MODALIDADES[k][0] + 0.28)
        ant = MODALIDADES[k - 1] if k > 0 else None

        caixa = g.ret_arredondado(200, 200, 30, OURO).copy()
        numeral_rolando(caixa, ant[1] if ant else None, num, p, 128, TINTA)
        g.colocar(img, caixa, m + 32, m + 35, ax=0, ay=0)

        x = m + 270
        g.colocar_texto_caps(img, kicker, "bold", 44, OURO, x, m + 62, tracking=5)
        tam = min(g.tam_que_cabe(it[3], "black", 92, larg_txt) for it in MODALIDADES)
        texto_trocando(img, ant[3] if ant else None, item, p, "black", tam, CREME, x, m + 150)

        pe = a.out_back(a.prog(t, MODALIDADES[k][0], MODALIDADES[k][0] + 0.32)) if k else 1.0
        g.colocar(img, g.emoji(ico, 104), m + w - 88, m + h / 2 - 8, s=max(0.01, pe))

        for i in range(len(MODALIDADES)):
            ativo = i <= k
            g.colocar(img, g.circulo(18, OURO if ativo else (*CREME, 90)), x + 9 + i * 36, m + 224)

    card(f, t, 7.38, 11.75, w, h, 720, 310, conteudo)


def batimento(t):
    fase = (t * 1.3) % 1.0
    return 1 + 0.12 * math.exp(-((fase - 0.08) / 0.05) ** 2) + 0.07 * math.exp(-((fase - 0.26) / 0.05) ** 2)


def el_respeito(f, t):
    """11.8–14.5 s  "e tem respeito pelo seu cavalo, pelo seu quarto de milha"."""
    w, h = 1200, 290

    def conteudo(img, m, t):
        ps = a.prog(t, 11.9, 12.2)
        g.colocar(img, selo_emoji("❤️"), m + 40 + 85, m + h / 2 - 4,
                  s=a.lerp(0.3, 1, a.out_back(ps)) * batimento(t), a=a.out_cubic(ps))
        x = m + 255
        g.colocar_texto_caps(img, "RESPEITO PELO SEU", "bold", 44, OURO, x, m + 60, tracking=5)
        tam = g.tam_que_cabe("QUARTO DE MILHA", "black", 84, w - 255 - 60)
        if t < 13.70:
            g.colocar_texto_caps(img, "CAVALO", "black", tam, CREME, x, m + 134)
        else:
            texto_trocando(img, "CAVALO", "QUARTO DE MILHA", a.prog(t, 13.70, 13.98), "black", tam, CREME,
                           x, m + 134)
        x1, yb = m + 1010, m + 206
        g.colocar(img, g.ret_arredondado(x1 - x, 30, 15, (*CREME, 60)), x, yb, ax=0, ay=0)
        pb = a.in_out_cubic(a.prog(t, 12.15, 13.45))
        if pb > 0.02:
            g.colocar(img, g.ret_arredondado(max(30, int((x1 - x) * pb)), 30, 15, OURO), x, yb, ax=0, ay=0)
        g.colocar_texto_caps(img, f"{round(100 * pb)}%", "black", 50, CREME, x1 + 26, yb + 15)

    card(f, t, 11.80, 14.50, w, h, 720, 320, conteudo)


@lru_cache(maxsize=None)
def medalha_base(d=330):
    tela = g.Tela(d, d)
    r = d / 2
    tela.elipse(r, r, r, r, cor=OURO_ESC)
    passos = 24
    for i in range(passos):  # degradê radial
        k = i / (passos - 1)
        cor = tuple(int(a.lerp(c0, c1, k)) for c0, c1 in zip((236, 168, 30), (255, 226, 120)))
        rr = (r - 14) * (1 - k * 0.92)
        tela.elipse(r - 6 * k, r - 8 * k, rr, rr, cor=cor)
    tela.elipse(r, r, r - 26, r - 26, borda=(*CREME, 170), larg=4)
    img = tela.final()
    g.colocar_texto_caps(img, "Nº", "black", 50, TINTA, r, r - 92, ax=0.5)
    return g.sombra(img, 22, 0.55, 12)


@lru_cache(maxsize=None)
def raios(d=820, n=14):
    tela = g.Tela(d, d, ss=2)
    r = d / 2
    for i in range(n):
        a0 = 2 * math.pi * i / n
        a1 = a0 + math.pi / n
        tela.poligono([(r, r), (r + r * math.cos(a0), r + r * math.sin(a0)),
                       (r + r * math.cos(a1), r + r * math.sin(a1))], (*OURO, 95))
    img = tela.final().filter(ImageFilter.GaussianBlur(4))
    fade = g.circulo(d, (255, 255, 255, 255)).getchannel("A")
    radial = Image.radial_gradient("L").resize((d, d)).point(lambda v: max(0, 255 - int(v * 1.1)))
    return g.recortar_com_mascara(img, ImageChops.multiply(fade, radial))


def el_numero_um(f, t):
    """14.55–16.4 s  "a melhor manta do Brasil": medalha Nº1 com contagem regressiva."""
    ini, fim = 14.55, 16.40
    w, h = 1000, 250

    def conteudo(img, m, t):
        x = m + 50
        g.colocar_texto_caps(img, "A MELHOR MANTA", "bold", 46, OURO, x, m + 72, tracking=5)
        larg = g.colocar_texto_caps(img, "DO BRASIL", "black", 108, CREME, x, m + 162)
        pf = a.prog(t, 15.45, 15.75)
        g.colocar(img, g.emoji("🇧🇷", 96), x + larg + 66, m + 160, s=max(0.01, a.out_back(pf)))

    card(f, t, ini, fim, w, h, 560, 320, conteudo)

    v = a.vida(t, 14.68, fim, 0.4, 0.22)
    if not v:
        return
    s, alpha, dy = v
    cx, cy = 1185, 320 + dy
    impacto = t >= 15.50
    if impacto:
        pr = a.prog(t, 15.50, 15.75)
        rot = (t - 15.5) * 28
        g.colocar(f, raios(), cx, cy, s=a.lerp(0.4, 1, a.out_cubic(pr)) * s, a=a.out_cubic(pr) * alpha, rot=rot)
    base, m = medalha_base()
    img = base.copy()
    d = 330
    janela = g.nova(220, 170)
    passos, t0, dur = 8, 14.72, 0.76
    if t < t0:
        numeral_rolando(janela, None, "9", 1.0, 150, TINTA)
    else:
        i = min(passos - 1, int((t - t0) / (dur / passos)))
        p = a.prog(t - t0 - i * dur / passos, 0, dur / passos * 0.8)
        numeral_rolando(janela, str(9 - i), str(8 - i), p, 150, TINTA)
    g.colocar(img, janela, m + d / 2, m + d / 2 + 30)
    bump = 1 + 0.22 * (1 - a.out_elastic(a.prog(t, 15.50, 16.2))) if impacto else 1
    g.colocar(f, img, cx, cy, s=s * bump, a=alpha)


def el_fabricante(f, t):
    """16.45–17.7 s  "compra direto do fabricante": Fábrica → Você."""
    ini, fim = 16.43, 17.70
    if not ini <= t <= fim:
        return
    sai = a.in_cubic(a.prog(t, fim - 0.22, fim))
    y = 330
    for ch, rotulo, x, t0 in (("🏭", "FÁBRICA", 215, 16.45), ("🏠", "VOCÊ", 1225, 16.66)):
        p = a.prog(t, t0, t0 + 0.32)
        sp = a.lerp(0.3, 1, a.out_back(p))
        g.colocar(f, selo_emoji(ch, 200, 120, CREME, 9, OURO), x, y, s=sp, a=a.out_cubic(p) * (1 - sai))
        g.colocar(f, pilula(rotulo, 40, (*TINTA, 235), CREME, "bold", 26, 4), x, y + 150, s=sp,
                  a=a.out_cubic(p) * (1 - sai))
    x0, x1 = 340, 1100
    pa = a.in_out_cubic(a.prog(t, 16.55, 16.95))
    if pa > 0:
        tela = g.Tela(W, 140, ss=2)
        fim_x = x0 + (x1 - x0) * pa
        traco, vao = 40, 24
        off = (t * 260) % (traco + vao)
        xx = x0 - traco + off
        while xx < fim_x - 30:
            tela.linha([(max(x0, xx), 70), (min(fim_x - 30, xx + traco), 70)], OURO, 13)
            xx += traco + vao
        g.ponta_seta(tela, fim_x - 8, 70, 0, 54, OURO)
        g.colocar(f, g.com_sombra(tela.final(), 10, 0.6, 4), W / 2, y, a=1 - sai)
    pp = a.prog(t, 16.72, 17.02)
    g.colocar(f, pilula("DIRETO DO FABRICANTE", 50), 720, y - 135, s=a.lerp(0.6, 1, a.out_back(pp)),
              a=a.out_cubic(pp) * (1 - sai))


# Recortes (x0, y0, lado) das mantas que aparecem no quadro de 10 s.
RECORTES_ESTAMPAS = [(120, 1240, 440), (850, 1090, 300), (830, 1430, 250), (1170, 1990, 230)]


@lru_cache(maxsize=None)
def amostras_estampas(lado=230):
    quadro = extrair_quadro(ENTRADA, 10.0, FILTRO_COR).convert("RGBA")
    out = []
    for x, y, l in RECORTES_ESTAMPAS:
        sw = quadro.crop((x, y, x + l, y + l)).resize((lado, lado), Image.LANCZOS)
        sw = g.recortar_com_mascara(sw, g.ret_arredondado(lado, lado, 28, (255, 255, 255, 255)).getchannel("A"))
        moldura = g.ret_arredondado(lado + 16, lado + 16, 34, CREME).copy()
        moldura.alpha_composite(sw, (8, 8))
        out.append(g.com_sombra(moldura, 20, 0.55, 10))
    return out


def el_estampas(f, t):
    """17.8–19.95 s  "Várias estampas, vários modelos": amostras reais das mantas."""
    ini, fim = 17.80, 19.95
    if not ini <= t <= fim:
        return
    sai = a.in_cubic(a.prog(t, fim - 0.22, fim))
    rots = (-5, 3, -3, 5)
    for i, (img, x) in enumerate(zip(amostras_estampas(), (330, 590, 850, 1110))):
        p = a.prog(t, 17.85 + 0.12 * i, 17.85 + 0.12 * i + 0.35)
        boia = 7 * math.sin(2 * math.pi * 0.8 * t + i * 1.3)
        g.colocar(f, img, x, 300 + boia + a.lerp(80, 0, a.out_cubic(p)) - 40 * sai,
                  s=a.lerp(0.4, 1, a.out_back(p)) * (1 - 0.15 * sai), a=a.out_cubic(p) * (1 - sai),
                  rot=rots[i] * (1 - 0.4 * a.out_cubic(p)))
    txt = "VÁRIAS ESTAMPAS" if t < 18.80 else "VÁRIOS MODELOS"
    t_ref = 17.95 if t < 18.80 else 18.80
    pp = a.prog(t, t_ref, t_ref + 0.3)
    g.colocar(f, pilula(txt, 50), 720, 452, s=a.lerp(0.6, 1, a.out_back(pp)),
              a=(a.out_cubic(pp) if t < 18.80 else 1) * (1 - sai))


def marca_check(tela, cx, cy, d, p):
    pts = [(cx - d * 0.22, cy + d * 0.01), (cx - d * 0.06, cy + d * 0.17), (cx + d * 0.24, cy - d * 0.16)]
    if p > 0.02:
        tela.linha(g.polilinha_parcial(pts, p), TINTA, d * 0.12)


def el_ideal(f, t):
    """19.95–22.4 s  "ideal para o seu quarto de milha e respeito à sua montaria"."""
    w, h = 1240, 270
    linhas = [(20.00, "IDEAL PARA SEU QUARTO DE MILHA", 92), (21.60, "RESPEITO À SUA MONTARIA", 186)]
    tam = min(g.tam_que_cabe(txt, "extrabold", 64, w - 140 - 50) for _, txt, _ in linhas)

    def conteudo(img, m, t):
        for t0, txt, yc in linhas:
            p = a.prog(t, t0, t0 + 0.3)
            if p <= 0:
                continue
            d = 78
            tela = g.Tela(d, d)
            tela.elipse(d / 2, d / 2, d / 2, d / 2, cor=OURO)
            marca_check(tela, d / 2, d / 2, d, a.out_cubic(a.prog(t, t0 + 0.08, t0 + 0.3)))
            g.colocar(img, tela.final(), m + 62, m + yc, s=a.lerp(0.3, 1, a.out_back(p)))
            pt = a.out_cubic(a.prog(t, t0 + 0.05, t0 + 0.38))
            g.colocar_texto_caps(img, txt, "extrabold", tam, CREME, m + 125 - 30 * (1 - pt), m + yc, a=pt)

    card(f, t, 19.95, 22.40, w, h, 720, 315, conteudo)


def el_cta(f, t):
    """22.45–23.7 s  "Vem pra cá": cartão e setas pulsando para baixo."""
    ini, fim = 22.45, 23.70
    w, h = 880, 230

    def conteudo(img, m, t):
        tam = g.tam_que_cabe("VEM PRA CÁ!", "black", 128, w - 220)
        g.colocar_texto_caps(img, "VEM PRA CÁ!", "black", tam, CREME, m + 60, m + h / 2 - 4)
        g.colocar(img, g.emoji("👇", 104), m + w - 100, m + h / 2 + 8 * math.sin(2 * math.pi * 3 * t))

    card(f, t, ini, fim, w, h, 720, 300, conteudo)
    if not 22.55 <= t <= fim:
        return
    ent = a.out_cubic(a.prog(t, 22.55, 22.8)) * (1 - a.in_cubic(a.prog(t, fim - 0.2, fim)))
    tela = g.Tela(260, 330, ss=2)
    for i in range(3):
        brilho = max(0.0, math.sin(2 * math.pi * 2.2 * t - i * 0.9))
        cor = (*OURO, int(255 * (0.45 + 0.55 * brilho)))
        y = 60 + i * 90
        tela.linha([(50, y - 30), (130, y + 30), (210, y - 30)], cor, 22)
    g.colocar(f, g.com_sombra(tela.final(), 12, 0.6, 5), 720, 2215, a=ent)


@lru_cache(maxsize=None)
def gradiente_final():
    return g.gradiente_vertical(W, 620, (18, 11, 8), 0.0, 0.9, a.in_out_sine)


LOGO = "SR MANTAS"
LOGO_TAM, LOGO_TRACK, LOGO_Y = 190, 6, 2165


@lru_cache(maxsize=None)
def letra_logo(ch):
    return g.com_sombra(g.texto(ch, "black", LOGO_TAM, CREME), 16, 0.6, 8)


@lru_cache(maxsize=None)
def logo_inteiro():
    spr = g.texto(LOGO, "black", LOGO_TAM, CREME, LOGO_TRACK)
    return spr


def posicoes_logo():
    fnt = g.fonte("black", LOGO_TAM)
    total = g.largura_texto(LOGO, "black", LOGO_TAM, LOGO_TRACK)
    x = W / 2 - total / 2
    out = []
    for ch in LOGO:
        out.append((ch, x + fnt.getlength(ch) / 2))
        x += fnt.getlength(ch) + LOGO_TRACK
    return out, total


def el_final(f, t):
    """23.72 s–fim  "SR Mantas, a melhor do Brasil": assinatura da marca."""
    ini = 23.72
    if t < ini:
        return
    g.colocar(f, gradiente_final(), 0, H - 620, ax=0, ay=0, a=a.out_cubic(a.prog(t, ini, ini + 0.3)))
    posicoes, total = posicoes_logo()
    topo = LOGO_Y - g.ALTURA_CAPS * LOGO_TAM / 2 - g.topo_caps("black", LOGO_TAM)
    if t < 24.75:
        k = 0
        for i, (ch, xc) in enumerate(posicoes):
            if ch == " ":
                continue
            t0 = 23.78 + 0.05 * i if i < 2 else 24.22 + 0.045 * (k := k + 1)
            p = a.prog(t, t0, t0 + 0.28)
            spr = letra_logo(ch)
            g.colocar(f, spr, xc, topo + spr.height / 2 - 30 * (1 - a.out_cubic(p)) - 8,
                      s=a.lerp(1.8, 1, a.out_cubic(p)), a=a.out_cubic(p))
    else:
        logo = logo_inteiro()
        pb = a.prog(t, 25.35, 25.95)
        if 0 < pb < 1:
            logo = g.brilho_diagonal(logo, a.in_out_sine(pb))
        g.colocar(f, g.com_sombra(logo, 16, 0.6, 8), W / 2, topo + logo.height / 2, ax=0.5, ay=0.5)
    pf = a.out_cubic(a.prog(t, 24.35, 24.75))
    if pf > 0:
        faixa = g.faixa_listrada(int(total), 16, LISTRAS)
        corte = int(total * pf)
        faixa = faixa.crop((int(total / 2 - corte / 2), 0, int(total / 2 + corte / 2) + 1, 16))
        g.colocar(f, faixa, W / 2, LOGO_Y + 105)
    pt = a.prog(t, 24.75, 25.10)
    if pt > 0:
        tag = g.texto("A MELHOR DO BRASIL", "bold", 54, OURO, 9)
        alpha, dy = a.out_cubic(pt), 30 * (1 - a.out_cubic(pt))
        g.colocar(f, tag, W / 2 - 40, LOGO_Y + 185 + dy, a=alpha)
        pb = a.prog(t, 25.25, 25.55)
        g.colocar(f, g.emoji("🇧🇷", 66), W / 2 + tag.width / 2 + 10, LOGO_Y + 185 + dy,
                  s=max(0.01, a.out_back(pb)), a=alpha)


ELEMENTOS = [el_tamanho, el_grossura, el_quarto_de_milha, el_modalidades, el_respeito,
             el_numero_um, el_fabricante, el_estampas, el_ideal, el_cta, el_final]


def desenhar(f, t):
    for el in ELEMENTOS:
        el(f, t)


# ======================================================== câmera e flashes

PUNCH_INS = [(0.75, .06), (2.30, .06), (5.45, .05), (7.55, .035), (8.70, .035), (9.45, .035),
             (10.20, .035), (12.05, .05), (15.50, .10), (16.75, .05), (18.00, .04), (20.00, .035),
             (21.65, .05), (22.75, .07), (24.25, .09)]
IMPACTOS = [15.50, 24.25]


def camera(t):
    zoom = 1 + 0.03 * t / 26 + min(0.14, sum(a.pulso(t, t0, pico) for t0, pico in PUNCH_INS))
    dx = dy = 0.0
    for t0 in IMPACTOS:
        sx, sy = a.tremor(t, t0, 16)
        dx, dy = dx + sx, dy + sy
    flash = sum(a.pulso(t, t0, 0.32, 0.03, 0.22) for t0 in IMPACTOS) + a.pulso(t, 22.45, 0.15, 0.03, 0.2)
    return zoom, dx, dy, flash


# ======================================================== efeitos sonoros

def trilha_sfx(caminho, duracao):
    wh, wh_curto = sfx.whoosh(), sfx.whoosh(0.28)
    pp, tk, dg = sfx.pop(), sfx.tick(), sfx.ding()
    cues = [
        (0.66, wh, -20, 0), (0.80, pp, -18, 0),
        (2.20, wh, -20, 0.3), (2.38, pp, -18, 0.3),
        (4.22, wh, -20, 0), (4.38, pp, -19, -0.4), (5.42, wh_curto, -22, 0),
        (7.36, wh, -20, 0),
        (11.78, wh, -20, 0), (13.45, dg, -18, 0), (13.70, pp, -20, 0),
        (14.52, wh, -20, 0), (15.48, sfx.impacto(), -9, 0),
        (16.43, wh, -20, 0), (16.47, pp, -19, -0.6), (16.55, wh_curto, -22, 0), (16.66, pp, -19, 0.6),
        (16.72, pp, -18, 0),
        (17.78, wh, -20, 0), (18.80, pp, -18, 0),
        (19.93, wh, -20, 0), (20.00, dg, -18, -0.2), (21.60, dg, -18, 0.2),
        (22.43, wh, -19, 0), (22.50, pp, -18, 0),
        (22.88, sfx.riser(0.85), -18, 0), (23.74, wh, -19, 0), (24.22, sfx.impacto(), -8, 0),
        (25.35, sfx.brilho(), -18, 0),
    ]
    for t0, *_ in MODALIDADES:
        cues += [(t0, tk, -18, -0.3), (t0 + 0.03, pp, -20, 0.4)]
    cues += [(12.15 + i * 0.13, tk, -25, 0) for i in range(10)]
    cues += [(14.72 + i * 0.095, tk, -21, 0.4) for i in range(8)]
    cues += [(17.85 + 0.12 * i, sfx.pop(760 + 90 * i, 240), -19, -0.6 + 0.4 * i) for i in range(4)]
    sfx.mixar(cues, duracao, caminho)


# ======================================================== CLI

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--previa", type=float, nargs="*", help="tempos (s) para exportar quadros PNG")
    ap.add_argument("--pasta", type=Path, default=RAIZ / "saida" / "previas")
    ap.add_argument("--saida", type=Path, default=SAIDA)
    ap.add_argument("--rapido", action="store_true", help="codificação rápida (rascunho)")
    args = ap.parse_args()

    if args.previa:
        args.pasta.mkdir(parents=True, exist_ok=True)
        for t in args.previa:
            img = processar_quadro(extrair_quadro(ENTRADA, t, FILTRO_COR), t, camera, desenhar, CENTRO_ZOOM)
            destino = args.pasta / f"previa_{t:06.2f}.png"
            img.save(destino)
            print(destino)
        return

    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "sfx.wav"
        trilha_sfx(wav, 26.3)
        renderizar(ENTRADA, args.saida, camera, desenhar, FILTRO_COR, wav, CENTRO_ZOOM,
                   preset="veryfast" if args.rapido else "medium")
    print(args.saida)


if __name__ == "__main__":
    main()
