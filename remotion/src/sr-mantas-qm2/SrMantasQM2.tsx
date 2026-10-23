import { colorCorrection } from "@remotion/effects/color-correction";
import { vignette } from "@remotion/effects/vignette";
import { Video } from "@remotion/media";
import React from "react";
import { AbsoluteFill, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { carregarFontes, pulso, tremor } from "../comum/estilo";
import {
  Assinatura,
  CENAS,
  Cta,
  Estampas,
  Fabricante,
  Grossura,
  Ideal,
  Modalidades,
  NumeroUm,
  QuartoDeMilha,
  Respeito,
  Tamanho,
} from "./cenas";

carregarFontes();

// Punch-ins de câmera nas palavras de ênfase: [segundo, intensidade].
const PUNCH_INS: [number, number][] = [
  [0.75, 0.06], [2.3, 0.06], [5.45, 0.05], [7.55, 0.035], [8.7, 0.035], [9.45, 0.035], [10.2, 0.035],
  [12.05, 0.05], [15.5, 0.1], [16.75, 0.05], [18.0, 0.04], [20.0, 0.035], [21.65, 0.05], [22.75, 0.07],
  [24.25, 0.09],
];
const IMPACTOS = [15.5, 24.25];

/** Zoom lento contínuo + punch-ins + tremor nos impactos. */
const Camera: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const t = frame / fps;
  const punch = Math.min(0.14, PUNCH_INS.reduce((soma, [t0, pico]) => soma + pulso(t, t0, pico), 0));
  const [dx, dy] = IMPACTOS.map((t0) => tremor(t, t0)).reduce(([ax, ay], [bx, by]) => [ax + bx, ay + by], [0, 0]);
  return (
    <AbsoluteFill
      style={{
        transformOrigin: "720px 1150px",
        scale: 1.004 + (0.03 * frame) / durationInFrames + punch,
        translate: `${dx}px ${dy}px`,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

const Flash: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const intensidade = IMPACTOS.reduce((s, t0) => s + pulso(t, t0, 0.32, 0.03, 0.22), 0) + pulso(t, 22.45, 0.15, 0.03, 0.2);
  return <AbsoluteFill style={{ backgroundColor: "#fffaf0", opacity: Math.min(1, intensidade) }} />;
};

export const SrMantasQM2: React.FC = () => {
  const { fps } = useVideoConfig();
  const cena = (c: keyof typeof CENAS) => ({
    from: Math.round(CENAS[c].inicio * fps),
    durationInFrames: Math.round((CENAS[c].fim - CENAS[c].inicio) * fps),
  });
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <Camera>
        <Video
          name="Vídeo original"
          src={staticFile("sr-mantas-qm2.mp4")}
          effects={[
            colorCorrection({ temperature: 0.06, contrast: 1.06, saturation: 1.02, vibrance: 0.04, highlights: -0.06 }),
            vignette({ amount: 0.35, radius: 0.7, feather: 0.45 }),
          ]}
        />
      </Camera>
      <Sequence name="Tamanho" {...cena("tamanho")}>
        <Tamanho />
      </Sequence>
      <Sequence name="Grossura" {...cena("grossura")}>
        <Grossura />
      </Sequence>
      <Sequence name="Quarto de milha" {...cena("quartoDeMilha")}>
        <QuartoDeMilha />
      </Sequence>
      <Sequence name="Modalidades" {...cena("modalidades")}>
        <Modalidades />
      </Sequence>
      <Sequence name="Respeito" {...cena("respeito")}>
        <Respeito />
      </Sequence>
      <Sequence name="Nº 1 do Brasil" {...cena("numeroUm")}>
        <NumeroUm />
      </Sequence>
      <Sequence name="Direto do fabricante" {...cena("fabricante")}>
        <Fabricante />
      </Sequence>
      <Sequence name="Estampas" {...cena("estampas")}>
        <Estampas />
      </Sequence>
      <Sequence name="Ideal" {...cena("ideal")}>
        <Ideal />
      </Sequence>
      <Sequence name="Vem pra cá" {...cena("cta")}>
        <Cta />
      </Sequence>
      <Sequence name="Assinatura" {...cena("assinatura")}>
        <Assinatura />
      </Sequence>
      <Flash />
    </AbsoluteFill>
  );
};
