import { useState } from "react";

interface PartidoAsistencia {
  sigla: string;
  color: string;
  presentes: number;
  total: number;
}

interface Props {
  asistencia: PartidoAsistencia[];
}

const DOT = 7;
const GAP = 3;

export default function AsistenciaWidget({ asistencia }: Props) {
  const [hovered, setHovered] = useState<string | null>(null);

  const totalPresentes = asistencia.reduce((s, p) => s + p.presentes, 0);
  const totalConcejales = asistencia.reduce((s, p) => s + p.total, 0);
  const totalAusentes = totalConcejales - totalPresentes;

  return (
    <div>
      {asistencia.map((p) => {
        const ausentes = p.total - p.presentes;
        const isActive = hovered === null || hovered === p.sigla;
        return (
          <div
            key={p.sigla}
            onMouseEnter={() => setHovered(p.sigla)}
            onMouseLeave={() => setHovered(null)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              marginBottom: "8px",
              opacity: isActive ? 1 : 0.4,
              transition: "opacity 0.15s",
              cursor: "default",
            }}
          >
            {/* Sigla */}
            <div style={{
              display: "flex", alignItems: "center", gap: "5px",
              width: "76px", flexShrink: 0,
            }}>
              <span style={{
                width: "7px", height: "7px", borderRadius: "50%",
                background: p.color, flexShrink: 0, display: "inline-block",
              }} />
              <span style={{
                fontSize: "0.6875rem", fontWeight: 600,
                color: "var(--color-ink)",
                overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
              }}>
                {p.sigla}
              </span>
            </div>

            {/* Dots: presentes (color partido) + ausentes (gris) */}
            <div style={{
              display: "flex", gap: `${GAP}px`, flex: 1, flexWrap: "wrap",
              alignItems: "center",
            }}>
              {Array.from({ length: p.presentes }).map((_, i) => (
                <span key={`p-${i}`} style={{
                  width: `${DOT}px`, height: `${DOT}px`, borderRadius: "50%",
                  background: p.color, flexShrink: 0, display: "inline-block",
                }} />
              ))}
              {Array.from({ length: ausentes }).map((_, i) => (
                <span key={`a-${i}`} style={{
                  width: `${DOT}px`, height: `${DOT}px`, borderRadius: "50%",
                  background: "var(--color-border-strong)",
                  flexShrink: 0, display: "inline-block",
                  opacity: 0.5,
                }} />
              ))}
            </div>

            {/* Recuento */}
            <span style={{
              fontSize: "0.6875rem", color: "var(--color-ink-subtle)",
              flexShrink: 0, width: "28px", textAlign: "right",
            }}>
              {p.presentes}/{p.total}
            </span>
          </div>
        );
      })}

      {/* Resumen total */}
      {totalAusentes > 0 && (
        <div style={{
          marginTop: "10px",
          paddingTop: "8px",
          borderTop: "1px solid var(--color-border)",
          fontSize: "0.6875rem",
          color: "var(--color-ink-subtle)",
        }}>
          <strong style={{ color: "var(--color-ink)" }}>{totalPresentes}</strong> presentes
          {" · "}
          <strong style={{ color: "var(--color-amber, #b45309)" }}>{totalAusentes}</strong>{" "}
          {totalAusentes === 1 ? "ausente" : "ausentes"}
        </div>
      )}
    </div>
  );
}
