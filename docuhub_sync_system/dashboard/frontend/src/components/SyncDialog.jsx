import { useEffect, useRef, useState } from "react";
import { formatDate, formatNumber } from "../lib/dashboard.js";
import { Icon } from "./Common.jsx";

export function SyncConfirmationDialog({ open, operatorMode, onCancel, onConfirm }) {
  const [operatorKey, setOperatorKey] = useState("");
  const cancelRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    cancelRef.current?.focus();
    const onKeyDown = (event) => { if (event.key === "Escape") onCancel(); };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onCancel]);

  if (!open) return null;
  const tokenRequired = operatorMode === "token";

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onCancel(); }}>
      <section className="modal-card confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="confirm-sync-title">
        <button className="modal-close" type="button" aria-label="Close confirmation" onClick={onCancel}><Icon name="close" /></button>
        <div className="modal-icon warning"><Icon name="alert" size={22} /></div>
        <div className="eyebrow">Confirm operation</div>
        <h2 id="confirm-sync-title">Run the complete synchronization?</h2>
        <p>This will pull repository changes, download external content, regenerate artifacts, call OpenAI when required, and update the database.</p>
        <ul className="confirmation-list">
          <li>The operation may take several minutes.</li>
          <li>Token usage and estimated cost will be recorded in the run report.</li>
          <li>A failed prerequisite will stop its dependent steps.</li>
        </ul>
        <label className="field-label" htmlFor="operator-key">
          Operator key {tokenRequired ? <strong>Required</strong> : <span>Not required for local use</span>}
        </label>
        <input id="operator-key" className="text-input" type="password" autoComplete="off" value={operatorKey} onChange={(event) => setOperatorKey(event.target.value)} placeholder={tokenRequired ? "Enter the configured operator key" : "Optional"} />
        <div className="modal-actions">
          <button ref={cancelRef} className="button button-secondary" type="button" onClick={onCancel}>Cancel</button>
          <button className="button button-primary" type="button" onClick={() => onConfirm(operatorKey)} disabled={tokenRequired && !operatorKey.trim()}><Icon name="play" /> Run synchronization</button>
        </div>
      </section>
    </div>
  );
}

export function SyncDetailDialog({ run, detail, loading, error, onClose }) {
  useEffect(() => {
    if (!run) return undefined;
    const onKeyDown = (event) => { if (event.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [run, onClose]);

  if (!run) return null;
  const content = detail?.content || {};
  const usage = detail?.openai_usage || {};
  const database = detail?.database || {};
  const metadata = detail?.metadata || {};

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section className="modal-card run-detail-dialog" role="dialog" aria-modal="true" aria-labelledby="run-detail-title">
        <button className="modal-close" type="button" aria-label="Close run details" onClick={onClose}><Icon name="close" /></button>
        <div className="eyebrow">Synchronization report</div>
        <div className="detail-title-row"><h2 id="run-detail-title">Run {run.sync_id}</h2><span className={`run-status ${run.status}`}>{run.status}</span></div>
        {loading && <div className="empty-state">Loading the complete report…</div>}
        {error && <div className="notice notice-warning">{error}</div>}
        {detail && (
          <>
            <dl className="detail-grid">
              <div><dt>Started</dt><dd>{formatDate(run.started_at)}</dd></div>
              <div><dt>Completed</dt><dd>{formatDate(run.completed_at)}</dd></div>
              <div><dt>Duration</dt><dd>{run.duration_label}</dd></div>
              <div><dt>Mode</dt><dd>{detail.mode || "Not available"}</dd></div>
            </dl>
            {detail.error && <div className="run-error-detail"><strong>{metadata.failed_label || "Synchronization failed"}</strong><span>{detail.error}</span></div>}
            <div className="detail-section"><h3>Content</h3><dl className="detail-metrics"><div><dt>Artifacts</dt><dd>{formatNumber(content.total_artifacts)}</dd></div><div><dt>New</dt><dd>{formatNumber(content.new_count)}</dd></div><div><dt>Updated</dt><dd>{formatNumber(content.updated_count)}</dd></div><div><dt>Deleted</dt><dd>{formatNumber(content.deleted_count)}</dd></div><div><dt>Chunks</dt><dd>{formatNumber(content.total_chunks)}</dd></div></dl></div>
            <div className="detail-section"><h3>OpenAI usage</h3><dl className="detail-metrics"><div><dt>Input</dt><dd>{formatNumber(usage.input_tokens)}</dd></div><div><dt>Cached input</dt><dd>{formatNumber(usage.cached_input_tokens)}</dd></div><div><dt>Output</dt><dd>{formatNumber(usage.output_tokens)}</dd></div><div><dt>Total tokens</dt><dd>{formatNumber(usage.total_tokens)}</dd></div><div><dt>Estimated cost</dt><dd>{usage.estimated_cost_usd == null ? "Unavailable" : `$${Number(usage.estimated_cost_usd).toFixed(4)}`}</dd></div></dl></div>
            {Object.keys(database).length > 0 && <div className="detail-section"><h3>Database</h3><dl className="detail-metrics"><div><dt>Upserted</dt><dd>{formatNumber(database.upserted_artifacts)}</dd></div><div><dt>Deactivated</dt><dd>{formatNumber(database.deactivated_artifacts)}</dd></div><div><dt>Chunks inserted</dt><dd>{formatNumber(database.chunks_inserted)}</dd></div></dl></div>}
            <div className="detail-section"><h3>Completed steps</h3><div className="step-list">{(metadata.completed_steps || []).length ? metadata.completed_steps.map((step) => <code key={step}>{step}</code>) : <span className="muted-text">No completed steps recorded.</span>}</div></div>
          </>
        )}
      </section>
    </div>
  );
}
