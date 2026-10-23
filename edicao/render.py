"""Pipeline de renderização: decodifica com FFmpeg, processa quadro a quadro
em Python (câmera + gráficos) e recodifica mixando o áudio original com os
efeitos sonoros."""
import json
import subprocess
import sys
import time

from PIL import Image


def info(video):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,r_frame_rate,nb_frames:format=duration", "-of", "json", str(video)],
        check=True, capture_output=True, text=True).stdout
    d = json.loads(out)
    s = d["streams"][0]
    num, den = map(int, s["r_frame_rate"].split("/"))
    return {"w": s["width"], "h": s["height"], "fps": num / den,
            "duracao": float(d["format"]["duration"]), "quadros": int(s.get("nb_frames", 0))}


def extrair_quadro(video, t, filtro=None):
    vf = ["-vf", filtro] if filtro else []
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(video), *vf, "-frames:v", "1",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], check=True, capture_output=True).stdout
    i = info(video)
    return Image.frombytes("RGB", (i["w"], i["h"]), out)


def aplicar_camera(img, zoom, dx, dy, centro):
    """Zoom em torno de `centro` com deslocamento (dx, dy) em pixels."""
    if zoom <= 1.0005 and abs(dx) < 0.3 and abs(dy) < 0.3:
        return img
    w, h = img.size
    zoom = max(zoom, 1.0 + (2 * max(abs(dx), abs(dy)) + 2) / min(w, h))  # margem para o tremor
    cw, ch = w / zoom, h / zoom
    cx, cy = centro
    x0 = min(max(cx - cx / zoom + dx, 0), w - cw)
    y0 = min(max(cy - cy / zoom + dy, 0), h - ch)
    return img.resize((w, h), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))


def processar_quadro(img, t, camera, desenhar, centro):
    zoom, dx, dy, flash = camera(t)
    img = aplicar_camera(img, zoom, dx, dy, centro).convert("RGBA")
    desenhar(img, t)
    img = img.convert("RGB")
    if flash > 0.003:
        img = Image.blend(img, Image.new("RGB", img.size, (255, 250, 240)), min(flash, 1.0))
    return img


def renderizar(entrada, saida, camera, desenhar, filtro_cor, trilha_sfx, centro, crf=18,
               preset="medium", ganho_sfx_db=0.0, bitrate_max="16M"):
    i = info(entrada)
    w, h, fps = i["w"], i["h"], i["fps"]
    total = i["quadros"] or int(i["duracao"] * fps)
    dec = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", str(entrada), "-vf", filtro_cor,
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    filtro_audio = (f"[2:a]volume={ganho_sfx_db}dB[s];"
                    "[1:a][s]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.94:level=disabled[a]")
    enc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
         "-r", f"{fps}", "-i", "-", "-i", str(entrada), "-i", str(trilha_sfx),
         "-filter_complex", filtro_audio, "-map", "0:v", "-map", "[a]",
         "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p",
         "-maxrate", bitrate_max, "-bufsize", "32M",
         "-profile:v", "high", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
         "-shortest", str(saida)], stdin=subprocess.PIPE)
    tamanho = w * h * 3
    n, t0 = 0, time.time()
    while True:
        buf = dec.stdout.read(tamanho)
        if len(buf) < tamanho:
            break
        img = processar_quadro(Image.frombytes("RGB", (w, h), buf), n / fps, camera, desenhar, centro)
        enc.stdin.write(img.tobytes())
        n += 1
        if n % 60 == 0:
            vel = n / (time.time() - t0)
            sys.stderr.write(f"\r  quadro {n}/{total}  ({vel:.1f} q/s)")
            sys.stderr.flush()
    enc.stdin.close()
    enc.wait()
    dec.wait()
    sys.stderr.write(f"\r  {n} quadros em {time.time() - t0:.0f}s{' ' * 20}\n")
    if enc.returncode != 0:
        raise RuntimeError("falha na codificação do vídeo")
