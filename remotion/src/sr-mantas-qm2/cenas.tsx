/**
 * Cenas do vídeo "SR Mantas Quarto de Milha 2".
 *
 * Cada cena roda dentro de um <Sequence> que começa em `CENAS.x.inicio`;
 * os tempos abaixo são escritos em segundos absolutos do vídeo (iguais aos
 * do roteiro) e convertidos para o relógio local da cena por `useCena`.
 */
import { Audio } from "@remotion/media";
import React from "react";
import { AbsoluteFill, Img, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import {
  Cartao,
  Chamada,
  FaixaListrada,
  Pilula,
  Rolagem,
  SeloEmoji,
  Titulo,
} from "../comum/componentes";
import {
  ACELERA,
  COR,
  ELASTICO,
  FONTE_TEXTO,
  FONTE_TITULO,
  SOMBRA_FILTRO,
  SUAVE,
  VAI_E_VOLTA,
  progresso,
} from "../comum/estilo";

export const DURACAO_TOTAL = 26.2333;

export const CENAS = {
  tamanho: { inicio: 0.7, fim: 2.1 },
  grossura: { inicio: 2.22, fim: 4.1 },
  quartoDeMilha: { inicio: 4.25, fim: 6.95 },
  modalidades: { inicio: 7.38, fim: 11.75 },
  respeito: { inicio: 11.8, fim: 14.5 },
  numeroUm: { inicio: 14.55, fim: 16.4 },
  fabricante: { inicio: 16.43, fim: 17.7 },
  estampas: { inicio: 17.8, fim: 19.95 },
  ideal: { inicio: 19.95, fim: 22.4 },
  cta: { inicio: 22.45, fim: 23.7 },
  assinatura: { inicio: 22.85, fim: DURACAO_TOTAL },
};

type Cena = keyof typeof CENAS;

const useCena = (cena: Cena) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { inicio, fim } = CENAS[cena];
  return {
    fps,
    /** tempo absoluto no vídeo, em segundos */
    t: inicio + frame / fps,
    /** progresso 0..1 entre dois tempos absolutos */
    p: (a: number, b: number, easing?: (x: number) => number) => progresso(frame, fps, a - inicio, b - inicio, easing),
    /** opacidade de saída nos últimos `d` segundos da cena */
    saida: (d = 0.2) => 1 - progresso(frame, fps, fim - inicio - d, fim - inicio, ACELERA),
    duracao: fim - inicio,
  };
};

const db = (ganho: number) => Math.pow(10, ganho / 20);

/** Efeito sonoro em um tempo absoluto, dentro da cena `cena`. */
const Som: React.FC<{ cena: Cena; em: number; arquivo: string; ganho: number }> = ({ cena, em, arquivo, ganho }) => {
  const { fps } = useVideoConfig();
  return (
    <Sequence name={`som ${arquivo}`} from={Math.round((em - CENAS[cena].inicio) * fps)} layout="none">
      <Audio src={staticFile(`sfx/${arquivo}.wav`)} volume={db(ganho)} />
    </Sequence>
  );
};

const seta = (x: number, y: number, direcao: 1 | -1, tam = 50) =>
  `${x + direcao * tam * 0.55},${y} ${x - direcao * tam * 0.45},${y - tam * 0.55} ${x - direcao * tam * 0.45},${y + tam * 0.55}`;

// ------------------------------------------------------------------ 0,7 s

