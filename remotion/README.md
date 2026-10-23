# Projetos em Remotion

Vídeos editados com [Remotion](https://www.remotion.dev) (React + TypeScript).
Segue a skill `remotion-best-practices`, instalada em `../.claude/skills/`.

## Estrutura

```
src/
  Root.tsx                    registra as composições
  comum/estilo.ts             paleta, fontes, easings, pulso de câmera e tremor
  comum/componentes.tsx       cartão, pílula, selo com emoji, rolagem de números, faixa listrada
  sr-mantas-qm2/
    SrMantasQM2.tsx           vídeo base com correção de cor, câmera, cenas e flash
    cenas.tsx                 uma cena por fala, com gráficos e sons agrupados
scripts/preparar.py           monta public/ (vídeo, fontes, amostras das estampas, efeitos sonoros)
```

## Como usar

```bash
npm i
npm run preparar                 # gera public/ (precisa de Python, Pillow, numpy e FFmpeg)
npm run dev                      # Remotion Studio, para prévia interativa
npm run render:sr-mantas-qm2     # vídeo final em ../saida/
```

Quadros soltos para conferência:

```bash
npx remotion render SrMantasQM2 out/frames --frames=78,954,1536 --image-format=png
```

No ambiente de nuvem do Claude Code, acrescente
`--browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell`.

## Licença

A Remotion é gratuita para pessoas físicas e equipes de até 3 pessoas.
Empresas maiores precisam de licença: https://www.remotion.pro/license
