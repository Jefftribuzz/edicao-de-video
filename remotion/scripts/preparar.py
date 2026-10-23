"""Prepara a pasta public/ do projeto Remotion.

- copia o vídeo original (raiz do repositório) para public/
- copia as fontes Inter do sistema
- recorta as amostras reais das estampas de um quadro do vídeo
- sintetiza os efeitos sonoros com o módulo edicao.sfx

Uso, a partir de remotion/:  python3 scripts/preparar.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

REMOTION = Path(__file__).resolve().parents[1]
RAIZ = REMOTION.parent
PUBLIC = REMOTION / "public"
sys.path.insert(0, str(RAIZ))

from PIL import Image  # noqa: E402

from edicao import sfx  # noqa: E402

VIDEO = RAIZ / "SR Mantas Quarto de Milha 2.mp4"
FONTES = ["InterDisplay-Black.otf", "InterDisplay-ExtraBold.otf", "Inter-Bold.otf"]
# Recortes (x0, y0, lado) das mantas que aparecem no quadro de 10 s.
RECORTES_ESTAMPAS = [(120, 1240, 440), (850, 1090, 300), (830, 1430, 250), (1170, 1990, 230)]


def copiar_video():
    # cópia (não link): o bundle da Remotion copia public/ para outra pasta
    destino = PUBLIC / "sr-mantas-qm2.mp4"
    if destino.is_symlink() or destino.exists():
        destino.unlink()
    shutil.copy(VIDEO, destino)


def copiar_fontes():
    (PUBLIC / "fonts").mkdir(parents=True, exist_ok=True)
    for nome in FONTES:
        shutil.copy(Path("/usr/share/fonts/opentype/inter") / nome, PUBLIC / "fonts" / nome)


def recortar_estampas():
    pasta = PUBLIC / "estampas"
    pasta.mkdir(parents=True, exist_ok=True)
    quadro = pasta / "_quadro.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "10", "-i", str(VIDEO), "-frames:v", "1", str(quadro)],
                   check=True)
    img = Image.open(quadro).convert("RGB")
    for i, (x, y, lado) in enumerate(RECORTES_ESTAMPAS, 1):
        img.crop((x, y, x + lado, y + lado)).resize((460, 460), Image.LANCZOS).save(pasta / f"estampa-{i}.jpg",
                                                                                     quality=92)
    quadro.unlink()


def gerar_sfx():
    pasta = PUBLIC / "sfx"
    pasta.mkdir(parents=True, exist_ok=True)
    sons = {
        "whoosh": sfx.whoosh(),
        "whoosh-curto": sfx.whoosh(0.28),
        "pop": sfx.pop(),
        "tick": sfx.tick(),
        "ding": sfx.ding(),
        "impacto": sfx.impacto(),
        "riser": sfx.riser(0.85),
        "brilho": sfx.brilho(),
        **{f"pop-{i}": sfx.pop(760 + 90 * i, 240) for i in range(4)},
    }
    for nome, som in sons.items():
        sfx.mixar([(0, som, 0, 0)], len(som) / sfx.SR, pasta / f"{nome}.wav")


if __name__ == "__main__":
    copiar_video()
    copiar_fontes()
    recortar_estampas()
    gerar_sfx()
    print("public/ pronto")
