"""Monta o vídeo final: legendas ASS + voz tratada + efeitos sonoros.

Uso: python3 final.py <work_dir> <saida.mp4> [musica.(mp3|wav)] [inicio_s] [volume_db]
A música (opcional) entra em loop se for curta, com fade de entrada/saída e
"ducking" automático: abaixa quando a voz fala e sobe nas pausas.
"""
import json, subprocess, sys

WORK, OUT = sys.argv[1], sys.argv[2]
MUSIC = sys.argv[3] if len(sys.argv) > 3 else None
M_START = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
M_DB = float(sys.argv[5]) if len(sys.argv) > 5 else -12.0
DUR = 62.96
sfx = json.load(open(f"{WORK}/sfx.json"))

inputs = ["-i", f"{WORK}/fx.mp4", "-i", f"{WORK}/base.mov"]
files = sorted({n for n, _, _ in sfx})
for n in files:
    inputs += ["-i", f"{WORK}/sfx/{n}.wav"]
idx = {n: 2 + i for i, n in enumerate(files)}
if MUSIC:
    inputs += ["-stream_loop", "-1", "-ss", str(M_START), "-i", MUSIC]
    m_idx = 2 + len(files)

fc = []
fc.append("[0:v]subtitles=captions.ass:fontsdir=/usr/share/fonts/opentype/inter[v]")
fc.append("[1:a]aresample=48000,highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=3dB,"
          "equalizer=f=3000:t=q:w=1:g=2[voice0]")
if MUSIC:
    fc.append("[voice0]asplit=2[voice][vkey]")
    fc.append(f"[{m_idx}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{DUR},asetpts=PTS-STARTPTS,"
              f"volume={M_DB}dB,afade=t=in:d=0.6,afade=t=out:st={DUR - 2.5}:d=2.5[mus0]")
    fc.append("[mus0][vkey]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=450:makeup=1[mus]")
else:
    fc.append("[voice0]anull[voice]")
# divide cada arquivo de efeito pelo número de usos
uses = {n: [(t, v) for m, t, v in sfx if m == n] for n in files}
labels = []
for n in files:
    k = len(uses[n])
    outs = "".join(f"[{n}{j}]" for j in range(k))
    fc.append(f"[{idx[n]}:a]asplit={k}{outs}" if k > 1 else f"[{idx[n]}:a]anull{outs}")
    for j, (t, v) in enumerate(uses[n]):
        ms = int(t * 1000)
        fc.append(f"[{n}{j}]volume={v * 0.55 * 0.7:.3f},adelay={ms}|{ms}[s_{n}{j}]")
        labels.append(f"[s_{n}{j}]")
fc.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest[fxmix]")
mix_in = "[voice][fxmix][mus]" if MUSIC else "[voice][fxmix]"
fc.append(f"{mix_in}amix=inputs={3 if MUSIC else 2}:normalize=0:duration=first,"
          "loudnorm=I=-14:TP=-1.0:LRA=11,aresample=48000[a]")

cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc),
       "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-b:v", "6M", "-maxrate", "8M", "-bufsize", "12M",
       "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "30",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT]
subprocess.run(cmd, check=True, cwd=WORK)
print("ok", OUT)
