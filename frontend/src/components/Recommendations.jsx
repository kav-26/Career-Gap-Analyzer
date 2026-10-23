import { useState } from "react";

const DIFF_LABEL = { beginner: "Beginner", intermediate: "Intermediate", advanced: "Advanced" };

function CopyButton({ text }) {
  const [done, setDone] = useState(false);
  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setDone(true);
      setTimeout(() => setDone(false), 1500);
    } catch {
      /* clipboard not available */
    }
  }
  return (
    <button className="link" onClick={copy}>
      {done ? "Copied" : "Copy"}
    </button>
  );
}

export default function Recommendations({ recs, status, error, onGenerate }) {
  if (!recs) {
    if (status === "loading") {
      return (
        <div className="card center">
          <span className="spinner big" />
          <h2>Writing project ideas...</h2>
          <p className="muted">
            Your gap results are already ready in the other tabs. This part can take a little longer.
          </p>
        </div>
      );
    }
    return (
      <div className="card center">
        <h2>Project recommendations</h2>
        <p className="muted">Projects that would close your biggest gaps, ranked by impact.</p>
        {error && <p className="error">{error}</p>}
        <button className="btn primary" onClick={onGenerate}>
          Generate project recommendations
        </button>
      </div>
    );
  }

  if (!recs.projects || recs.projects.length === 0) {
    return <div className="card">{recs.message || "No projects were suggested."}</div>;
  }

  return (
    <div>
      <p className="muted">
        Impact is the share of your total skill gap that a project closes on its own. Projects overlap,
        so the percentages add up to more than 100%.
      </p>
      {recs.projects.map((p, i) => (
        <section className="card project" key={p.title + i}>
          <div className="row-between">
            <h2>
              {i + 1}. {p.title}
            </h2>
            <span className="impact">{Math.round(p.impact_pct)}% impact</span>
          </div>
          <div className="bar">
            <div className="bar-fill" style={{ width: `${Math.min(100, p.impact_pct)}%` }} />
          </div>
          <div className="meta">
            <span className="chip">{DIFF_LABEL[p.difficulty] || p.difficulty}</span>
            <span className="chip">
              {p.estimated_weeks} week{p.estimated_weeks === 1 ? "" : "s"}
            </span>
          </div>
          <p>{p.description}</p>

          <div className="detail-label">Closes these gaps</div>
          <div className="chips">
            {p.gaps_addressed.map((g) => (
              <span className="chip gap" key={g}>
                {g}
              </span>
            ))}
          </div>

          <div className="detail-label">Deliverables</div>
          <ul className="list">
            {p.deliverables.map((d) => (
              <li key={d}>{d}</li>
            ))}
          </ul>

          <div className="resume">
            <div className="row-between">
              <span className="detail-label">Resume bullet (use after finishing)</span>
              <CopyButton text={p.resume_bullet} />
            </div>
            <div>{p.resume_bullet}</div>
          </div>
        </section>
      ))}

      {recs.gaps_not_covered && recs.gaps_not_covered.length > 0 && (
        <p className="muted">Not covered by these projects: {recs.gaps_not_covered.join(", ")}</p>
      )}
    </div>
  );
}
