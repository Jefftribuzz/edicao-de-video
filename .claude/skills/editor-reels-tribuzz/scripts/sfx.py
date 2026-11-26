"""Sintetiza efeitos sonoros (WAV 48 kHz estéreo) para a edição."""
import sys, wave
import numpy as np

SR = 48000
rng = np.random.default_rng(7)
OUT = sys.argv[1]


def save(name, x, pan=0.0):
    x = np.asarray(x, dtype=np.float64)
    peak = np.max(np.abs(x)) or 1.0
    x = x / peak * 0.9
    l = x * (1 - max(pan, 0)); r = x * (1 + min(pan, 0))
    st = np.stack([l, r], 1)
    st = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    with wave.open(f"{OUT}/{name}.wav", "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(st.tobytes())


def t(d):
    return np.arange(int(SR * d)) / SR


def onepole_lp(x, fc):
    """Low-pass de um polo com corte variável (fc pode ser array)."""
    fc = np.broadcast_to(fc, x.shape)
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x); s = 0.0
    for i in range(len(x)):
        s = (1 - a[i]) * x[i] + a[i] * s
        y[i] = s
    return y


def env_adsr(n, a, r):
    e = np.ones(n)
    na = max(1, int(a * SR)); e[:na] = np.linspace(0, 1, na)
    e[na:] = np.exp(-np.arange(n - na) / (r * SR))
    return e


# Whoosh: ruído com corte subindo e descendo
d = 0.55; tt = t(d); n = len(tt)
noise = rng.standard_normal(n)
fc = 300 + 5000 * np.sin(np.pi * tt / d) ** 2
w = onepole_lp(noise, fc) - onepole_lp(noise, fc * 0.25)
w *= np.sin(np.pi * tt / d) ** 1.5
save("whoosh", w)

# Pop: seno com pitch caindo
d = 0.18; tt = t(d)
f = 900 * np.exp(-tt * 25) + 250
ph = 2 * np.pi * np.cumsum(f) / SR
save("pop", np.sin(ph) * np.exp(-tt * 28))

# Impacto / boom grave para preço e desconto
d = 1.4; tt = t(d)
f = 140 * np.exp(-tt * 6) + 42
ph = 2 * np.pi * np.cumsum(f) / SR
sub = np.sin(ph) * np.exp(-tt * 3.2)
crack = onepole_lp(rng.standard_normal(len(tt)), 2500) * np.exp(-tt * 30)
save("impact", sub + 0.6 * crack)

# Cha-ching (caixa registradora): clique metálico + dois sinos
d = 1.2; tt = t(d)
click = onepole_lp(rng.standard_normal(len(tt)), 6000) * np.exp(-tt * 80)
bell = np.zeros_like(tt)
for start, base in ((0.08, 2093), (0.2, 2637)):
    m = tt >= start; tb = tt[m] - start
    tone = sum(np.sin(2 * np.pi * base * k * tb) / k for k in (1, 2.76, 5.4))
    bell[m] += tone * np.exp(-tb * 5)
save("cash", 0.8 * click + bell)

# Brilho mágico (cores): arpejo rápido de sinos agudos
d = 1.3; tt = t(d); sh = np.zeros_like(tt)
notes = [1568, 1976, 2349, 2794, 3136, 3951, 4699]
for i, f0 in enumerate(notes):
    st = i * 0.07; m = tt >= st; tb = tt[m] - st
    sh[m] += (np.sin(2 * np.pi * f0 * tb) + 0.3 * np.sin(2 * np.pi * f0 * 2.01 * tb)) * np.exp(-tb * 6)
sh += 0.15 * onepole_lp(rng.standard_normal(len(tt)), 9000) * np.exp(-tt * 3)
save("sparkle", sh)

# Riser curto (tensão antes do "mas... na Black Friday")
d = 1.6; tt = t(d)
f = 200 * (1 + 8 * (tt / d) ** 2)
ph = 2 * np.pi * np.cumsum(f) / SR
r = (np.sin(ph) * 0.4 + onepole_lp(rng.standard_normal(len(tt)), 800 + 7000 * tt / d) * 1.2)
r *= (tt / d) ** 2
save("riser", r)

# Swoosh curto de transição (tick)
d = 0.25; tt = t(d)
x = rng.standard_normal(len(tt))
x = x - onepole_lp(x, 3000)
save("swish", x * np.sin(np.pi * tt / d) ** 3)

# Ding de notificação (WhatsApp/Zap) – dois tons
d = 0.7; tt = t(d); x = np.zeros_like(tt)
for st, f0 in ((0, 1318), (0.12, 1760)):
    m = tt >= st; tb = tt[m] - st
    x[m] += np.sin(2 * np.pi * f0 * tb) * np.exp(-tb * 9)
save("ding", x)

# Batida de música de fundo simples (loop de 4 tempos, 120 BPM) – trilha leve
bpm = 120; beat = 60 / bpm; d = beat * 16; tt = t(d); bed = np.zeros_like(tt)
for b in range(16):
    s0 = int(b * beat * SR)
    k = t(0.35); kick = np.sin(2 * np.pi * np.cumsum(55 + 120 * np.exp(-k * 30)) / SR) * np.exp(-k * 9)
    if b % 2 == 0:
        bed[s0:s0 + len(k)] += kick[: len(bed) - s0]
    h = t(0.06); hat = (rng.standard_normal(len(h)) - 0) * np.exp(-h * 70)
    hs = int((b * beat + beat / 2) * SR)
    hat = hat - onepole_lp(hat, 6000)
    bed[hs:hs + len(h)] += 0.35 * hat[: max(0, len(bed) - hs)]
    if b % 4 == 2:
        c = t(0.2); clap = onepole_lp(rng.standard_normal(len(c)), 3000) * np.exp(-c * 25)
        bed[s0:s0 + len(c)] += 0.5 * clap[: len(bed) - s0]
save("beat", bed)
print("ok")
