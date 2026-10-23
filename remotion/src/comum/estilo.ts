import { loadFont } from "@remotion/fonts";
import { Easing, interpolate, staticFile } from "remotion";

// Paleta tirada da própria manta, com dourado de destaque.
export const COR = {
  tinta: "#140d0a",
  painel: "rgba(20, 13, 10, 0.89)",
  ouro: "#ffc82e",
  ouroEscuro: "#be8014",
  creme: "#f8efe0",
  vermelho: "#c43440",
  caramelo: "#d6b086",
  marrom: "#502d1e",
};

const LISTRAS: [string, number][] = [
  [COR.vermelho, 44], [COR.creme, 6], [COR.marrom, 20], [COR.caramelo, 30], [COR.marrom, 8],
  [COR.creme, 5], [COR.vermelho, 16], [COR.tinta, 9], [COR.caramelo, 12], [COR.marrom, 14],
];

/** Faixa listrada no padrão da manta, como gradiente CSS repetido. */
export const LISTRAS_CSS = (() => {
  let x = 0;
  const paradas = LISTRAS.map(([cor, largura]) => {
    const trecho = `${cor} ${x}px ${x + largura}px`;
    x += largura;
    return trecho;
  });
  return `repeating-linear-gradient(90deg, ${paradas.join(", ")})`;
})();

export const FONTE_TITULO = '"Inter Display", "Noto Color Emoji", sans-serif';
export const FONTE_TEXTO = '"Inter", "Noto Color Emoji", sans-serif';

export const carregarFontes = () =>
  Promise.all([
    loadFont({ family: "Inter Display", url: staticFile("fonts/InterDisplay-Black.otf"), weight: "900" }),
    loadFont({ family: "Inter Display", url: staticFile("fonts/InterDisplay-ExtraBold.otf"), weight: "800" }),
    loadFont({ family: "Inter", url: staticFile("fonts/Inter-Bold.otf"), weight: "700" }),
  ]);

export const SOMBRA = "0 14px 40px rgba(0, 0, 0, 0.5)";
export const SOMBRA_FILTRO = "drop-shadow(0 4px 10px rgba(0, 0, 0, 0.7))";

export const SUAVE = Easing.bezier(0.16, 1, 0.3, 1);
export const ELASTICO = Easing.bezier(0.34, 1.56, 0.64, 1);
export const ACELERA = Easing.bezier(0.55, 0, 1, 0.45);
export const VAI_E_VOLTA = Easing.bezier(0.65, 0, 0.35, 1);

export const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** Progresso 0..1 entre dois tempos (em segundos) do quadro atual. */
export const progresso = (
  frame: number,
  fps: number,
  inicio: number,
  fim: number,
  easing: (x: number) => number = (x) => x,
) => interpolate(frame, [inicio * fps, fim * fps], [0, 1], { ...CLAMP, easing });

/** Pulso que sobe rápido até `pico` e relaxa: usado em zooms e flashes. */
export const pulso = (t: number, t0: number, pico: number, subida = 0.12, descida = 0.9) => {
  if (t < t0) return 0;
  if (t < t0 + subida) return pico * SUAVE((t - t0) / subida);
  return pico * (1 - VAI_E_VOLTA(Math.min(1, (t - t0 - subida) / descida)));
};

/** Deslocamento de câmera tremendo depois de um impacto. */
export const tremor = (t: number, t0: number, amplitude = 16, duracao = 0.45, freq = 17) => {
  if (t < t0 || t > t0 + duracao) return [0, 0];
  const a = amplitude * Math.exp((-7 * (t - t0)) / duracao);
  const w = 2 * Math.PI * freq * (t - t0);
  return [a * Math.sin(w), a * Math.cos(w * 1.31)];
};
