function Icon({ name }) {
  const props = {
    width: 18,
    height: 18,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round",
    strokeLinejoin: "round",
  };
  const shapes = {
    plus: <path d="M12 5v14M5 12h14" />,
    grid: <path d="M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z" />,
    list: <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />,
    bulb: <path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.2 1 2V17h6v-.3c0-.8.4-1.5 1-2A7 7 0 0 0 12 2z" />,
    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),
  };
  return <svg {...props}>{shapes[name]}</svg>;
}

const ITEMS = [
  { id: "upload", label: "New analysis", icon: "plus", needsResult: false },
  { id: "overview", label: "Overview", icon: "grid", needsResult: true },
  { id: "skills", label: "Skills & gaps", icon: "list", needsResult: true },
  { id: "projects", label: "Projects", icon: "bulb", needsResult: true },
  { id: "history", label: "History", icon: "clock", needsResult: false },
];

export default function Sidebar({ view, onNavigate, hasResult, running, score, recsStatus, recsCount, online }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="logo">CG</span>
        <span>Career Gap Analyzer</span>
      </div>

      <nav className="nav">
        {ITEMS.map((item) => {
          const active = view === item.id || (view === "running" && item.id === "upload");
          const disabled = running || (item.needsResult && !hasResult);
          return (
            <button
              key={item.id}
              className={"nav-item" + (active ? " active" : "")}
              disabled={disabled}
              onClick={() => onNavigate(item.id)}
            >
              <Icon name={item.icon} />
              <span className="nav-label">{item.label}</span>
              {item.id === "projects" && hasResult && recsStatus === "loading" && (
                <span className="spinner light" />
              )}
              {item.id === "projects" && hasResult && recsStatus === "done" && recsCount > 0 && (
                <span className="nav-badge">{recsCount}</span>
              )}
              {item.id === "projects" && hasResult && recsStatus === "error" && (
                <span className="nav-badge warn">!</span>
              )}
            </button>
          );
        })}
      </nav>

      {hasResult && score !== null && (
        <div className="side-score">
          <span>Current match</span>
          <strong>{Math.round(score)}</strong>
        </div>
      )}

      <div className="side-footer">
        <span
          className="status-dot"
          style={{ background: online === null ? "#94a3b8" : online ? "#34d399" : "#f87171" }}
        />
        {online === null ? "Checking backend..." : online ? "Backend online" : "Backend offline"}
      </div>
    </aside>
  );
}
