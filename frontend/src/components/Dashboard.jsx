import { Fragment, useState } from "react";
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell,
  LabelList,
  PieChart,
  Pie,
} from "recharts";

const STATUS_LABEL = { covered: "Covered", partial: "Partial", missing: "Missing" };
const LEVEL_LABEL = { exposure: "Exposure", working: "Working", proficient: "Proficient" };
const STATUS_ORDER = { missing: 0, partial: 1, covered: 2 };
const STATUS_COLOR = { covered: "#10b981", partial: "#f59e0b", missing: "#ef4444" };

function verdict(score) {
  if (score >= 70) return { title: "Strong match", text: "You already cover most of what this job asks for." };
  if (score >= 40) return { title: "Promising match", text: "You have a solid base, with some clear gaps to close." };
  return { title: "Big gaps, but fixable", text: "Several key skills are missing. The projects tab shows how to close them." };
}

function Ring({ value }) {
  const r = 52;
  const c = 2 * Math.PI * r;
  return (
    <svg width="132" height="132" viewBox="0 0 132 132" className="ring-svg">
      <circle cx="66" cy="66" r={r} fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth="12" />
      <circle
        cx="66"
        cy="66"
        r={r}
        fill="none"
        stroke="#ffffff"
        strokeWidth="12"
        strokeLinecap="round"
        strokeDasharray={`${(value / 100) * c} ${c}`}
        transform="rotate(-90 66 66)"
      />
      <text x="66" y="70" textAnchor="middle" fill="#ffffff" fontSize="34" fontWeight="700">
        {Math.round(value)}
      </text>
      <text x="66" y="90" textAnchor="middle" fill="rgba(255,255,255,0.8)" fontSize="12">
        out of 100
      </text>
    </svg>
  );
}

function RadarTip({ active, payload }) {
  if (!active || !payload || !payload.length) return null;
  const d = payload[0].payload;
  return (
    <div className="tip">
      <strong>{d.category}</strong>
      <div>Your coverage: {d.coverage}%</div>
      <div className="muted small">{d.requirements} requirement(s) in this area</div>
    </div>
  );
}

function BarTip({ active, payload }) {
  if (!active || !payload || !payload.length) return null;
  const d = payload[0].payload;
  return (
    <div className="tip">
      <strong>{d.name}</strong>
      <div>
        {STATUS_LABEL[d.status]}: {d.value}%
      </div>
      {d.matched && <div className="muted small">Matched with: {d.matched}</div>}
    </div>
  );
}

function SkillTick({ x, y, payload, byName }) {
  const item = byName[payload.value];
  const fill = item ? STATUS_COLOR[item.status] : "#94a3b8";
  const text = payload.value.length > 22 ? payload.value.slice(0, 21) + "\u2026" : payload.value;
  return (
    <g transform={`translate(${x},${y})`}>
      <circle cx={-8} cy={0} r={4} fill={fill} />
      <text x={-18} y={0} dy={4} textAnchor="end" fill="#334155" fontSize={12}>
        {text}
      </text>
    </g>
  );
}

