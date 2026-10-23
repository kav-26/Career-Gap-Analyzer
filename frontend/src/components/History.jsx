import { useEffect, useState } from "react";
import { listAnalyses, listDocuments, errorMessage } from "../api.js";

function formatDate(iso) {
  const withZone = /Z|[+-]\d\d:?\d\d$/.test(iso) ? iso : iso + "Z";
  const d = new Date(withZone);
  return isNaN(d.getTime()) ? iso : d.toLocaleString();
}

export default function History({ onOpen }) {
  const [items, setItems] = useState(null);
  const [error, setError] = useState(null);
  const [busyId, setBusyId] = useState(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [analyses, docs] = await Promise.all([listAnalyses(), listDocuments()]);
        const names = Object.fromEntries(docs.map((d) => [d.id, d.filename]));
        if (alive) {
          setItems(
            analyses.map((a) => ({
              ...a,
              jobName: names[a.job_document_id] || `Job #${a.job_document_id}`,
            }))
          );
        }
      } catch (e) {
        if (alive) setError(errorMessage(e));
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  async function open(item) {
    setBusyId(item.analysis_id);
    setError(null);
    try {
      await onOpen(item);
    } catch (e) {
      setError(errorMessage(e));
      setBusyId(null);
    }
  }

  if (error && !items) return <div className="error">{error}</div>;
  if (!items) return <div className="card center"><span className="spinner big" /></div>;
  if (items.length === 0) {
    return <div className="card center muted">No analyses yet. Run one from "New analysis".</div>;
  }

  return (
    <div>
      {error && <div className="error">{error}</div>}
      {items.map((item) => (
        <div className="card history-item" key={item.analysis_id}>
          <div className="history-score">{Math.round(item.match_score)}</div>
          <div className="history-info">
            <strong>{item.jobName}</strong>
            <div className="muted small">
              Analysis #{item.analysis_id} - {formatDate(item.created_at)}
            </div>
          </div>
          <button className="btn ghost" disabled={busyId === item.analysis_id} onClick={() => open(item)}>
            {busyId === item.analysis_id ? "Opening..." : "Open"}
          </button>
        </div>
      ))}
    </div>
  );
}
