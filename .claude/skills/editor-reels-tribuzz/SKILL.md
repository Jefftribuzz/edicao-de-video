---
name: editor-reels-tribuzz
description: Edita vídeos verticais de anúncio (Reels, Stories, TikTok, Meta Ads) de clientes da Tribuzz a partir de um link do Google Drive. Gera legenda animada em todo o vídeo, destaques de frases no centro com fundo desfocado, selo de campanha (Black Friday, Dia das Mães, Natal, etc.), cartão de preço e desconto, listas de cores/itens, adesivos, botão "chama no Zap", efeitos visuais e sonoros e música de fundo com ducking. Use sempre que pedirem para editar, legendar ou "deixar pronto pra anúncio" um vídeo de vendedor/loja/cliente, destacar oferta, preço ou desconto em vídeo, colocar efeitos ou música num vídeo de anúncio, ou ajustar uma edição feita antes (volume dos efeitos, cores, textos), mesmo que a palavra "skill" ou "Reels" não apareça.
---

# Editor de Reels Tribuzz

O trabalho já está todo em scripts. A edição é **preencher um `projeto.json`**, sem escrever código e sem calcular segundos à mão. Os tempos são frases da transcrição ("desconto de r$ 250"), e o `make.py` encontra os segundos sozinho.

`SKILL_DIR` = pasta deste arquivo. Scripts em `SKILL_DIR/scripts/`, exemplo completo e aprovado em `SKILL_DIR/assets/exemplo-projeto.json` (anúncio Pet Prime Black Friday 2026). Leia o exemplo antes de montar um projeto novo, porque ele mostra todos os campos.

## Fluxo (4 passos)

**1. Preparar** (baixa, converte para 1080x1920 30 fps e transcreve):
```bash
python3 SKILL_DIR/scripts/prepare.py --work /tmp/<cliente>-work --drive "<link do Drive>" \
  --prompt "Nome da loja, produtos, cores e termos técnicos citados no vídeo"
```
Imprime os cortes de cena e a transcrição compacta (`palavra@segundos`). O `--prompt` com vocabulário do nicho melhora muito o texto. Use o modelo `medium`, que dá o tempo por palavra mais preciso. O `large-v3` acerta mais o texto, mas erra o tempo; só vale para tirar dúvida de uma palavra.

**2. Montar o `projeto.json`** em `/tmp/<cliente>-work/`, copiando a estrutura do exemplo:
- `fixes`: corrija erros da transcrição ("acentuaino book" → "assento em nobuck"). Chaves com várias palavras funcionam. **Pergunte ao usuário a grafia de nomes de cores, modelos e marcas que soarem estranhos** (ex.: "marrom eber" era "Marrom Heber"). Pergunte antes de renderizar, não depois.
- `highlights`: as frases que o cliente pediu para destacar. `{palavra}` fica em amarelo e `\\N` quebra a linha. Use 2 a 3 linhas curtas.
- `badge`, `price`, `lists`, `stickers`, `cta`: selo, preço, listas laterais, adesivos e botão final.
- Extras opcionais: `slow_zooms`, `zooms`, `flashes` (use os cortes de cena), `shakes`, `sfx` (`[nome, tempo, volume]`), `no_captions`.
- Sons disponíveis: whoosh, pop, impact, cash, sparkle, riser, swish, ding.

Confira os tempos sem renderizar: `python3 SKILL_DIR/scripts/make.py projeto.json --no-render`. Ele lista os destaques com início e fim. Se uma frase não for achada, o erro mostra a transcrição corrigida para você ajustar o texto.

**3. Renderizar** (cerca de 3 min para 60 s de vídeo):
```bash
python3 SKILL_DIR/scripts/make.py /tmp/<cliente>-work/projeto.json
```
Quando a mudança for só de áudio, legenda ou texto de destaque, use `--skip-fx`, que reaproveita os efeitos visuais e leva cerca de 1 min. Mudanças em overlays, zoom, flash ou cor exigem apagar o `fx.mp4` ou rodar sem `--skip-fx`.

