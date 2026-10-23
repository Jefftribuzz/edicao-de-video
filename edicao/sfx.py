"""Efeitos sonoros sintetizados (sem arquivos externos) e mixagem em trilha WAV."""
import math
import wave

import numpy as np

SR = 44100
_rng = np.random.default_rng(7)


def _t(dur):
    return np.arange(int(dur * SR)) / SR


def _passa_baixa(x, corte):
    """Filtro passa-baixa de um polo; `corte` pode variar por amostra (Hz)."""
    corte = np.broadcast_to(np.asarray(corte, dtype=np.float64), x.shape)
    k = 1 - np.exp(-2 * np.pi * corte / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += k[i] * (x[i] - acc)
        y[i] = acc
    return y


def _norm(x, pico=0.9):
    m = np.max(np.abs(x)) or 1.0
    return x / m * pico


def whoosh(dur=0.42):
    t = _t(dur)
    p = t / dur
    ruido = _rng.standard_normal(len(t))
    corte = 300 + 5200 * np.sin(np.pi * p) ** 2
    som = _passa_baixa(ruido, corte) - _passa_baixa(ruido, corte * 0.25)
    env = np.sin(np.pi * p ** 0.7) ** 2
    return _norm(som * env)


def pop(f0=820, f1=260, dur=0.11):
    t = _t(dur)
    f = f1 + (f0 - f1) * np.exp(-t * 38)
    fase = 2 * np.pi * np.cumsum(f) / SR
    som = np.sin(fase) * np.exp(-t * 30)
    clique = _rng.standard_normal(len(t)) * np.exp(-t * 900) * 0.4
    return _norm(som + clique)


def tick(f=2100, dur=0.045):
    t = _t(dur)
    som = np.sin(2 * np.pi * f * t) * np.exp(-t * 140)
    som += _rng.standard_normal(len(t)) * np.exp(-t * 600) * 0.3
    return _norm(som, 0.8)


def ding(f0=1318.5, dur=1.1):
    t = _t(dur)
    som = sum(a * np.sin(2 * np.pi * f0 * m * t) * np.exp(-t * d)
              for m, a, d in ((1, 1.0, 4.5), (2.0, 0.35, 7), (2.76, 0.25, 9), (5.4, 0.12, 14)))
    ataque = np.clip(t / 0.004, 0, 1)
    return _norm(som * ataque, 0.85)


def impacto(dur=1.0):
    t = _t(dur)
    f = 42 + 70 * np.exp(-t * 9)
    corpo = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.2)
    ruido = _passa_baixa(_rng.standard_normal(len(t)), 1800) * np.exp(-t * 22) * 2.5
    return _norm(np.tanh((corpo + ruido) * 1.6))


def riser(dur=0.9):
    t = _t(dur)
    p = t / dur
    ruido = _rng.standard_normal(len(t))
    corte = 400 + 7000 * p ** 2
    som = _passa_baixa(ruido, corte) - _passa_baixa(ruido, corte * 0.3)
    tom = np.sin(2 * np.pi * np.cumsum(220 + 900 * p ** 2) / SR) * 0.25
    env = p ** 2.2 * np.clip((1 - p) / 0.03, 0, 1)
    return _norm((som + tom) * env)


def brilho(dur=0.7):
    """Cintilar agudo (sparkle) para o brilho passando no logo."""
    t = _t(dur)
    som = np.zeros_like(t)
    for i, f in enumerate((2637, 3136, 3951, 4699)):
        t0 = i * 0.06
        tt = np.clip(t - t0, 0, None)
        som += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 9) * (t >= t0)
    return _norm(som, 0.7)


def mixar(cues, duracao, caminho):
    """Mixa a lista de (tempo, som, ganho_db, pan) numa trilha WAV estéreo."""
    n = int(duracao * SR) + SR
    trilha = np.zeros((n, 2))
    for tempo, som, ganho_db, pan in cues:
        i = int(tempo * SR)
        g = 10 ** (ganho_db / 20)
        fim = min(n, i + len(som))
        trecho = som[: fim - i] * g
        ang = (pan + 1) * math.pi / 4
        trilha[i:fim, 0] += trecho * math.cos(ang)
        trilha[i:fim, 1] += trecho * math.sin(ang)
    trilha = trilha[: int(duracao * SR)]
    dados = (np.clip(trilha, -1, 1) * 32767).astype("<i2")
    with wave.open(str(caminho), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(dados.tobytes())
