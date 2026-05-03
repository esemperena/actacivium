import { useState } from "react";

interface VotoPartido {
  sigla: string;
  color: string;
  a_favor: number;
  en_contra: number;
  abstencion: number;
}

interface Props {
  votos: VotoPartido[];
}

export default function VotacionToggle({ votos }: Props) {
  const [open, setOpen] = useState(false);

  const totalFavor  = votos.reduce((s, v) => s + v.a_favor,    0);
  const totalContra = votos.reduce((s, v) => s + v.en_contra,  0);
  const totalAbst   = votos.reduce((s, v) => s + v.abstencion, 0);
  const total = totalFavor + totalContra + totalAbst;

  const pctFavor  = total > 0 ? (totalFavor  / total) * 100 : 0;
  const pctContra = total > 0 ? (totalContra / total) * 100 : 0;

  return (
    <div style={{ borderTop: "1px solid var(--color-border)", marginTop: "4px" }}>
      {/* ── Trigger ── */}
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        style={{
          display: "flex", alignItems: "center", width: "100%",
          padding: "10px 0", background: "none", border: "none",
          cursor: "pointer", gap: "10px", textAlign: "left",
          fontFamily: "var(--font-sans)",
        }}
      >
        <span style={{
          fontSize: "0.75rem", fontWeight: 600,
          letterSpacing: "0.06em", textTransform: "uppercase",
          color: "var(--color-ink-subtle)", flexShrink: 0,
        }}>
          Votación
        </span>

        {/* Proportional bar */}
        <div style={{
          flex: 1, height: "6px", borderRadius: "3px",
          overflow: "hidden", display: "flex",
          background: "var(--color-border)",
        }}>
          <div style={{
            width: `${pctFavor}%`, height: "100%",
            background: "var(--color-green-mid)",
            borderRadius: "3px 0 0 3px",
            transition: "width 0.3s ease",
          }} />
          <div style={{
            width: `${pctContra}%`, height: "100%",
            background: "var(--color-red-mid)",
            borderRadius: "0 3px 3px 0",
            transition: "width 0.3s ease",
          }} />
        </div>

        {/* Vote counts */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexShrink: 0 }}>
          {totalFavor > 0 && (
            <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--color-green)", display: "flex", alignItems: "center", gap: "3px" }}>
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                <path d="M1.5 5l2.5 2.5 4.5-4.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              {totalFavor}
            </span>
          )}
          {totalFavor > 0 && totalContra > 0 && (
            <span style={{ color: "var(--color-border-strong)", fontSize: "0.625rem" }}>·</span>
          )}
          {totalContra > 0 && (
            <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--color-red)", display: "flex", alignItems: "center", gap: "3px" }}>
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                <path d="M2 2l6 6M8 2l-6 6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
              </svg>
              {totalContra}
            </span>
          )}
          {totalAbst > 0 && (
            <>
              <span style={{ color: "var(--color-border-strong)", fontSize: "0.625rem" }}>·</span>
              <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--color-amber)" }}>
                {totalAbst} abs.
              </span>
            </>
          )}
        </div>

        {/* Chevron */}
        <svg
          width="14" height="14" viewBox="0 0 14 14" fill="none"
          style={{
            flexShrink: 0, color: "var(--color-ink-subtle)",
            transform: open ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform 0.2s ease",
          }}
        >
          <path d="M3 5l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </button>

      {/* ── Expanded panel ── */}
      {open && (
        <div style={{ paddingBottom: "14px" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "5px" }}>
            {votos.map((v) => {
              const total = v.a_favor + v.en_contra + v.abstencion;
              const allFavor  = v.a_favor  > 0 && v.en_contra === 0 && v.abstencion === 0;
              const allContra = v.en_contra > 0 && v.a_favor  === 0 && v.abstencion === 0;
              const chips = [
                ...Array(v.a_favor).fill("favor"),
                ...Array(v.en_contra).fill("contra"),
                ...Array(v.abstencion).fill("abstencion"),
              ] as Array<"favor" | "contra" | "abstencion">;

              return (
                <div key={v.sigla} style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span style={{
                    fontSize: "0.8125rem", fontWeight: 600,
                    color: v.color, width: "88px", flexShrink: 0,
                    whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
                  }} title={v.sigla}>
                    {v.sigla}
                  </span>
                  <div style={{ display: "flex", gap: "3px", flexWrap: "wrap", flex: 1 }}>
                    {chips.map((tipo, i) => (
                      <span key={i} style={{
                        width: "22px", height: "22px", borderRadius: "4px",
                        display: "flex", alignItems: "center", justifyContent: "center",
                        fontSize: "0.625rem", fontWeight: 700, flexShrink: 0,
                        background: tipo === "favor" ? "var(--color-green-bg)"
                          : tipo === "contra" ? "var(--color-red-bg)"
                          : "var(--color-amber-bg)",
                        color: tipo === "favor" ? "var(--color-green)"
                          : tipo === "contra" ? "var(--color-red)"
                          : "var(--color-amber)",
                      }}>
                        {tipo === "favor" ? "✓" : tipo === "contra" ? "✗" : "–"}
                      </span>
                    ))}
                  </div>
                  <span style={{
                    fontSize: "0.75rem", fontWeight: 600,
                    flexShrink: 0, width: "32px", textAlign: "right",
                    color: allFavor ? "var(--color-green)"
                      : allContra ? "var(--color-red)"
                      : "var(--color-ink-subtle)",
                  }}>
                    {allFavor  ? `+${v.a_favor}` :
                     allContra ? `−${v.en_contra}` :
                     total > 0 ? `${total}` : ""}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
