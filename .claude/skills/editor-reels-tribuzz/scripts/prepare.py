"""Etapa 1: baixa o vídeo, gera a cópia de trabalho e transcreve com tempo por palavra.

Uso:
  python3 prepare.py --work <pasta> (--drive <link ou id> | --src <arquivo>) [--model medium]
                     [--prompt "vocabulário: nomes de produtos, marca..."]

Gera em <pasta>:
  src.mp4        original baixado (se --drive)
  base.mov       1080x1920, 30 fps (corta/ajusta para 9:16 se precisar)
  audio16k.wav   áudio para a transcrição
  transcript.json  saída do Whisper (com palavras)
  words.txt      transcrição compacta: uma linha por frase, cada palavra com o início em segundos
Imprime só um resumo curto (duração, cortes de cena, words.txt) para economizar contexto.
"""
import argparse, json, os, re, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument("--work", required=True)
ap.add_argument("--drive")
ap.add_argument("--src")
ap.add_argument("--model", default="medium")
ap.add_argument("--prompt", default="")
a = ap.parse_args()
os.makedirs(a.work, exist_ok=True)
W = lambda f: os.path.join(a.work, f)


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


src = a.src
if a.drive:
    m = re.search(r"/d/([\w-]+)|id=([\w-]+)", a.drive)
    fid = (m.group(1) or m.group(2)) if m else a.drive
    src = W("src.mp4")
    if not os.path.exists(src):
        r = subprocess.run(["curl", "-sSL", "-o", src, "-w", "%{http_code} %{content_type}",
                            f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t"],
                           capture_output=True, text=True)
        if r.returncode or "text/html" in r.stdout:
            os.remove(src) if os.path.exists(src) else None
            sys.exit(f"Falha ao baixar do Drive ({r.stdout} {r.stderr.strip()[-200:]}). "
                     "Peça para compartilhar como 'Qualquer pessoa com o link' ou libere drive.usercontent.google.com na rede.")

info = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
                       "-of", "json", src]).stdout)
v = next(s for s in info["streams"] if s["codec_type"] == "video")
dur = float(info["format"]["duration"])
print(f"origem: {v['width']}x{v['height']} {v['r_frame_rate']} fps, {dur:.2f}s")

if not os.path.exists(W("base.mov")):
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf",
         "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,fps=30",
         "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-pix_fmt", "yuv420p",
         "-c:a", "pcm_s16le", "-ar", "48000", W("base.mov")])
if not os.path.exists(W("audio16k.wav")):
    run(["ffmpeg", "-v", "error", "-y", "-i", W("base.mov"), "-ac", "1", "-ar", "16000", W("audio16k.wav")])

# cortes de cena e pausas (úteis para flashes/transições)
sc = subprocess.run(["ffmpeg", "-hide_banner", "-i", W("base.mov"), "-vf", "scale=270:480,select='gt(scene,0.3)',showinfo",
                     "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
cuts = [round(float(x), 2) for x in re.findall(r"pts_time:([\d.]+)", sc)]
print("cortes de cena:", cuts)

if not os.path.exists(W("transcript.json")):
    try:
        import whisper  # noqa
    except ImportError:
        print("instalando openai-whisper (o torch vem do PyPI; download.pytorch.org costuma estar bloqueado)...", flush=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "openai-whisper"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import whisper
    import contextlib, io
    with contextlib.redirect_stderr(io.StringIO()):  # esconde barras de progresso
        model = whisper.load_model(a.model)
        r = model.transcribe(W("audio16k.wav"), language="pt", word_timestamps=True,
                             initial_prompt=a.prompt or None, verbose=None)
    json.dump(r, open(W("transcript.json"), "w"), ensure_ascii=False)
r = json.load(open(W("transcript.json")))
lines = []
for s in r["segments"]:
    lines.append(f"[{s['start']:.2f}-{s['end']:.2f}] " + " ".join(f"{w['word'].strip()}@{w['start']:.2f}" for w in s["words"]))
open(W("words.txt"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