**4. Conferir e entregar:**
```bash
python3 SKILL_DIR/scripts/preview.py <saida.mp4> /tmp/<cliente>-work/sheet.png 1.2 3.5 9 ...
```
Escolha um tempo dentro de cada destaque, cartão e lista, e leia **uma** folha (quadros de 240 px custam pouco contexto). Para comparar a cor com o original, use `--orig /tmp/<cliente>-work/base.mov`.
Para entregar: copie o MP4 para a pasta do cliente no repositório, faça commit e push na branch da sessão e envie com `SendUserFile` (display `attach`). O conector do Drive não sobe arquivos desse tamanho, então diga que o upload no Drive é manual.

## Preferências já aprovadas pelo cliente (padrão da skill)

Cada item abaixo veio de uma correção do usuário. Mantenha esses padrões, a menos que ele peça diferente:
- **Cor do produto natural.** Nada de filtro de cor, saturação, luzes coloridas ou flash branco sobre o produto, porque o cliente compra pela cor que vê. `color_fx` fica vazio e `stars` fica `false`.
- **Efeitos sonoros baixos.** `sfx_gain` 0.19. O cliente pediu duas vezes para baixar, porque os efeitos competiam com a voz. Se pedirem para baixar mais, reduza o `sfx_gain` e rode com `--skip-fx`.
- **Nunca calcule nem escreva preço final** (ex.: 1.899 − 250). Mostre só os valores falados no vídeo, como o preço cheio e o desconto. O cliente vetou o valor calculado.
- **Legenda:** Inter Black 86, palavra falada em amarelo, no máximo cerca de 17 caracteres por bloco, escondida durante destaques e cartões de preço.
- **Saída:** 1080x1920, 30 fps, H.264 a 6 Mbps (cerca de 45 MB/min), áudio a -14 LUFS. Abaixo de 100 MB cabe no GitHub.
- **Música de fundo:** só instrumental, a -13 dB, com ducking (abaixa sozinha sob a voz) e fade no início e no fim. Escolha o trecho com mais energia começando num tempo forte. Configure em `music.start` (segundos dentro da faixa).

## Música com IA (licença)

- Para anúncio pago, sugira gerar no **Suno com plano pago** (Pro/Premier, que dá direito comercial), no modo Instrumental. Exemplo de estilo: `sertanejo universitário, instrumental, upbeat, happy, acoustic guitar, viola caipira, accordion, 125 bpm`.
- Link do Suno de música **privada não baixa**: a API devolve "forbidden". Peça para baixar o MP3/WAV no Suno e mandar pelo Drive.
- O MusicGen (Meta) tem licença **não comercial**. Use só para prévia, nunca para o anúncio.

## Ambiente e rede

- O ambiente de nuvem **edicao-de-video** já libera `drive.google.com`, `drive.usercontent.google.com`, `openaipublic.azureedge.net` (modelos Whisper), `suno.com` e `cdn1.suno.ai`. Se a sessão estiver em outro ambiente e o download der `403 CONNECT`, proponha mudar para ele com `switch_environment`.
- Baixar vídeo pelo conector do Google Drive não funciona para arquivos grandes (vem em base64). Use o `prepare.py`, que baixa por curl.
- O `prepare.py` instala o Whisper se faltar. O torch vem do PyPI, porque `download.pytorch.org` costuma estar bloqueado. A instalação leva alguns minutos e o modelo medium tem 1,4 GB.
- Fontes Inter, ffmpeg (com libass), ImageMagick, numpy e Pillow já vêm na imagem.

## Para gastar menos tokens

- Não leia os scripts, só o exemplo e este arquivo. Os scripts têm `--help` nas docstrings, se precisar.
- Não leia saídas longas: o `prepare.py` e o `make.py` já imprimem só o resumo.
- Faça uma folha de preview por rodada, só nos momentos que mudaram.
- Em pedidos de ajuste, edite o `projeto.json` e renderize de novo, sem refazer o fluxo inteiro. Ajustes comuns:

| Pedido | O que mudar |
|---|---|
| efeitos sonoros altos/baixos | `sfx_gain` (+ `--skip-fx`) |
| música alta/baixa ou outro trecho | `music.db` / `music.start` (+ `--skip-fx`) |
| tirar um efeito visual | remova de `zooms`/`flashes`/`shakes` ou da lista correspondente |
| palavra errada na legenda | `fixes` (+ `--skip-fx`) |
| trocar texto de destaque | `highlights[].text` (+ `--skip-fx`; a posição do blur depende só do tempo) |
| campanha diferente | `badge.top` / `badge.band` / `badge.tag` (ex.: "DIA DAS", "MÃES", "") |
