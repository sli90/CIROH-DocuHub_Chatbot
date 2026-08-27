import { useMemo, useState } from "react";
import { formatDate, formatNumber, formatSeconds } from "../lib/dashboard.js";
import { Icon, SearchField } from "./Common.jsx";

export default function SyncHistory({ items, loading, error, onRefresh, onSelect }) {
  const [status, setStatus] = useState("all");
  const [query, setQuery] = useState("");
  const visibleItems = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return items.filter((item) => {
      if (status !== "all" && item.status !== status) return false;
      if (!needle) return true;
      return [item.sync_id, item.mode, item.failed_step, item.error].some((value) => String(value || "").toLowerCase().includes(needle));
    });
  }, [items, query, status]);

  return (
    <section id="history" className="panel" aria-labelledby="history-title">
      <div className="section-header">
        <div><div className="eyebrow">Operational records</div><h2 id="history-title">Synchronization history</h2><p>Review prior status, duration, token use, cost, and failure details.</p></div>
        <button className="button button-secondary" type="button" onClick={onRefresh} disabled={loading}><span className={loading ? "spin" : ""}><Icon name="refresh" /></span>{loading ? "Refreshing" : "Refresh history"}</button>
      </div>

      <div className="data-toolbar">
        <SearchField label="Search synchronization history" placeholder="Search by run ID, mode, or failure…" value={query} onChange={setQuery} />
        <label className="select-field"><span>Status</span><select value={status} onChange={(event) => setStatus(event.target.value)}><option value="all">All statuses</option><option value="completed">Completed</option><option value="failed">Failed</option></select></label>
      </div>

      {error && <div className="notice notice-warning">{error}</div>}
      <div className="table-wrap">
        <table className="data-table history-table">
          <caption className="sr-only">Synchronization history</caption>
          <thead><tr><th>Status</th><th>Completed</th><th>Duration</th><th>Artifacts</th><th>Tokens</th><th>Est. cost</th><th><span className="sr-only">Actions</span></th></tr></thead>
          <tbody>
            {visibleItems.length === 0 ? <tr><td colSpan="7"><div className="empty-state">{loading ? "Loading synchronization history…" : items.length ? "No runs match these filters." : "No synchronization reports are available yet."}</div></td></tr>
              : visibleItems.map((item) => (
                <tr key={item.sync_id}>
                  <td><span className={`run-status ${item.status}`}>{item.status}</span></td>
                  <td><div className="run-id-cell"><strong>{formatDate(item.completed_at || item.started_at)}</strong><code>{item.sync_id}</code></div></td>
                  <td>{formatSeconds(item.duration_seconds)}</td>
                  <td>{formatNumber(item.total_artifacts)}</td>
                  <td>{formatNumber(item.openai_tokens)}</td>
                  <td>{item.estimated_cost_usd == null ? "—" : `$${Number(item.estimated_cost_usd).toFixed(4)}`}</td>
                  <td><button className="table-action" type="button" onClick={() => onSelect({ ...item, duration_label: formatSeconds(item.duration_seconds) })}>View details</button></td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
      <p className="section-note">These records come from immutable operational synchronization reports.</p>
    </section>
  );
}
