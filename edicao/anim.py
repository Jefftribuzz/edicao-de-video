"""Curvas de easing e utilitários de tempo para animação."""
import math


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def lerp(a, b, x):
    return a + (b - a) * x


def prog(t, ini, fim):
    """Progresso linear 0..1 de t entre ini e fim."""
    if fim <= ini:
        return 1.0 if t >= ini else 0.0
    return clamp((t - ini) / (fim - ini))


def out_cubic(x):
    return 1 - (1 - x) ** 3


def in_cubic(x):
    return x ** 3


def in_out_sine(x):
    return -(math.cos(math.pi * x) - 1) / 2


def in_out_cubic(x):
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def out_back(x, s=1.70158):
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def out_elastic(x):
    if x <= 0 or x >= 1:
        return clamp(x)
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi) / 3) + 1


def vida(t, ini, fim, d_in=0.35, d_out=0.22):
    """Envelope de entrada/saída de um elemento.

    Retorna None fora do intervalo, ou (escala, alpha, dy) para aplicar
    ao elemento: entra crescendo com overshoot e subindo, sai encolhendo.
    """
    if t < ini or t > fim:
        return None
    p_in = prog(t, ini, ini + d_in)
    p_out = in_cubic(prog(t, fim - d_out, fim))
    escala = lerp(0.82, 1.0, out_back(p_in)) * lerp(1.0, 0.9, p_out)
    alpha = out_cubic(prog(t, ini, ini + d_in * 0.6)) * (1 - p_out)
    dy = lerp(60, 0, out_cubic(p_in)) + lerp(0, -40, p_out)
    return escala, alpha, dy


def pulso(t, t0, pico=1.0, subida=0.12, descida=0.9):
    """Pulso suave: sobe rápido até `pico` em t0+subida e relaxa."""
    if t < t0:
        return 0.0
    if t < t0 + subida:
        return pico * out_cubic((t - t0) / subida)
    return pico * (1 - in_out_sine(prog(t, t0 + subida, t0 + subida + descida)))


def tremor(t, t0, amp=14.0, dur=0.45, freq=17.0):
    """Deslocamento (dx, dy) de câmera tremendo após um impacto."""
    if t < t0 or t > t0 + dur:
        return 0.0, 0.0
    k = math.exp(-7 * (t - t0) / dur * 1.0)
    a = amp * k
    w = 2 * math.pi * freq * (t - t0)
    return a * math.sin(w), a * math.cos(w * 1.31)
