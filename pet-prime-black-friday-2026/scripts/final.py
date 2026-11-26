"""Monta o vídeo final: legendas ASS + voz tratada + efeitos sonoros.

Uso: python3 final.py <work_dir> <saida.mp4>
"""
import json, subprocess, sys

WORK, OUT = sys.argv[1], sys.argv[2]
sfx = json.load(open(f"{WORK}/sfx.json"))

inputs = ["-i", f"{WORK}/fx.mp4", "-i", f"{WORK}/base.mov"]
files = sorted({n for n, _, _ in sfx})
for n in files:
    inputs += ["-i", f"{WORK}/sfx/{n}.wav"]
idx = {n: 2 + i for i, n in enumerate(files)}

fc = []
fc.append("[0:v]subtitles=captions.ass:fontsdir=/usr/share/fonts/opentype/inter[v]")
fc.append("[1:a]aresample=48000,highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=3dB,"
          "equalizer=f=3000:t=q:w=1:g=2[voice]")
# divide cada arquivo de efeito pelo número de usos
uses = {n: [(t, v) for m, t, v in sfx if m == n] for n in files}
labels = []
for n in files:
    k = len(uses[n])
    outs = "".join(f"[{n}{j}]" for j in range(k))
    fc.append(f"[{idx[n]}:a]asplit={k}{outs}" if k > 1 else f"[{idx[n]}:a]anull{outs}")
    for j, (t, v) in enumerate(uses[n]):
        ms = int(t * 1000)
        fc.append(f"[{n}{j}]volume={v * 0.55:.3f},adelay={ms}|{ms}[s_{n}{j}]")
        labels.append(f"[s_{n}{j}]")
fc.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest[fxmix]")
fc.append("[voice][fxmix]amix=inputs=2:normalize=0:duration=first,"
          "loudnorm=I=-14:TP=-1.0:LRA=11,aresample=48000[a]")

cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc),
       "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-b:v", "6M", "-maxrate", "8M", "-bufsize", "12M",
       "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "30",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT]
subprocess.run(cmd, check=True, cwd=WORK)
print("ok", OUT)
