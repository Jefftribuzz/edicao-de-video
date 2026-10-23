import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import {
  ACELERA,
  CLAMP,
  COR,
  ELASTICO,
  FONTE_TEXTO,
  FONTE_TITULO,
  LISTRAS_CSS,
  SOMBRA,
  SUAVE,
} from "./estilo";

/**
 * Cartão escuro com barra dourada e faixa listrada da manta.
 * Entra crescendo e subindo; sai encolhendo nos últimos 0,22 s da `duracao`.
 * Os filhos usam coordenadas internas do cartão.
 */
export const Cartao: React.FC<{
  largura: number;
  altura: number;
  cx: number;
  cy: number;
  duracao: number;
  children: React.ReactNode;
}> = ({ largura, altura, cx, cy, duracao, children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const entra = interpolate(frame, [0, 0.35 * fps], [0, 1], { ...CLAMP, easing: SUAVE });
  const sai = interpolate(frame, [(duracao - 0.22) * fps, duracao * fps], [0, 1], { ...CLAMP, easing: ACELERA });
  return (
    <div
      style={{
        position: "absolute",
        left: cx - largura / 2,
        top: cy - altura / 2,
        width: largura,
        height: altura,
        borderRadius: 34,
        overflow: "hidden",
        background: COR.painel,
        boxShadow: SOMBRA,
        opacity: interpolate(frame, [0, 0.2 * fps], [0, 1], CLAMP) * (1 - sai),
        scale: interpolate(frame, [0, 0.35 * fps], [0.82, 1], { ...CLAMP, easing: ELASTICO }) * (1 - 0.1 * sai),
        translate: `0px ${60 * (1 - entra) - 40 * sai}px`,
      }}
    >
      <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: 14, background: COR.ouro }} />
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 12, background: LISTRAS_CSS }} />
      {children}
    </div>
  );
};

/** Texto pequeno em dourado, espaçado, acima do título do cartão. */
export const Chamada: React.FC<{ x: number; y: number; children: React.ReactNode }> = ({ x, y, children }) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      fontFamily: FONTE_TEXTO,
      fontWeight: 700,
      fontSize: 44,
      letterSpacing: 5,
      color: COR.ouro,
      lineHeight: 1,
      whiteSpace: "nowrap",
    }}
  >
    {children}
  </div>
);

export const Titulo: React.FC<{
  x: number;
  y: number;
  tamanho: number;
  style?: React.CSSProperties;
  children: React.ReactNode;
}> = ({ x, y, tamanho, style, children }) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      fontFamily: FONTE_TITULO,
      fontWeight: 900,
      fontSize: tamanho,
      color: COR.creme,
      lineHeight: 1,
      whiteSpace: "nowrap",
      ...style,
    }}
  >
    {children}
  </div>
);

/** Selo em pílula, centralizado em (x, y). */
export const Pilula: React.FC<{
  x: number;
  y: number;
  tamanho: number;
  escala?: number;
  opacidade?: number;
  fundo?: string;
  cor?: string;
  peso?: number;
  children: React.ReactNode;
}> = ({ x, y, tamanho, escala = 1, opacidade = 1, fundo = COR.ouro, cor = COR.tinta, peso = 900, children }) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      translate: "-50% -50%",
      scale: escala,
      opacity: opacidade,
      padding: `${tamanho * 0.3}px ${tamanho * 0.55}px`,
      borderRadius: 999,
      background: fundo,
      color: cor,
      fontFamily: peso >= 800 ? FONTE_TITULO : FONTE_TEXTO,
      fontWeight: peso,
      fontSize: tamanho,
      letterSpacing: 2,
      lineHeight: 1,
      whiteSpace: "nowrap",
      boxShadow: "0 8px 24px rgba(0, 0, 0, 0.5)",
    }}
  >
    {children}
  </div>
);

/** Círculo com emoji no centro, centralizado em (x, y). */
export const SeloEmoji: React.FC<{
  x: number;
  y: number;
  emoji: string;
  diametro?: number;
  escala?: number;
  opacidade?: number;
  fundo?: string;
  borda?: string;
}> = ({ x, y, emoji, diametro = 170, escala = 1, opacidade = 1, fundo = COR.ouro, borda }) => (
  <div
    style={{
      position: "absolute",
      left: x - diametro / 2,
      top: y - diametro / 2,
      width: diametro,
      height: diametro,
      borderRadius: "50%",
      background: fundo,
      border: borda ? `9px solid ${borda}` : undefined,
      boxSizing: "border-box",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontSize: diametro * 0.52,
      lineHeight: 1,
      fontFamily: FONTE_TEXTO,
      scale: escala,
      opacity: opacidade,
      boxShadow: "0 8px 22px rgba(0, 0, 0, 0.45)",
    }}
  >
    {emoji}
  </div>
);

/**
 * Troca de conteúdo rolando na vertical dentro de uma janela:
 * o antigo sobe e some, o novo sobe e entra (p de 0 a 1).
 */
export const Rolagem: React.FC<{
  largura: number;
  altura: number;
  antigo: React.ReactNode | null;
  novo: React.ReactNode;
  p: number;
  style?: React.CSSProperties;
}> = ({ largura, altura, antigo, novo, p, style }) => {
  const caixa: React.CSSProperties = {
    position: "absolute",
    inset: 0,
    display: "flex",
    alignItems: "center",
  };
  return (
    <div style={{ position: "absolute", width: largura, height: altura, overflow: "hidden", ...style }}>
      {antigo !== null && p < 1 ? (
        <div style={{ ...caixa, translate: `0px ${-altura * p}px`, opacity: 1 - p }}>{antigo}</div>
      ) : null}
      <div style={{ ...caixa, translate: `0px ${altura * (1 - p)}px`, opacity: antigo === null ? 1 : p }}>{novo}</div>
    </div>
  );
};

/** Faixa listrada que abre do centro para as pontas. */
export const FaixaListrada: React.FC<{
  cx: number;
  y: number;
  largura: number;
  altura?: number;
  abertura: number;
}> = ({ cx, y, largura, altura = 16, abertura }) => (
  <div
    style={{
      position: "absolute",
      left: cx - largura / 2,
      top: y,
      width: largura,
      height: altura,
      background: LISTRAS_CSS,
      clipPath: `inset(0 ${(50 * (1 - abertura)).toFixed(3)}%)`,
    }}
  />
);
