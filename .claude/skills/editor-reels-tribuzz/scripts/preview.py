"""Folha de conferência: quadros pequenos do vídeo nos tempos pedidos, com o tempo escrito.

Uso: python3 preview.py <video.mp4> <saida.png> 1.2 3.5 9.0 ...  [--orig base.mov]
Com --orig, monta duas linhas (original em cima, editado embaixo) para comparar cores.
Quadros de 240 px de largura: o suficiente para conferir layout gastando pouco contexto.
"""
import os, subprocess, sys, tempfile

a = sys.argv[1:]
orig = None
if "--orig" in a:
    k = a.index("--orig"); orig = a[k + 1]; del a[k:k + 2]
video, out, times = a[0], a[1], a[2:]
tmp = tempfile.mkdtemp()
font = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"

files = []
for tag, src in ([("o", orig)] if orig else []) + [("e", video)]:
    for i, t in enumerate(times):
        f = f"{tmp}/{tag}{i:02d}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", t, "-i", src, "-frames:v", "1", "-vf",
                        f"scale=240:426,drawtext=fontfile={font}:text='{t}':x=5:y=400:fontsize=20:fontcolor=white:box=1:boxcolor=black", f],
                       check=True)
        files.append(f)
cols = len(times) if len(times) <= 9 else 9
subprocess.run(["montage", *files, "-tile", f"{cols}x", "-geometry", "+2+2", out], check=True)
print(out)
