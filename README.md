# Edição de Vídeo

Edição de vídeos por código: gráficos animados, textos, ícones, setas,
contadores, punch-ins de câmera e efeitos sonoros, tudo sincronizado com a fala.

## Estrutura

```
edicao/                 motor reutilizável
  anim.py               curvas de easing, envelopes de entrada/saída, pulsos e tremor
  gfx.py                primitivas gráficas (texto, emoji, formas, sombras, setas, brilho)
  sfx.py                efeitos sonoros sintetizados e mixagem
  render.py             pipeline FFmpeg → Python (quadro a quadro) → FFmpeg
projetos/
  sr_mantas_qm2/        "SR Mantas Quarto de Milha 2"
    editar.py           linha do tempo da edição
    roteiro.md          fala com minutagem e o que entra em cada trecho
saida/                  vídeos renderizados
```

## Requisitos

- FFmpeg (com libx264)
- Python 3.10+ com `pip install -r requirements.txt`
- Fontes Inter e Noto Color Emoji (caminhos em `edicao/gfx.py`)

## Como renderizar

A partir da raiz do repositório:

```bash
# vídeo final em saida/
python3 -m projetos.sr_mantas_qm2.editar

# quadros de prévia em tempos específicos (segundos)
python3 -m projetos.sr_mantas_qm2.editar --previa 1.3 15.9 25.6

# rascunho com codificação rápida
python3 -m projetos.sr_mantas_qm2.editar --rapido
```

## Novo projeto

Copie `projetos/sr_mantas_qm2/` e ajuste em `editar.py`: o vídeo de entrada,
a lista `ELEMENTOS` (uma função por cena, que recebe o quadro e o tempo), os
`PUNCH_INS` da câmera e as entradas da trilha de efeitos sonoros.
