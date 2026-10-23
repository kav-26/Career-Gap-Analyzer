export default function Progress({ steps, progress, error, onBack }) {
  function stateOf(i) {
    if (error && error.step === i) return "error";
    if (i < progress.step) return "done";
    if (i === progress.step) return progress.state === "done" ? "done" : "active";
    return "pending";
  }

  return (
    <div className="card narrow">
      <h2>{error ? "Something went wrong" : "Analyzing..."}</h2>
      {!error && (
        <p className="muted">This can take a minute or two, since the AI reads every document.</p>
      )}
      <ul className="steps">
        {steps.map((label, i) => {
          const s = stateOf(i);
          return (
            <li key={label} className={"step " + s}>
              <span className="icon">
                {s === "done" && "\u2713"}
                {s === "error" && "\u2715"}
                {s === "pending" && "\u25CB"}
                {s === "active" && <span className="spinner" />}
              </span>
              <div>
                <div>{label}</div>
                {s === "active" && progress.note && <div className="muted small">{progress.note}</div>}
              </div>
            </li>
          );
        })}
      </ul>
      {error && (
        <div>
          <p className="error">{error.message}</p>
          <button className="btn primary" onClick={onBack}>
            Back to upload
          </button>
        </div>
      )}
    </div>
  );
}