/** "Olha o tamanho": cota de medida atravessando a manta. */
export const Tamanho: React.FC = () => {
  const { p, saida } = useCena("tamanho");
  const meia = 600 * p(0.72, 1.08, SUAVE);
  const pontas = p(1.02, 1.24, ELASTICO);
  const pp = p(0.8, 1.1);
  return (
    <AbsoluteFill style={{ opacity: saida() }}>
      <svg width={1440} height={240} style={{ position: "absolute", top: 1320, filter: SOMBRA_FILTRO }}>
        {meia > 4 ? (
          <>
            <line x1={720 - meia} y1={120} x2={720 + meia} y2={120} stroke={COR.ouro} strokeWidth={11} strokeLinecap="round" />
            <polygon points={seta(720 - meia - 6, 120, -1)} fill={COR.ouro} />
            <polygon points={seta(720 + meia + 6, 120, 1)} fill={COR.ouro} />
          </>
        ) : null}
        {[86, 1354].map((x) => (
          <line key={x} x1={x} y1={120 - 52 * pontas} x2={x} y2={120 + 52 * pontas} stroke={COR.ouro} strokeWidth={9} strokeLinecap="round" />
        ))}
      </svg>
      <Pilula x={720} y={1320} tamanho={70} escala={0.6 + 0.4 * ELASTICO(pp)} opacidade={SUAVE(pp)}>
        TAMANHO
      </Pilula>
      <Som cena="tamanho" em={0.7} arquivo="whoosh" ganho={-20} />
      <Som cena="tamanho" em={0.8} arquivo="pop" ganho={-18} />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ 2,2 s

/** "e a grossura": anel desenhado em volta da espessura do forro. */
export const Grossura: React.FC = () => {
  const { p, saida } = useCena("grossura");
  const anel = p(2.25, 2.75, VAI_E_VOLTA);
  const conector = p(2.55, 2.75, SUAVE);
  const pp = p(2.36, 2.66);
  return (
    <AbsoluteFill style={{ opacity: saida() }}>
      <svg width={640} height={1330} style={{ position: "absolute", left: 800, top: 600, filter: SOMBRA_FILTRO }}>
        <ellipse
          cx={320}
          cy={755}
          rx={520}
          ry={280}
          fill="none"
          stroke={COR.ouro}
          strokeWidth={12}
          pathLength={1}
          strokeDasharray={1}
          strokeDashoffset={1 - anel}
          transform="rotate(-90 320 755)"
        />
        {conector > 0 ? (
          <line x1={320} y1={112} x2={320} y2={112 + 123 * conector} stroke={COR.ouro} strokeWidth={7} strokeLinecap="round" />
        ) : null}
      </svg>
      <Pilula x={1120} y={660} tamanho={66} escala={0.6 + 0.4 * ELASTICO(pp)} opacidade={SUAVE(pp)}>
        GROSSURA
      </Pilula>
      <Som cena="grossura" em={2.22} arquivo="whoosh" ganho={-20} />
      <Som cena="grossura" em={2.38} arquivo="pop" ganho={-18} />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ 4,25 s

/** "Você que tem quarto de milha e participa". */
export const QuartoDeMilha: React.FC = () => {
  const { p, duracao } = useCena("quartoDeMilha");
  const selo = p(4.35, 4.65);
  const wipe = p(5.42, 5.75, SUAVE);
  return (
    <>
      <Cartao largura={1200} altura={250} cx={720} cy={300} duracao={duracao}>
        <SeloEmoji x={125} y={121} emoji="🐎" escala={0.3 + 0.7 * ELASTICO(selo)} opacidade={SUAVE(selo)} />
        <Chamada x={255} y={46}>VOCÊ QUE TEM</Chamada>
        <Titulo x={255} y={110} tamanho={96} style={{ clipPath: `inset(0 ${100 * (1 - wipe)}% 0 0)` }}>
          QUARTO DE MILHA
        </Titulo>
      </Cartao>
      <Som cena="quartoDeMilha" em={4.25} arquivo="whoosh" ganho={-20} />
      <Som cena="quartoDeMilha" em={4.38} arquivo="pop" ganho={-19} />
      <Som cena="quartoDeMilha" em={5.42} arquivo="whoosh-curto" ganho={-22} />
    </>
  );
};

// ------------------------------------------------------------------ 7,4 s

const MODALIDADES = [
  { em: 7.55, numero: "01", chamada: "PROVAS", nome: "TRÊS TAMBORES", icone: "🏇" },
  { em: 8.7, numero: "02", chamada: "PROVAS", nome: "RANCH SORTING", icone: "🐄" },
  { em: 9.45, numero: "03", chamada: "PROVAS", nome: "TEAM PENNING", icone: "🤠" },
  { em: 10.2, numero: "+", chamada: "E AINDA", nome: "VÁRIAS MODALIDADES", icone: "🏆" },
];

/** "provas de três tambores, ranch sorting, team penning e várias modalidades". */
export const Modalidades: React.FC = () => {
  const { t, p, duracao } = useCena("modalidades");
  const k = Math.max(0, MODALIDADES.filter((m) => t >= m.em).length - 1);
  const atual = MODALIDADES[k];
  const anterior = k > 0 ? MODALIDADES[k - 1] : null;
  const troca = k > 0 ? p(atual.em, atual.em + 0.28, VAI_E_VOLTA) : 1;
  const icone = k > 0 ? p(atual.em, atual.em + 0.32, ELASTICO) : 1;
  const numeral = (n: string) => (
    <div style={{ width: "100%", textAlign: "center", fontFamily: FONTE_TITULO, fontWeight: 900, fontSize: 128, color: COR.tinta, lineHeight: 1 }}>
      {n}
    </div>
  );
  const nome = (n: string) => (
    <div style={{ fontFamily: FONTE_TITULO, fontWeight: 900, fontSize: 72, color: COR.creme, lineHeight: 1, whiteSpace: "nowrap" }}>{n}</div>
  );
  return (
    <>
      <Cartao largura={1240} altura={270} cx={720} cy={310} duracao={duracao}>
        <div style={{ position: "absolute", left: 32, top: 35, width: 200, height: 200, borderRadius: 30, background: COR.ouro }}>
          <Rolagem largura={200} altura={200} antigo={anterior ? numeral(anterior.numero) : null} novo={numeral(atual.numero)} p={troca} />
        </div>
        <Chamada x={270} y={40}>{atual.chamada}</Chamada>
        <Rolagem largura={820} altura={110} antigo={anterior ? nome(anterior.nome) : null} novo={nome(atual.nome)} p={troca} style={{ left: 270, top: 92 }} />
        <div style={{ position: "absolute", left: 1152, top: 127, translate: "-50% -50%", fontSize: 96, lineHeight: 1, scale: Math.max(0.01, icone) }}>
          {atual.icone}
        </div>
        {MODALIDADES.map((m, i) => (
          <div
            key={m.numero}
            style={{
              position: "absolute",
              left: 270 + i * 36,
              top: 214,
              width: 18,
              height: 18,
              borderRadius: "50%",
              background: i <= k ? COR.ouro : "rgba(248, 239, 224, 0.35)",
            }}
          />
        ))}
      </Cartao>
      <Som cena="modalidades" em={7.38} arquivo="whoosh" ganho={-20} />
      {MODALIDADES.map((m) => (
        <React.Fragment key={m.numero}>
          <Som cena="modalidades" em={m.em} arquivo="tick" ganho={-18} />
          <Som cena="modalidades" em={m.em + 0.03} arquivo="pop" ganho={-20} />
        </React.Fragment>
      ))}
    </>
  );
};

// ------------------------------------------------------------------ 11,8 s

const batimento = (t: number) => {
  const fase = (t * 1.3) % 1;
  return 1 + 0.12 * Math.exp(-(((fase - 0.08) / 0.05) ** 2)) + 0.07 * Math.exp(-(((fase - 0.26) / 0.05) ** 2));
};

/** "e tem respeito pelo seu cavalo, pelo seu quarto de milha". */
export const Respeito: React.FC = () => {
  const { t, p, duracao } = useCena("respeito");
  const selo = p(11.9, 12.2);
  const barra = p(12.15, 13.45, VAI_E_VOLTA);
  const troca = p(13.7, 13.98, VAI_E_VOLTA);
  const titulo = (txt: string) => (
    <div style={{ fontFamily: FONTE_TITULO, fontWeight: 900, fontSize: 84, color: COR.creme, lineHeight: 1, whiteSpace: "nowrap" }}>{txt}</div>
  );
  return (
    <>
      <Cartao largura={1200} altura={290} cx={720} cy={320} duracao={duracao}>
        <SeloEmoji x={125} y={141} emoji="❤️" escala={(0.3 + 0.7 * ELASTICO(selo)) * batimento(t)} opacidade={SUAVE(selo)} />
        <Chamada x={255} y={38}>RESPEITO PELO SEU</Chamada>
        <Rolagem
          largura={890}
          altura={100}
          antigo={t >= 13.7 ? titulo("CAVALO") : null}
          novo={titulo(t >= 13.7 ? "QUARTO DE MILHA" : "CAVALO")}
          p={t >= 13.7 ? troca : 1}
          style={{ left: 255, top: 86 }}
        />
        <div style={{ position: "absolute", left: 255, top: 206, width: 755, height: 30, borderRadius: 15, background: "rgba(248, 239, 224, 0.24)" }} />
        <div style={{ position: "absolute", left: 255, top: 206, width: Math.max(30, 755 * barra), height: 30, borderRadius: 15, background: COR.ouro, opacity: barra > 0.02 ? 1 : 0 }} />
        <div style={{ position: "absolute", left: 1036, top: 196, fontFamily: FONTE_TITULO, fontWeight: 900, fontSize: 50, color: COR.creme, lineHeight: 1 }}>
          {Math.round(100 * barra)}%
        </div>
      </Cartao>
      <Som cena="respeito" em={11.8} arquivo="whoosh" ganho={-20} />
      {Array.from({ length: 10 }, (_, i) => (
        <Som key={i} cena="respeito" em={12.15 + i * 0.13} arquivo="tick" ganho={-25} />
      ))}
      <Som cena="respeito" em={13.45} arquivo="ding" ganho={-18} />
      <Som cena="respeito" em={13.7} arquivo="pop" ganho={-20} />
    </>
  );
};

// ------------------------------------------------------------------ 14,55 s

const elastico = (x: number) =>
  x <= 0 ? 0 : x >= 1 ? 1 : 2 ** (-10 * x) * Math.sin(((x * 10 - 0.75) * (2 * Math.PI)) / 3) + 1;

const Raios: React.FC<{ rotacao: number }> = ({ rotacao }) => {
  const n = 14;
  const r = 410;
  return (
    <svg width={820} height={820} viewBox="-410 -410 820 820" style={{ rotate: `${rotacao}deg`, filter: "blur(4px)" }}>
      <defs>
        <radialGradient id="raio-fade">
          <stop offset="0%" stopColor={COR.ouro} stopOpacity={0.55} />
          <stop offset="100%" stopColor={COR.ouro} stopOpacity={0} />
        </radialGradient>
      </defs>
      {Array.from({ length: n }, (_, i) => {
        const a0 = (2 * Math.PI * i) / n;
        const a1 = a0 + Math.PI / n;
        return <polygon key={i} points={`0,0 ${r * Math.cos(a0)},${r * Math.sin(a0)} ${r * Math.cos(a1)},${r * Math.sin(a1)}`} fill="url(#raio-fade)" />;
      })}
    </svg>
  );
};

/** "a melhor manta do Brasil": medalha Nº com contagem regressiva até 1. */
export const NumeroUm: React.FC = () => {
  const { t, p, duracao } = useCena("numeroUm");
  const bandeira = p(15.45, 15.75, ELASTICO);
  const entra = p(14.68, 15.08, ELASTICO);
  const sai = 1 - p(16.18, 16.4, ACELERA);
  const impacto = t >= 15.5;
  const raios = p(15.5, 15.75, SUAVE);
  const passos = 8;
  const passo = 0.76 / passos;
  const i = Math.min(passos - 1, Math.max(0, Math.floor((t - 14.72) / passo)));
  const rolagem = t < 14.72 ? 0 : p(14.72 + i * passo, 14.72 + i * passo + passo * 0.8, VAI_E_VOLTA);
  const bump = impacto ? 1 + 0.22 * (1 - elastico(p(15.5, 16.2))) : 1;
  const digito = (d: number) => (
    <div style={{ width: "100%", textAlign: "center", fontFamily: FONTE_TITULO, fontWeight: 900, fontSize: 150, color: COR.tinta, lineHeight: 1 }}>{d}</div>
  );
  return (
    <>
      <Cartao largura={1000} altura={250} cx={560} cy={320} duracao={duracao}>
        <Chamada x={50} y={48}>A MELHOR MANTA</Chamada>
        <Titulo x={50} y={106} tamanho={108}>
          DO BRASIL{" "}
          <span style={{ display: "inline-block", fontSize: 88, scale: Math.max(0.01, bandeira) }}>🇧🇷</span>
        </Titulo>
      </Cartao>
      {impacto ? (
        <div style={{ position: "absolute", left: 1185 - 410, top: 320 - 410, opacity: SUAVE(raios) * sai, scale: 0.4 + 0.6 * raios }}>
          <Raios rotacao={(t - 15.5) * 28} />
        </div>
      ) : null}
      <div
        style={{
          position: "absolute",
          left: 1185 - 165,
          top: 320 - 165,
          width: 330,
          height: 330,
          borderRadius: "50%",
          boxSizing: "border-box",
          border: `14px solid ${COR.ouroEscuro}`,
          background: "radial-gradient(circle at 45% 38%, #ffe278 0%, #f5bf3a 55%, #e2a01c 100%)",
          boxShadow: "0 12px 34px rgba(0, 0, 0, 0.55)",
          scale: Math.max(0.01, (0.82 + 0.18 * entra) * bump * (0.9 + 0.1 * sai)),
          opacity: SUAVE(p(14.68, 14.9)) * sai,
        }}
      >
        <div style={{ position: "absolute", inset: 12, borderRadius: "50%", border: "4px solid rgba(248, 239, 224, 0.67)" }} />
        <div style={{ position: "absolute", top: 40, width: "100%", textAlign: "center", fontFamily: FONTE_TITULO, fontWeight: 900, fontSize: 50, color: COR.tinta }}>
          Nº
        </div>
        <Rolagem
          largura={220}
          altura={170}
          antigo={t < 14.72 ? null : digito(9 - i)}
          novo={digito(t < 14.72 ? 9 : 8 - i)}
          p={t < 14.72 ? 1 : rolagem}
          style={{ left: 41, top: 110 }}
        />
      </div>
      <Som cena="numeroUm" em={14.52} arquivo="whoosh" ganho={-20} />
      {Array.from({ length: passos }, (_, n) => (
        <Som key={n} cena="numeroUm" em={14.72 + n * 0.095} arquivo="tick" ganho={-21} />
      ))}
      <Som cena="numeroUm" em={15.48} arquivo="impacto" ganho={-9} />
    </>
  );
};

// ------------------------------------------------------------------ 16,43 s

/** "compra direto do fabricante": Fábrica → Você. */
export const Fabricante: React.FC = () => {
  const { t, p, saida } = useCena("fabricante");
  const y = 330;
  const x0 = 340;
  const x1 = 1100;
  const seta1 = p(16.55, 16.95, VAI_E_VOLTA);
  const fimX = x0 + (x1 - x0) * seta1;
  const pp = p(16.72, 17.02);
  return (
    <AbsoluteFill style={{ opacity: saida(0.22) }}>
      {[
        { emoji: "🏭", rotulo: "FÁBRICA", x: 215, em: 16.45 },
        { emoji: "🏠", rotulo: "VOCÊ", x: 1225, em: 16.66 },
      ].map((b) => {
        const e = p(b.em, b.em + 0.32);
        const escala = 0.3 + 0.7 * ELASTICO(e);
        return (
          <React.Fragment key={b.rotulo}>
            <SeloEmoji x={b.x} y={y} emoji={b.emoji} diametro={200} fundo={COR.creme} borda={COR.ouro} escala={escala} opacidade={SUAVE(e)} />
            <Pilula x={b.x} y={y + 150} tamanho={40} peso={700} fundo="rgba(20, 13, 10, 0.92)" cor={COR.creme} escala={escala} opacidade={SUAVE(e)}>
              {b.rotulo}
            </Pilula>
          </React.Fragment>
        );
      })}
      {seta1 > 0 ? (
        <svg width={1440} height={140} style={{ position: "absolute", top: y - 70, filter: SOMBRA_FILTRO }}>
          <line
            x1={x0}
            y1={70}
            x2={Math.max(x0, fimX - 30)}
            y2={70}
            stroke={COR.ouro}
            strokeWidth={13}
            strokeLinecap="round"
            strokeDasharray="40 24"
            strokeDashoffset={-(t * 260) % 64}
          />
          <polygon points={seta(fimX - 8, 70, 1, 54)} fill={COR.ouro} />
        </svg>
      ) : null}
      <Pilula x={720} y={y - 135} tamanho={50} escala={0.6 + 0.4 * ELASTICO(pp)} opacidade={SUAVE(pp)}>
        DIRETO DO FABRICANTE
      </Pilula>
      <Som cena="fabricante" em={16.43} arquivo="whoosh" ganho={-20} />
      <Som cena="fabricante" em={16.47} arquivo="pop" ganho={-19} />
      <Som cena="fabricante" em={16.55} arquivo="whoosh-curto" ganho={-22} />
      <Som cena="fabricante" em={16.66} arquivo="pop" ganho={-19} />
      <Som cena="fabricante" em={16.72} arquivo="pop" ganho={-18} />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ 17,8 s

/** "Várias estampas, vários modelos": amostras reais recortadas do vídeo. */
export const Estampas: React.FC = () => {
  const { t, p } = useCena("estampas");
  const sai = p(19.73, 19.95, ACELERA);
  const giros = [-5, 3, -3, 5];
  const segundo = t >= 18.8;
  const pp = p(segundo ? 18.8 : 17.95, segundo ? 19.1 : 18.25);
  return (
    <AbsoluteFill>
      {[330, 590, 850, 1110].map((x, i) => {
        const e = p(17.85 + 0.12 * i, 18.2 + 0.12 * i);
        const boia = 7 * Math.sin(2 * Math.PI * 0.8 * t + i * 1.3);
        return (
          <Img
            key={x}
            src={staticFile(`estampas/estampa-${i + 1}.jpg`)}
            style={{
              position: "absolute",
              left: x - 123,
              top: 300 - 123 + boia + 80 * (1 - SUAVE(e)) - 40 * sai,
              width: 246,
              height: 246,
              boxSizing: "border-box",
              border: `8px solid ${COR.creme}`,
              borderRadius: 34,
              objectFit: "cover",
              boxShadow: "0 10px 30px rgba(0, 0, 0, 0.55)",
              scale: Math.max(0.01, (0.4 + 0.6 * ELASTICO(e)) * (1 - 0.15 * sai)),
              rotate: `${giros[i] * (1 - 0.4 * SUAVE(e))}deg`,
              opacity: SUAVE(e) * (1 - sai),
            }}
          />
        );
      })}
      <Pilula x={720} y={452} tamanho={50} escala={0.6 + 0.4 * ELASTICO(pp)} opacidade={(segundo ? 1 : SUAVE(pp)) * (1 - sai)}>
        {segundo ? "VÁRIOS MODELOS" : "VÁRIAS ESTAMPAS"}
      </Pilula>
      <Som cena="estampas" em={17.8} arquivo="whoosh" ganho={-20} />
      {[0, 1, 2, 3].map((i) => (
        <Som key={i} cena="estampas" em={17.85 + 0.12 * i} arquivo={`pop-${i}`} ganho={-19} />
      ))}
      <Som cena="estampas" em={18.8} arquivo="pop" ganho={-18} />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ 19,95 s

/** "ideal para o seu quarto de milha e respeito à sua montaria". */
export const Ideal: React.FC = () => {
  const { p, duracao } = useCena("ideal");
  const linhas = [
    { em: 20.0, texto: "IDEAL PARA SEU QUARTO DE MILHA", y: 92 },
    { em: 21.6, texto: "RESPEITO À SUA MONTARIA", y: 186 },
  ];
  return (
    <>
      <Cartao largura={1240} altura={270} cx={720} cy={315} duracao={duracao}>
        {linhas.map((l) => {
          const e = p(l.em, l.em + 0.3);
          const marca = p(l.em + 0.08, l.em + 0.3, SUAVE);
          const texto = p(l.em + 0.05, l.em + 0.38, SUAVE);
          if (e <= 0) return null;
          return (
            <React.Fragment key={l.texto}>
              <svg width={78} height={78} viewBox="0 0 78 78" style={{ position: "absolute", left: 23, top: l.y - 39, scale: 0.3 + 0.7 * ELASTICO(e) }}>
                <circle cx={39} cy={39} r={39} fill={COR.ouro} />
                <polyline
                  points="21.8,39.8 34.3,52.3 57.7,26.5"
                  fill="none"
                  stroke={COR.tinta}
                  strokeWidth={9.4}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  pathLength={1}
                  strokeDasharray={1}
                  strokeDashoffset={1 - marca}
                />
              </svg>
              <div
                style={{
                  position: "absolute",
                  left: 125 - 30 * (1 - texto),
                  top: l.y - 27,
                  opacity: texto,
                  fontFamily: FONTE_TITULO,
                  fontWeight: 800,
                  fontSize: 54,
                  color: COR.creme,
                  lineHeight: 1,
                  whiteSpace: "nowrap",
                }}
              >
                {l.texto}
              </div>
            </React.Fragment>
          );
        })}
      </Cartao>
      <Som cena="ideal" em={19.93} arquivo="whoosh" ganho={-20} />
      <Som cena="ideal" em={20.0} arquivo="ding" ganho={-18} />
      <Som cena="ideal" em={21.6} arquivo="ding" ganho={-18} />
    </>
  );
};

// ------------------------------------------------------------------ 22,45 s

/** "Vem pra cá": cartão e setas pulsando para baixo. */
export const Cta: React.FC = () => {
  const { t, p, duracao, saida } = useCena("cta");
  const setas = SUAVE(p(22.55, 22.8)) * saida();
  return (
    <>
      <Cartao largura={880} altura={230} cx={720} cy={300} duracao={duracao}>
        <Titulo x={56} y={65} tamanho={100}>VEM PRA CÁ!</Titulo>
        <div style={{ position: "absolute", left: 800, top: 115 + 8 * Math.sin(2 * Math.PI * 3 * t), translate: "-50% -50%", fontSize: 96, lineHeight: 1 }}>
          👇
        </div>
      </Cartao>
      <svg width={260} height={330} style={{ position: "absolute", left: 720 - 130, top: 2215 - 165, opacity: setas, filter: SOMBRA_FILTRO }}>
        {[0, 1, 2].map((i) => {
          const brilho = Math.max(0, Math.sin(2 * Math.PI * 2.2 * t - i * 0.9));
          const y = 60 + i * 90;
          return (
            <polyline
              key={i}
              points={`50,${y - 30} 130,${y + 30} 210,${y - 30}`}
              fill="none"
              stroke={COR.ouro}
              strokeOpacity={0.45 + 0.55 * brilho}
              strokeWidth={22}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          );
        })}
      </svg>
      <Som cena="cta" em={22.45} arquivo="whoosh" ganho={-19} />
      <Som cena="cta" em={22.5} arquivo="pop" ganho={-18} />
    </>
  );
};

// ------------------------------------------------------------------ 23,72 s

const LOGO = "SR MANTAS";
const LOGO_TAMANHO = 190;

/** "SR Mantas, a melhor do Brasil": assinatura da marca. */
export const Assinatura: React.FC = () => {
  const { p } = useCena("assinatura");
  const brilho = p(25.35, 25.95, VAI_E_VOLTA);
  const faixa = p(24.35, 24.75, SUAVE);
  const tag = p(24.75, 25.1, SUAVE);
  const bandeira = p(25.25, 25.55, ELASTICO);
  let k = 0;
  const atrasos = LOGO.split("").map((ch, i) => (ch === " " ? 0 : i < 2 ? 23.78 + 0.05 * i : 24.22 + 0.045 * ++k));
  const textoLogo: React.CSSProperties = {
    fontFamily: FONTE_TITULO,
    fontWeight: 900,
    fontSize: LOGO_TAMANHO,
    letterSpacing: 6,
    lineHeight: 1,
    whiteSpace: "pre",
  };
  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: 0,
          height: 620,
          background: "linear-gradient(180deg, rgba(18, 11, 8, 0) 0%, rgba(18, 11, 8, 0.55) 45%, rgba(18, 11, 8, 0.9) 100%)",
          opacity: SUAVE(p(23.72, 24.02)),
        }}
      />
      <div style={{ position: "absolute", left: 0, right: 0, top: 2075, display: "flex", justifyContent: "center" }}>
        <div style={{ position: "relative", ...textoLogo, color: COR.creme, filter: "drop-shadow(0 8px 16px rgba(0, 0, 0, 0.6))" }}>
          {LOGO.split("").map((ch, i) => {
            const e = p(atrasos[i], atrasos[i] + 0.28, SUAVE);
            return (
              <span key={i} style={{ display: "inline-block", opacity: ch === " " ? 1 : e, scale: ch === " " ? 1 : 1.8 - 0.8 * e, translate: `0px ${-30 * (1 - e)}px` }}>
                {ch}
              </span>
            );
          })}
          {brilho > 0 && brilho < 1 ? (
            <div
              style={{
                position: "absolute",
                inset: 0,
                ...textoLogo,
                color: "transparent",
                backgroundImage: "linear-gradient(105deg, transparent 42%, rgba(255, 255, 255, 0.95) 50%, transparent 58%)",
                backgroundSize: "300% 100%",
                backgroundPosition: `${100 - 100 * brilho}% 0%`,
                WebkitBackgroundClip: "text",
                backgroundClip: "text",
              }}
            >
              {LOGO}
            </div>
          ) : null}
        </div>
      </div>
      <FaixaListrada cx={720} y={2270} largura={1010} abertura={faixa} />
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 2318 + 30 * (1 - tag),
          opacity: tag,
          textAlign: "center",
          fontFamily: FONTE_TEXTO,
          fontWeight: 700,
          fontSize: 54,
          letterSpacing: 9,
          color: COR.ouro,
          lineHeight: 1,
        }}
      >
        A MELHOR DO BRASIL{" "}
        <span style={{ display: "inline-block", fontSize: 58, scale: Math.max(0.01, bandeira) }}>🇧🇷</span>
      </div>
      <Som cena="assinatura" em={22.88} arquivo="riser" ganho={-18} />
      <Som cena="assinatura" em={23.74} arquivo="whoosh" ganho={-19} />
      <Som cena="assinatura" em={24.22} arquivo="impacto" ganho={-8} />
      <Som cena="assinatura" em={25.35} arquivo="brilho" ganho={-18} />
    </AbsoluteFill>
  );
};