export default function Dashboard({ analysis, section = "overview", jobName = "", onNavigate }) {
  const { match_score, counts, radar, requirements } = analysis;
  const [filter, setFilter] = useState("all");
  const [open, setOpen] = useState(null);

  const v = verdict(match_score);
  const mustAll = requirements.filter((r) => r.importance === "must_have");
  const mustCovered = mustAll.filter((r) => r.status === "covered").length;

  const radarData = radar.map((r) => ({
    label: `${r.category} (${r.requirements})`,
    category: r.category,
    coverage: r.coverage,
    target: 100,
    requirements: r.requirements,
  }));

  const pieData = [
    { name: "Covered", value: counts.covered, color: STATUS_COLOR.covered },
    { name: "Partial", value: counts.partial, color: STATUS_COLOR.partial },
    { name: "Missing", value: counts.missing, color: STATUS_COLOR.missing },
  ].filter((d) => d.value > 0);

  const barData = requirements
    .map((r) => ({
      name: r.requirement,
      value: Math.round(r.score * 100),
      status: r.status,
      matched: r.matched_skill,
    }))
    .sort((a, b) => b.value - a.value);
  const byName = Object.fromEntries(barData.map((d) => [d.name, d]));

  const topGaps = requirements
    .filter((r) => r.status !== "covered")
    .slice()
    .sort((a, b) => {
      const wa = (a.importance === "must_have" ? 2 : 1) * (1 - a.score);
      const wb = (b.importance === "must_have" ? 2 : 1) * (1 - b.score);
      return wb - wa;
    })
    .slice(0, 5);

  const rows = requirements
    .filter((r) => filter === "all" || r.status === filter)
    .slice()
    .sort((a, b) => {
      if (STATUS_ORDER[a.status] !== STATUS_ORDER[b.status]) {
        return STATUS_ORDER[a.status] - STATUS_ORDER[b.status];
      }
      return (a.importance === "must_have" ? 0 : 1) - (b.importance === "must_have" ? 0 : 1);
    });

  return (
    <div>
      {section === "overview" && (
      <>
      {/* Summary */}
      <section className="hero-card">
        <Ring value={match_score} />
        <div className="hero-text">
          <div className="eyebrow">Overall match{jobName ? ` \u00B7 ${jobName}` : ""}</div>
          <h2>{v.title}</h2>
          <p>{v.text}</p>
          <div className="hero-stats">
            <div>
              <strong>{mustAll.length ? `${mustCovered}/${mustAll.length}` : "-"}</strong>
              <span>must-haves covered</span>
            </div>
            <div>
              <strong>{counts.covered}</strong>
              <span>covered</span>
            </div>
            <div>
              <strong>{counts.partial}</strong>
              <span>partial</span>
            </div>
            <div>
              <strong>{counts.missing}</strong>
              <span>missing</span>
            </div>
          </div>
        </div>
      </section>

      {/* Radar + breakdown */}
      <div className="grid-charts">
        <section className="card">
          <h2>Coverage by area</h2>
          <p className="muted small">
            The dashed outline is full coverage of what the job asks for. The filled shape is what your
            coursework covers. Numbers in brackets are requirements per area.
          </p>
          <ResponsiveContainer width="100%" height={340}>
            {radarData.length >= 3 ? (
              <RadarChart data={radarData} outerRadius="66%">
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis dataKey="label" tick={{ fill: "#334155", fontSize: 12 }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tickCount={5} tick={{ fill: "#94a3b8", fontSize: 10 }} />
                <Radar
                  name="Job demand"
                  dataKey="target"
                  stroke="#94a3b8"
                  strokeDasharray="5 5"
                  fill="none"
                />
                <Radar
                  name="Your coverage"
                  dataKey="coverage"
                  stroke="#6366f1"
                  strokeWidth={2}
                  fill="#6366f1"
                  fillOpacity={0.35}
                  dot
                />
                <Legend />
                <Tooltip content={<RadarTip />} />
              </RadarChart>
            ) : (
              <BarChart data={radarData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="label" />
                <YAxis domain={[0, 100]} />
                <Tooltip content={<RadarTip />} />
                <Bar dataKey="coverage" name="Your coverage %" fill="#6366f1" radius={[6, 6, 0, 0]} />
              </BarChart>
            )}
          </ResponsiveContainer>
        </section>

        <div className="stack">
          <section className="card">
            <h2>Status breakdown</h2>
            <div className="donut-wrap">
              <ResponsiveContainer width="100%" height={170}>
                <PieChart>
                  <Pie
                    data={pieData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={52}
                    outerRadius={76}
                    paddingAngle={3}
                    stroke="none"
                  >
                    {pieData.map((d) => (
                      <Cell key={d.name} fill={d.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="donut-center">
                <strong>{requirements.length}</strong>
                <span>requirements</span>
              </div>
            </div>
            <div className="legend">
              {["covered", "partial", "missing"].map((s) => (
                <span className="legend-item" key={s}>
                  <span className="dot" style={{ background: STATUS_COLOR[s] }} />
                  {STATUS_LABEL[s]} ({counts[s]})
                </span>
              ))}
            </div>
          </section>

          <section className="card">
            <h2>Top gaps to close</h2>
            {topGaps.length === 0 ? (
              <p className="muted">No gaps found. Nice work.</p>
            ) : (
              <ul className="gap-list">
                {topGaps.map((g) => (
                  <li key={g.requirement}>
                    <span className="dot" style={{ background: STATUS_COLOR[g.status] }} />
                    <span className="gap-name">{g.requirement}</span>
                    <span className={"tag " + (g.importance === "must_have" ? "must" : "nice")}>
                      {g.importance === "must_have" ? "Must-have" : "Nice-to-have"}
                    </span>
                  </li>
                ))}
              </ul>
            )}
            {onNavigate && (
              <button className="link" onClick={() => onNavigate("projects")}>
                See projects that close these gaps \u2192
              </button>
            )}
          </section>
        </div>
      </div>

      </>
      )}

      {section === "skills" && (
      <>
      {/* Skill by skill */}
      <section className="card">
        <h2>Skill by skill</h2>
        <p className="muted small">How well your coursework covers each requirement (0-100%).</p>
        <ResponsiveContainer width="100%" height={Math.max(220, barData.length * 34 + 40)}>
          <BarChart data={barData} layout="vertical" margin={{ left: 10, right: 36, top: 5, bottom: 5 }}>
            <CartesianGrid horizontal={false} stroke="#f1f5f9" />
            <XAxis type="number" domain={[0, 100]} tickFormatter={(t) => `${t}%`} tick={{ fill: "#94a3b8", fontSize: 11 }} />
            <YAxis type="category" dataKey="name" width={170} tick={<SkillTick byName={byName} />} />
            <Tooltip content={<BarTip />} cursor={{ fill: "#f8fafc" }} />
            <Bar dataKey="value" barSize={16} radius={[0, 6, 6, 0]} background={{ fill: "#f1f5f9", radius: 6 }}>
              {barData.map((d, i) => (
                <Cell key={i} fill={STATUS_COLOR[d.status]} />
              ))}
              <LabelList dataKey="value" position="right" formatter={(t) => `${t}%`} style={{ fontSize: 12, fill: "#64748b" }} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <div className="legend">
          {["covered", "partial", "missing"].map((s) => (
            <span className="legend-item" key={s}>
              <span className="dot" style={{ background: STATUS_COLOR[s] }} />
              {STATUS_LABEL[s]}
            </span>
          ))}
        </div>
      </section>

      {/* Details */}
      <section className="card">
        <div className="row-between">
          <h2>Requirement details</h2>
          <div className="tabs small">
            {["all", "missing", "partial", "covered"].map((f) => (
              <button
                key={f}
                className={filter === f ? "tab active" : "tab"}
                onClick={() => {
                  setFilter(f);
                  setOpen(null);
                }}
              >
                {f === "all" ? "All" : STATUS_LABEL[f]}
              </button>
            ))}
          </div>
        </div>

        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Requirement</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Your level</th>
                <th>Matched skill</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <Fragment key={r.requirement + i}>
                  <tr className="clickable" onClick={() => setOpen(open === i ? null : i)}>
                    <td>
                      <strong>{r.requirement}</strong>
                      <div className="muted small">{r.category}</div>
                    </td>
                    <td>{r.importance === "must_have" ? "Must-have" : "Nice-to-have"}</td>
                    <td>
                      <span className={"pill " + r.status}>{STATUS_LABEL[r.status]}</span>
                    </td>
                    <td>{r.student_level ? LEVEL_LABEL[r.student_level] : "-"}</td>
                    <td>
                      {r.matched_skill || "-"}
                      {r.relation === "related" && <span className="muted small"> (related)</span>}
                    </td>
                  </tr>
                  {open === i && (
                    <tr className="detail">
                      <td colSpan={5}>
                        <div className="detail-grid">
                          <div>
                            <div className="detail-label">What the job says</div>
                            <div>{r.job_evidence}</div>
                          </div>
                          <div>
                            <div className="detail-label">From your coursework</div>
                            <div>{r.student_evidence || "Nothing in your documents covers this."}</div>
                            {r.source_document && <div className="muted small">Source: {r.source_document}</div>}
                          </div>
                          <div>
                            <div className="detail-label">Why this status</div>
                            <div>{r.reason}</div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={5} className="muted">
                    Nothing in this category.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <p className="muted small">Click a row to see the evidence behind it.</p>
      </section>
      </>
      )}
    </div>
  );
}
