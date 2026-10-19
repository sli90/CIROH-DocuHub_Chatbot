import { formatDate, formatNumber } from "../lib/dashboard.js";
import { Icon } from "./Common.jsx";

const sourceMeta = {
  ciroh_hub: {
    description: "Documentation published from the main CIROH Hub repository.",
    icon: "docs",
    tone: "blue",
  },
  github_repositories: {
    description: "Artifacts and selected content from CIROH GitHub repositories.",
    icon: "github",
    tone: "purple",
  },
  hydroshare: {
    description: "Research resources discovered through the CIROH HydroShare portals.",
    icon: "hydroshare",
    tone: "green",
  },
};

const statusMeta = {
  completed: { label: "Synced", tone: "ready" },
  success: { label: "Synced", tone: "ready" },
  synced: { label: "Synced", tone: "ready" },
  current: { label: "Synced", tone: "ready" },
  running: { label: "Synchronizing", tone: "running" },
  syncing: { label: "Synchronizing", tone: "running" },
  partial: { label: "Partially synced", tone: "warning" },
  failed: { label: "Needs attention", tone: "error" },
  error: { label: "Needs attention", tone: "error" },
  not_synced: { label: "Not synchronized", tone: "idle" },
  unavailable: { label: "Unavailable", tone: "idle" },
};

const displayStatus = (status, loading, unavailable) => {
  if (loading) return { label: "Loading", tone: "loading" };
  if (unavailable) return statusMeta.unavailable;
  return statusMeta[String(status || "not_synced").toLowerCase()] || {
    label: String(status || "Unknown").replaceAll("_", " "),
    tone: "idle",
  };
};

const displayMetric = (value, unavailable) => unavailable ? "—" : formatNumber(value);

function SourceCard({ source, loading, unavailable, identifier }) {
  const meta = sourceMeta[source.key] || sourceMeta.ciroh_hub;
  const state = displayStatus(source.status, loading, unavailable);
  const changeCount = Number(source.new_count || 0)
    + Number(source.updated_count || 0)
    + Number(source.removed_count || 0);
  const lastSync = loading
    ? "Checking latest run…"
    : unavailable
      ? "Status could not be loaded"
      : source.last_synced_at
        ? formatDate(source.last_synced_at)
        : "No completed run recorded";

  return (
    <article className={`source-card source-tone-${meta.tone}`} aria-label={`${source.label} synchronization status`}>
      <div className="source-card-header">
        <div className="source-identity">
          <span className="source-icon"><Icon name={meta.icon} size={20} /></span>
          <div>
            <h3>{source.label}</h3>
            <span className="artifact-type">Artifact type {source.artifact_type_id}</span>
          </div>
        </div>
        <span className={`source-state source-state-${state.tone}`}>
          <span className="status-dot" aria-hidden="true" />
          {state.label}
        </span>
      </div>

      <p className="source-description">{meta.description}</p>
      {identifier && <code className="source-identifier">{identifier}</code>}

      <dl className="source-metrics">
        <div><dt>Artifacts</dt><dd>{displayMetric(source.artifacts, loading || unavailable)}</dd></div>
        <div><dt>Chunks</dt><dd>{displayMetric(source.chunks, loading || unavailable)}</dd></div>
        <div><dt>Changes</dt><dd>{displayMetric(changeCount, loading || unavailable)}</dd></div>
      </dl>

      <div className="source-change-breakdown" aria-label="Latest synchronization changes">
        <span><strong>{displayMetric(source.new_count, loading || unavailable)}</strong> new</span>
        <span><strong>{displayMetric(source.updated_count, loading || unavailable)}</strong> updated</span>
        <span><strong>{displayMetric(source.removed_count, loading || unavailable)}</strong> removed</span>
      </div>

      <div className="source-card-footer">
        <div className="source-last-sync"><span>Last synchronization</span><strong>{lastSync}</strong></div>
        <span className={`source-mode ${source.optional ? "optional" : "always-on"}`}>
          {source.optional ? "Optional source" : "Always included"}
        </span>
      </div>
    </article>
  );
}

export default function SourceStatus({ items, loading, error, unavailable, hubRepository, onRetry }) {
  return (
    <section id="source-status" className="panel source-status-panel" aria-labelledby="source-status-title" aria-busy={loading}>
      <div className="section-header">
        <div>
          <div className="eyebrow">Synchronization coverage</div>
          <h2 id="source-status-title">Data sources</h2>
          <p>Latest recorded synchronization coverage and changes for each source.</p>
        </div>
        <div className="source-legend" aria-label="Source inclusion modes">
          <span><i className="legend-dot always-on" />Always included</span>
          <span><i className="legend-dot optional" />Optional per run</span>
        </div>
      </div>

      {error && (
        <div className="source-status-error" role="status">
          <span>{error} The rest of the dashboard is still available.</span>
          <button className="text-button" type="button" onClick={onRetry}>Try again</button>
        </div>
      )}

      <div className="source-card-grid">
        {items.map((source) => (
          <SourceCard
            key={source.key}
            source={source}
            loading={loading}
            unavailable={unavailable}
            identifier={source.key === "ciroh_hub" ? (hubRepository || "CIROH-UA/ciroh_hub") : null}
          />
        ))}
      </div>
    </section>
  );
}
