import { useState } from "react";

interface Partido {
  sigla: string;
  concejales: number;
  color: string;
}

interface Props {
  composicion: Partido[];
  total: number;
}

const W = 232, H = 124, CX = 116, CY = 124;
const R_OUT = 108, R_IN = 68;
const GAP_DEG = 1.4;

function toRad(deg: number) {
  return (deg * Math.PI) / 180;
}

function arcPath(startDeg: number, endDeg: number): string {
  const s1 = { x: CX + R_OUT * Math.cos(toRad(startDeg)), y: CY + R_OUT * Math.sin(toRad(startDeg)) };
  const e1 = { x: CX + R_OUT * Math.cos(toRad(endDeg)),   y: CY + R_OUT * Math.sin(toRad(endDeg)) };
  const s2 = { x: CX + R_IN  * Math.cos(toRad(endDeg)),   y: CY + R_IN  * Math.sin(toRad(endDeg)) };
  const e2 = { x: CX + R_IN  * Math.cos(toRad(startDeg)), y: CY + R_IN  * Math.sin(toRad(startDeg)) };
  const large = endDeg - startDeg > 180 ? 1 : 0;
  return [
    `M ${s1.x.toFixed(2)} ${s1.y.toFixed(2)}`,
    `A ${R_OUT} ${R_OUT} 0 ${large} 1 ${e1.x.toFixed(2)} ${e1.y.toFixed(2)}`,
    `L ${s2.x.toFixed(2)} ${s2.y.toFixed(2)}`,
    `A ${R_IN} ${R_IN} 0 ${large} 0 ${e2.x.toFixed(2)} ${e2.y.toFixed(2)}`,
    "Z",
  ].join(" ");
}

export default function ParlamentArc({ composicion, total }: Props) {
  const [hovered, setHovered] = useState<string | null>(null);

  // Build segments: 180° → 360° (left to right semicircle)
  let cursor = 180;
  const segments = composicion.map((p, i) => {
    const spanDeg = (p.concejales / total) * 180;
    const gap = i === composicion.length - 1 ? 0 : GAP_DEG;
    const seg = { ...p, startDeg: cursor, endDeg: cursor + spanDeg - gap };
    cursor += spanDeg;
    return seg;
  });

  const hoveredPartido = hovered ? composicion.find((p) => p.sigla === hovered) : null;

  return (
    <div>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        width="100%"
        style={{ display: "block", overflow: "visible", marginBottom: "14px" }}
        aria-hidden="true"
      >
        {segments.map((seg) => (
          <path
            key={seg.sigla}
            d={arcPath(seg.startDeg, seg.endDeg)}
            fill={seg.color}
            opacity={hovered === null || hovered === seg.sigla ? 1 : 0.35}
            style={{ transition: "opacity 0.15s", cursor: "default" }}
            onMouseEnter={() => setHovered(seg.sigla)}
            onMouseLeave={() => setHovered(null)}
          >
            <title>{seg.sigla}: {seg.concejales} {seg.concejales === 1 ? "concejal" : "concejales"}</title>
          </path>
        ))}
        {/* Central label */}
        <text
          x={CX} y={CY - 18}
          textAnchor="middle"
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: "22px", fontWeight: 700,
            fill: "var(--color-ink)", letterSpacing: "-0.03em",
          }}
        >
          {hoveredPartido ? hoveredPartido.concejales : total}
        </text>
        <text
          x={CX} y={CY - 4}
          textAnchor="middle"
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: "9px", fontWeight: 600,
            fill: "var(--color-ink-subtle)",
            letterSpacing: "0.08em",
          }}
        >
          {hoveredPartido ? hoveredPartido.sigla : "concejales"}
        </text>
      </svg>

      {/* Legend */}
      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
        {composicion.map((p) => (
          <div
            key={p.sigla}
            onMouseEnter={() => setHovered(p.sigla)}
            onMouseLeave={() => setHovered(null)}
            style={{
              display: "flex", alignItems: "center", gap: "8px",
              opacity: hovered === null || hovered === p.sigla ? 1 : 0.4,
              transition: "opacity 0.15s", cursor: "default",
            }}
          >
            <span style={{
              width: "8px", height: "8px", borderRadius: "50%",
              background: p.color, flexShrink: 0,
            }} />
            <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--color-ink)", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {p.sigla}
            </span>
            <span style={{ fontSize: "0.6875rem", fontWeight: 600, color: "var(--color-ink-subtle)", flexShrink: 0 }}>
              {Math.round((p.concejales / total) * 100)}%
            </span>
            <span style={{ fontSize: "0.6875rem", color: "var(--color-ink-subtle)", flexShrink: 0, width: "42px", textAlign: "right" }}>
              {p.concejales} esc.
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
