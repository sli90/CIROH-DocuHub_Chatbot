import { useEffect, useMemo, useState } from "react";
import { fileTypeForPath, formatDate, formatDateShort, formatNumber } from "../lib/dashboard.js";
import { Icon, Pager, SearchField } from "./Common.jsx";

const TYPE_LABELS = {
  all: "All types", md: "Markdown", mdx: "MDX", images: "Images",
  page_components: "Page components", yml: "YAML", other: "Other"
};

export default function RepositoryChanges({ summary, selectedType, selectedRow, selectedFiles, typeFilesLoading, typeFilesError, filesPage, onFilesPage, onTypeClick, onCloseType }) {
  const [changeQuery, setChangeQuery] = useState("");
  const [changeStatus, setChangeStatus] = useState("all");
  const [changeType, setChangeType] = useState("all");
  const [fileQuery, setFileQuery] = useState("");
  const [fileSort, setFileSort] = useState("asc");
  const filesPageSize = 10;
  const fileStats = summary.file_stats || {};
  const statsProfile = fileStats.profile || {};
  const changeProfile = fileStats.change_profile || {};
  const changeByType = changeProfile.by_type || {};
  const statsRows = fileStats.table?.rows || [];
  const statsWindows = fileStats.windows || {};
  const changedFiles = summary.changes?.changed_files || [];
  const totalChanges = changeProfile.total_changes ?? summary.changes?.changed_files_count ?? 0;

  const statusItems = useMemo(() => [
    { key: "added", label: "Added", count: summary.status_counts?.added ?? 0 },
    { key: "modified", label: "Modified", count: summary.status_counts?.modified ?? 0 },
    { key: "removed", label: "Removed", count: summary.status_counts?.removed ?? 0 },
    { key: "renamed", label: "Renamed", count: summary.status_counts?.renamed ?? 0 },
    { key: "other", label: "Other", count: summary.status_counts?.other ?? 0 }
  ], [summary.status_counts]);
  const statusTotal = statusItems.reduce((total, item) => total + item.count, 0);

  const visibleChanges = useMemo(() => {
    const needle = changeQuery.trim().toLowerCase();
    return changedFiles.filter((file) => {
      const status = (file.status || "other").toLowerCase();
      const path = file.filename || file.path || "";
      if (changeStatus !== "all" && status !== changeStatus) return false;
      if (changeType !== "all" && fileTypeForPath(path) !== changeType) return false;
      return !needle || path.toLowerCase().includes(needle);
    });
  }, [changedFiles, changeQuery, changeStatus, changeType]);

  const filteredCategoryFiles = useMemo(() => {
    const needle = fileQuery.trim().toLowerCase();
    return selectedFiles.filter((path) => !needle || path.toLowerCase().includes(needle)).sort((a, b) => fileSort === "asc" ? a.localeCompare(b) : b.localeCompare(a));
  }, [selectedFiles, fileQuery, fileSort]);
  const filePages = Math.max(1, Math.ceil(filteredCategoryFiles.length / filesPageSize));
  const fileStart = (filesPage - 1) * filesPageSize;
  const fileEnd = Math.min(fileStart + filesPageSize, filteredCategoryFiles.length);

  useEffect(() => { onFilesPage(1); }, [fileQuery, fileSort, onFilesPage]);

  return (
    <section id="changes" className="panel" aria-labelledby="change-overview-title">
      <div className="section-header">
        <div><div className="eyebrow">Repository inventory</div><h2 id="change-overview-title">Change overview</h2><p>Compare the current file inventory with daily and weekly change windows.</p></div>
        <div className="date-stack"><span>Daily from <strong>{formatDateShort(statsWindows.daily_start)}</strong></span><span>Weekly from <strong>{formatDateShort(statsWindows.weekly_start)}</strong></span></div>
      </div>

      <div className="status-overview">
        <div className="status-bar" aria-label={`${statusTotal} total repository changes`}>
          {statusItems.filter((item) => item.count > 0).map((item) => <span className={`status-segment ${item.key}`} key={item.key} style={{ width: `${(item.count / Math.max(1, statusTotal)) * 100}%` }} title={`${item.label}: ${item.count}`} />)}
          {statusTotal === 0 && <span className="status-segment empty" />}
        </div>
        <div className="status-legend">{statusItems.map((item) => <div key={item.key}><span className={`legend-dot ${item.key}`} /><span>{item.label}</span><strong>{formatNumber(item.count)}</strong></div>)}</div>
      </div>

      <div className="inventory-grid">
        <InventoryCard title="Total repository files" total={statsProfile.total_files} values={statsProfile} />
        <InventoryCard title="Changes since last update" total={totalChanges} values={{ md: changeByType.md?.total, mdx: changeByType.mdx?.total, images: changeByType.images?.total, page_components: changeByType.page_components?.total, yml: changeByType.yml?.total }} />
      </div>

      <div className="table-wrap">
        <table className="data-table stats-table">
          <caption className="sr-only">File totals and recent changes by file type</caption>
          <thead><tr><th>File type</th><th>Total</th><th>New / updated</th><th>Deleted</th><th>Daily</th><th>Weekly</th></tr></thead>
          <tbody>
            {statsRows.length === 0 ? <tr><td colSpan="6"><div className="empty-state">Repository statistics are unavailable.</div></td></tr>
              : statsRows.map((row) => {
                const canOpen = row.key !== "external_md" && row.key !== "total";
                return <tr key={row.key} className={`${row.key === "total" ? "total-row" : ""} ${row.key === selectedType ? "selected" : ""}`}><td>{canOpen ? <button className="row-button" type="button" onClick={() => onTypeClick(row)} aria-expanded={selectedType === row.key}><span>{row.label}</span><Icon name="chevron" size={16} /></button> : <strong>{row.label}</strong>}</td><td>{formatNumber(row.total)}</td><td>{formatNumber(row.changed)}</td><td>{formatNumber(row.deleted)}</td><td>{row.daily == null ? "—" : formatNumber(row.daily)}</td><td>{row.weekly == null ? "—" : formatNumber(row.weekly)}</td></tr>;
              })}
          </tbody>
        </table>
      </div>

      {selectedType && (
        <div className="file-drawer">
          <div className="drawer-header"><div><span>Files in category</span><h3>{selectedRow?.label || "Files"}</h3></div><button className="text-button" type="button" onClick={onCloseType}>Close</button></div>
          <div className="data-toolbar compact-toolbar"><SearchField label="Search paths in selected category" placeholder="Search repository paths…" value={fileQuery} onChange={setFileQuery} /><label className="select-field"><span>Sort</span><select value={fileSort} onChange={(event) => setFileSort(event.target.value)}><option value="asc">Path A–Z</option><option value="desc">Path Z–A</option></select></label></div>
          {typeFilesError ? <div className="notice notice-warning">{typeFilesError}</div> : <div className="table-wrap compact-table"><table className="data-table"><caption className="sr-only">Files in {selectedRow?.label || "selected category"}</caption><thead><tr><th>#</th><th>Repository path</th></tr></thead><tbody>{typeFilesLoading ? <tr><td colSpan="2"><div className="empty-state">Loading files…</div></td></tr> : filteredCategoryFiles.length === 0 ? <tr><td colSpan="2"><div className="empty-state">No files match this search.</div></td></tr> : filteredCategoryFiles.slice(fileStart, fileEnd).map((path, index) => <tr key={path}><td>{fileStart + index + 1}</td><td><code className="path-code">{path}</code></td></tr>)}</tbody></table></div>}
          <Pager page={filesPage} pages={filePages} start={fileStart + 1} end={fileEnd} total={filteredCategoryFiles.length} onPrevious={() => onFilesPage(Math.max(1, filesPage - 1))} onNext={() => onFilesPage(Math.min(filePages, filesPage + 1))} />
        </div>
      )}

      <div className="subsection-header"><div><h3>Files in the current comparison</h3><p>Checked {formatDate(summary.changes?.last_checked)}. Filter by status, content type, or path.</p></div><strong>{formatNumber(visibleChanges.length)} results</strong></div>
      <div className="data-toolbar changes-toolbar">
        <SearchField label="Search changed repository paths" placeholder="Search changed paths…" value={changeQuery} onChange={setChangeQuery} />
        <label className="select-field"><span>Status</span><select value={changeStatus} onChange={(event) => setChangeStatus(event.target.value)}><option value="all">All statuses</option>{statusItems.filter((item) => item.count > 0).map((item) => <option key={item.key} value={item.key}>{item.label}</option>)}</select></label>
        <label className="select-field"><span>Type</span><select value={changeType} onChange={(event) => setChangeType(event.target.value)}>{Object.entries(TYPE_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      </div>
      <div className="change-list" role="list">{visibleChanges.length === 0 ? <div className="empty-state">No changed files match these filters.</div> : visibleChanges.slice(0, 100).map((file, index) => { const path = file.filename || file.path || "Unknown path"; const status = (file.status || "other").toLowerCase(); return <div className="change-item" role="listitem" key={`${path}-${index}`}><span className={`status-badge ${status}`}>{status}</span><code>{path}</code><span>{TYPE_LABELS[fileTypeForPath(path)]}</span></div>; })}</div>
      {visibleChanges.length > 100 && <p className="section-note">Showing the first 100 matching files. Narrow the search to inspect a specific path.</p>}
      <p className="section-note">Daily and weekly values use Git history. JavaScript and CSS are grouped as page components; the total includes external Markdown.</p>
    </section>
  );
}

function InventoryCard({ title, total, values }) {
  return <article className="inventory-card"><div><span>{title}</span><strong>{formatNumber(total)}</strong></div><dl><div><dt>Markdown</dt><dd>{formatNumber(values.md)}</dd></div><div><dt>MDX</dt><dd>{formatNumber(values.mdx)}</dd></div><div><dt>Images</dt><dd>{formatNumber(values.images)}</dd></div><div><dt>Page components</dt><dd>{formatNumber(values.page_components)}</dd></div><div><dt>YAML</dt><dd>{formatNumber(values.yml)}</dd></div></dl></article>;
}
