import { useCallback, useEffect, useMemo, useState } from "react";
import AttentionPanel from "./components/AttentionPanel.jsx";
import { Icon, MetricCard } from "./components/Common.jsx";
import ExternalSources from "./components/ExternalSources.jsx";
import RepositoryChanges from "./components/RepositoryChanges.jsx";
import { SyncConfirmationDialog, SyncDetailDialog } from "./components/SyncDialog.jsx";
import SyncHistory from "./components/SyncHistory.jsx";
import {
  API_BASE, emptyExternal, emptySummary, formatDate, formatDateShort,
  formatDuration, formatNumber, formatSeconds, freshnessLabel, shortSha, signalLabel
} from "./lib/dashboard.js";

export default function DashboardApp() {
  const [summary, setSummary] = useState(emptySummary);
  const [externalInfo, setExternalInfo] = useState(emptyExternal);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [lastLoadedAt, setLastLoadedAt] = useState(null);
  const [operatorMode, setOperatorMode] = useState("local_only");

  const [selectedType, setSelectedType] = useState(null);
  const [typeFiles, setTypeFiles] = useState({});
  const [typeFilesLoading, setTypeFilesLoading] = useState(false);
  const [typeFilesError, setTypeFilesError] = useState("");
  const [filesPage, setFilesPage] = useState(1);

  const [pipelineStarting, setPipelineStarting] = useState(false);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [pipelineStep, setPipelineStep] = useState(0);
  const [pipelineTotal, setPipelineTotal] = useState(6);
  const [pipelineLabel, setPipelineLabel] = useState("");
  const [pipelineError, setPipelineError] = useState("");
  const [pipelineResult, setPipelineResult] = useState(null);
  const [confirmationOpen, setConfirmationOpen] = useState(false);

  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState("");
  const [selectedRun, setSelectedRun] = useState(null);
  const [selectedRunDetail, setSelectedRunDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    setHistoryError("");
    try {
      const response = await fetch(`${API_BASE}/api/synchronizations?limit=50`, { cache: "no-store" });
      if (!response.ok) throw new Error("History endpoint unavailable");
      const data = await response.json();
      setHistory(data.items || []);
    } catch {
      setHistoryError("Synchronization history could not be loaded.");
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  const load = useCallback(async ({ initial = false, silent = false } = {}) => {
    if (initial) setIsLoading(true);
    if (!initial && !silent) setIsRefreshing(true);
    if (!silent) setLoadError("");
    try {
      const [summaryResult, externalResult, healthResult] = await Promise.allSettled([
        fetch(`${API_BASE}/api/summary`, { cache: "no-store" }).then((response) => { if (!response.ok) throw new Error(); return response.json(); }),
        fetch(`${API_BASE}/api/external`, { cache: "no-store" }).then((response) => { if (!response.ok) throw new Error(); return response.json(); }),
        fetch(`${API_BASE}/api/health`, { cache: "no-store" }).then((response) => { if (!response.ok) throw new Error(); return response.json(); })
      ]);
      if (summaryResult.status === "rejected") throw summaryResult.reason;
      setSummary(summaryResult.value);
      if (externalResult.status === "fulfilled") setExternalInfo(externalResult.value);
      else { setExternalInfo(emptyExternal); setLoadError("Repository data loaded, but external source data is unavailable."); }
      if (healthResult.status === "fulfilled") setOperatorMode(healthResult.value.operator_mode || "local_only");
      setLastLoadedAt(new Date());
    } catch {
      setLoadError("The dashboard API is unavailable. Check the backend service and try again.");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load({ initial: true });
    loadHistory();
    let active = true;
    fetch(`${API_BASE}/api/pipeline-status`, { cache: "no-store" })
      .then((response) => response.ok ? response.json() : null)
      .then((data) => {
        if (!active || !data) return;
        setPipelineRunning(Boolean(data.running));
        setPipelineStep(data.step || 0);
        setPipelineTotal(data.total || 6);
        setPipelineLabel(data.label || "");
        setPipelineError(data.error || "");
        setPipelineResult(data.result || null);
      }).catch(() => {});
    return () => { active = false; };
  }, [load, loadHistory]);

  useEffect(() => {
    if (!pipelineRunning) return undefined;
    let active = true;
    const checkStatus = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/pipeline-status`, { cache: "no-store" });
        if (!response.ok) throw new Error();
        const data = await response.json();
        if (!active) return;
        setPipelineStep(data.step || 0);
        setPipelineTotal(data.total || 6);
        setPipelineLabel(data.label || "");
        if (!data.running) {
          setPipelineRunning(false);
          setPipelineError(data.error || "");
          setPipelineResult(data.result || null);
          load({ silent: true });
          loadHistory();
        }
      } catch {
        if (!active) return;
        setPipelineRunning(false);
        setPipelineError("Lost connection to the backend while checking synchronization status.");
      }
    };
    checkStatus();
    const interval = window.setInterval(checkStatus, 2000);
    return () => { active = false; window.clearInterval(interval); };
  }, [pipelineRunning, load, loadHistory]);

  const score = summary.metrics?.signal_score ?? 0;
  const freshness = summary.metrics?.freshness_hours ?? null;
  const changedCount = summary.changes?.changed_files_count ?? 0;
  const externalFiles = externalInfo.rendered_files || [];
  const statsRows = summary.file_stats?.table?.rows || [];
  const selectedRow = statsRows.find((row) => row.key === selectedType) || null;
  const selectedFiles = selectedType ? typeFiles[selectedType] || [] : [];
  const deletedFiles = (summary.changes?.changed_files || []).filter((file) => (file.status || "").toLowerCase() === "removed");
  const externalChanged = externalFiles.filter((file) => file.change_state === "changed").length;
  const externalUnknown = externalFiles.filter((file) => (file.change_state || "unknown") === "unknown").length;
  const pipelineActive = pipelineStarting || pipelineRunning;
  const pipelinePercent = pipelineStarting ? 4 : Math.min(100, Math.round((pipelineStep / Math.max(1, pipelineTotal)) * 100));
  const topPath = summary.top_paths?.[0];

  const attentionItems = useMemo(() => {
    const items = [];
    if (pipelineError) items.push({ key: "pipeline-error", tone: "critical", title: "The latest synchronization failed", detail: pipelineResult?.failed_label || pipelineError, target: "#history" });
    else if (history[0]?.status === "failed") items.push({ key: "history-failed", tone: "critical", title: "The latest recorded run failed", detail: history[0].failed_label || "Open the report for failure details.", target: "#history" });
    if (loadError) items.push({ key: "data-error", tone: "critical", title: "Dashboard data is incomplete", detail: loadError, target: "#top" });
    if (freshness != null && freshness >= 72) items.push({ key: "stale", tone: "warning", title: "Repository signal is stale", detail: `${formatDuration(freshness)} since the latest commit.`, target: "#top" });
    if (deletedFiles.length) items.push({ key: "deleted", tone: "warning", title: `${deletedFiles.length} deleted ${deletedFiles.length === 1 ? "file" : "files"}`, detail: "Review removed paths in the current comparison.", target: "#changes" });
    if (externalChanged) items.push({ key: "external-changed", tone: "info", title: `${externalChanged} changed external ${externalChanged === 1 ? "source" : "sources"}`, detail: "Review upstream README updates before publishing.", target: "#external-sources" });
    if (externalUnknown) items.push({ key: "external-unknown", tone: "warning", title: `${externalUnknown} sources with unknown status`, detail: "These sources could not be classified during the latest check.", target: "#external-sources" });
    return items;
  }, [deletedFiles.length, externalChanged, externalUnknown, freshness, history, loadError, pipelineError, pipelineResult]);

  const handleTypeClick = async (row) => {
    if (!row?.key || row.key === "total" || row.key === "external_md") return;
    if (selectedType === row.key) { setSelectedType(null); return; }
    setSelectedType(row.key);
    setFilesPage(1);
    setTypeFilesError("");
    if (typeFiles[row.key]) return;
    setTypeFilesLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/file-type?key=${encodeURIComponent(row.key)}`, { cache: "no-store" });
      if (!response.ok) throw new Error();
      const data = await response.json();
      setTypeFiles((current) => ({ ...current, [row.key]: data.files || [] }));
    } catch { setTypeFilesError("Could not load files for this type."); }
    finally { setTypeFilesLoading(false); }
  };

  const startSynchronization = async (operatorKey, options = {}) => {
    const includeGitHubRepositories = Boolean(options.includeGitHubRepositories);
    setConfirmationOpen(false);
    setPipelineStarting(true);
    setPipelineError("");
    setPipelineResult(null);
    setPipelineStep(0);
    setPipelineTotal(includeGitHubRepositories ? 8 : 6);
    setPipelineLabel("Starting synchronization");
    try {
      const headers = operatorKey?.trim() ? { "X-CIROH-Operator-Key": operatorKey.trim() } : {};
      const query = includeGitHubRepositories ? "?include_github_repositories=true" : "";
      const response = await fetch(`${API_BASE}/api/run-pipeline${query}`, { method: "POST", cache: "no-store", headers });
      const payload = await response.json().catch(() => ({}));
      if (response.status !== 409 && !response.ok) throw new Error(payload.detail || "Start request failed");
      setPipelineRunning(true);
      if (response.status === 409) setPipelineLabel("Synchronization already running");
    } catch (error) {
      setPipelineError(error.message || "Could not start synchronization. Check the backend logs and try again.");
    } finally { setPipelineStarting(false); }
  };

  const openRunDetail = useCallback(async (run) => {
    setSelectedRun(run);
    setSelectedRunDetail(null);
    setDetailError("");
    setDetailLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/synchronizations/${encodeURIComponent(run.sync_id)}`, { cache: "no-store" });
      if (!response.ok) throw new Error();
      setSelectedRunDetail(await response.json());
    } catch { setDetailError("The complete synchronization report could not be loaded."); }
    finally { setDetailLoading(false); }
  }, []);
  const closeRunDetail = useCallback(() => { setSelectedRun(null); setSelectedRunDetail(null); setDetailError(""); }, []);
  const closeConfirmation = useCallback(() => setConfirmationOpen(false), []);

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="CIROH Sync Console home"><span className="brand-mark" aria-hidden="true"><span /></span><span><strong>CIROH</strong><small>Sync Console</small></span></a>
        <nav className="section-nav" aria-label="Dashboard sections"><a href="#changes">Changes</a><a href="#history">History</a><a href="#external-sources">External sources</a></nav>
        <div className="topbar-actions"><span className={`freshness-badge ${freshnessLabel(freshness).toLowerCase()}`}><span className="status-dot" />{freshnessLabel(freshness)}</span><button className="button button-secondary" type="button" onClick={() => { load(); loadHistory(); }} disabled={isRefreshing}><span className={isRefreshing ? "spin" : ""}><Icon name="refresh" /></span>{isRefreshing ? "Refreshing" : "Refresh data"}</button></div>
      </header>

      <main id="top" className="main" aria-busy={isLoading || isRefreshing}>
        {loadError && <div className="notice notice-warning" role="alert"><div><strong>Some dashboard data could not be loaded.</strong><span>{loadError}</span></div><button className="text-button" type="button" onClick={() => load()}>Try again</button></div>}

        <section className="command-card" aria-labelledby="page-title">
          <div className="command-copy"><div className="eyebrow">Repository operations</div><h1 id="page-title">Documentation sync, at a glance.</h1><p>Review repository changes, inspect external README sources, and run the complete DocuHub synchronization from one place.</p><div className="repository-meta"><span><Icon name="branch" size={16} /> <code>{summary.changes?.repo || "Repository unavailable"}</code></span><span><Icon name="clock" size={16} /> Checked {formatDate(summary.changes?.last_checked)}</span></div><div className="command-actions"><button className="button button-primary" type="button" onClick={() => setConfirmationOpen(true)} disabled={pipelineActive}><Icon name="play" />{pipelineStarting ? "Starting…" : pipelineRunning ? "Synchronization running" : "Run synchronization"}</button><span className="command-hint">{operatorMode === "token" ? "Operator key protected" : "Local-only execution"} · {pipelineTotal || 6} steps</span></div></div>
          <div className="activity-card"><div className="activity-header"><span>Change activity <button className="info-tip" type="button" title="Derived from change volume and commit freshness. This is not a quality score." aria-label="About the change activity score">?</button></span><strong>{signalLabel(score)}</strong></div><div className="activity-score-row"><div className="score-ring" style={{ "--score": Math.min(100, Math.max(0, score)) }}><span>{score}</span></div><div className="activity-summary"><strong>{formatNumber(changedCount)} files changed</strong><span>{formatDuration(freshness)} since the latest commit</span></div></div><div className="commit-message"><span>Latest commit</span><p>{summary.changes?.latest_commit_message || "No commit message available."}</p></div></div>
          {(pipelineActive || pipelineError || pipelineResult) && <div className="sync-status" aria-live="polite">{pipelineActive && <><div className="sync-status-head"><div><strong>{pipelineStarting ? "Starting synchronization" : pipelineLabel || "Synchronization running"}</strong><span>{pipelineStarting ? "Preparing the pipeline" : `Step ${pipelineStep} of ${pipelineTotal}`}</span></div><strong>{pipelinePercent}%</strong></div><div className="progress-track" role="progressbar" aria-label="Synchronization progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow={pipelinePercent}><span style={{ width: `${pipelinePercent}%` }} /></div></>}{pipelineError && <div className="sync-message error-message"><div><strong>Synchronization failed</strong><span>{pipelineResult?.failed_label || pipelineError}</span></div><div className="inline-actions"><button className="text-button" type="button" onClick={() => setConfirmationOpen(true)}>Retry</button>{pipelineResult?.sync_id && <button className="text-button" type="button" onClick={() => openRunDetail({ ...pipelineResult, duration_label: formatSeconds(pipelineResult.duration_seconds) })}>View details</button>}</div></div>}{pipelineResult && !pipelineActive && !pipelineError && <div className="sync-result"><div><strong>Synchronization complete</strong><span>{pipelineResult.sync_id} · {formatSeconds(pipelineResult.duration_seconds)}</span></div><dl><div><dt>Artifacts</dt><dd>{formatNumber(pipelineResult.total_artifacts)}</dd></div><div><dt>New</dt><dd>{formatNumber(pipelineResult.new_count)}</dd></div><div><dt>Updated</dt><dd>{formatNumber(pipelineResult.updated_count)}</dd></div><div><dt>Tokens</dt><dd>{formatNumber(pipelineResult.openai_tokens)}</dd></div><div><dt>Est. cost</dt><dd>{pipelineResult.estimated_cost_usd == null ? "—" : `$${Number(pipelineResult.estimated_cost_usd).toFixed(4)}`}</dd></div></dl>{pipelineResult.sync_id && <button className="table-action" type="button" onClick={() => openRunDetail({ ...pipelineResult, duration_label: formatSeconds(pipelineResult.duration_seconds) })}>View report</button>}</div>}</div>}
        </section>

        <section className="metric-grid" aria-label="Repository summary"><MetricCard icon="chart" label="Changed files" value={formatNumber(changedCount)} detail={`${summary.status_counts?.added ?? 0} added · ${summary.status_counts?.removed ?? 0} removed`} tone="blue" /><MetricCard icon="branch" label="Latest commit" value={shortSha(summary.changes?.latest_sha)} detail={formatDateShort(summary.changes?.latest_commit_date)} tone="purple" /><MetricCard icon="external" label="External sources" value={formatNumber(externalInfo.total_repos ?? Object.keys(externalInfo.repos || {}).length)} detail={`${formatNumber(externalFiles.length)} tracked README files`} tone="green" /><MetricCard icon="folder" label="Most active area" value={topPath?.path || "No changes"} detail={topPath ? `${formatNumber(topPath.count)} changed files` : `${summary.metrics?.cadence || "Weekly"} reporting cadence`} tone="amber" /></section>

        <AttentionPanel items={attentionItems} />
        <RepositoryChanges summary={summary} selectedType={selectedType} selectedRow={selectedRow} selectedFiles={selectedFiles} typeFilesLoading={typeFilesLoading} typeFilesError={typeFilesError} filesPage={filesPage} onFilesPage={setFilesPage} onTypeClick={handleTypeClick} onCloseType={() => setSelectedType(null)} />
        <SyncHistory items={history} loading={historyLoading} error={historyError} onRefresh={loadHistory} onSelect={openRunDetail} />
        <ExternalSources externalInfo={externalInfo} loading={isLoading} />
      </main>

      <footer className="footer"><div><strong>CIROH Sync Console</strong><span>University of Alabama SAIL Lab</span></div><span>{lastLoadedAt ? `Dashboard refreshed ${formatDate(lastLoadedAt)}` : "Waiting for dashboard data"}</span></footer>
      <SyncConfirmationDialog open={confirmationOpen} operatorMode={operatorMode} onCancel={closeConfirmation} onConfirm={startSynchronization} />
      <SyncDetailDialog run={selectedRun} detail={selectedRunDetail} loading={detailLoading} error={detailError} onClose={closeRunDetail} />
    </div>
  );
}
