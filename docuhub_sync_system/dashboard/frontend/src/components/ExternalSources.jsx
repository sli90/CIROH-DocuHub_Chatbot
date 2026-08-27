import { useEffect, useMemo, useState } from "react";
import { buildExternalCsv, downloadTextFile, formatDate, formatNumber, shortSha } from "../lib/dashboard.js";
import { Icon, Pager, SearchField } from "./Common.jsx";

export default function ExternalSources({ externalInfo, loading }) {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("all");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("date_desc");
  const pageSize = 10;
  const files = externalInfo.rendered_files || [];

  const counts = useMemo(() => {
    const result = { all: files.length, changed: 0, unchanged: 0, baseline: 0, unknown: 0 };
    files.forEach((file) => { const key = file.change_state || "unknown"; result[key] = (result[key] || 0) + 1; });
    return result;
  }, [files]);

  const visibleFiles = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const filtered = files.filter((file) => {
      if (status !== "all" && (file.change_state || "unknown") !== status) return false;
      if (!needle) return true;
      return [file.path, file.external_repo, file.tracked_path].some((value) => String(value || "").toLowerCase().includes(needle));
    });
    return filtered.sort((a, b) => {
      if (sort === "repo") return String(a.external_repo || "").localeCompare(String(b.external_repo || ""));
      if (sort === "path") return String(a.path || "").localeCompare(String(b.path || ""));
      if (sort === "status") return String(a.change_state || "unknown").localeCompare(String(b.change_state || "unknown"));
      const aDate = new Date(a.latest_commit_date || 0).getTime() || 0;
      const bDate = new Date(b.latest_commit_date || 0).getTime() || 0;
      return sort === "date_asc" ? aDate - bDate : bDate - aDate;
    });
  }, [files, query, sort, status]);

  useEffect(() => { setPage(1); }, [query, sort, status]);
  const pages = Math.max(1, Math.ceil(visibleFiles.length / pageSize));
  const start = (page - 1) * pageSize;
  const end = Math.min(start + pageSize, visibleFiles.length);
  const pageItems = visibleFiles.slice(start, end);

  const downloadFiltered = () => {
    const csv = buildExternalCsv(visibleFiles, externalInfo.repo_root, externalInfo.download_root);
    downloadTextFile(csv, `external_readme_sources_${new Date().toISOString().slice(0, 10)}.csv`, "text/csv;charset=utf-8;");
  };

  return (
    <section id="external-sources" className="panel" aria-labelledby="external-title">
      <div className="section-header">
        <div><div className="eyebrow">Embedded content</div><h2 id="external-title">External README sources</h2><p>Monitor the upstream repositories that provide content to CIROH Hub.</p></div>
        <div className="panel-toolbar"><span>{externalInfo.last_checked ? `Checked ${formatDate(externalInfo.last_checked)}` : "Not checked yet"}</span><button className="button button-secondary" onClick={downloadFiltered} disabled={visibleFiles.length === 0} type="button"><Icon name="download" /> Export filtered ({formatNumber(visibleFiles.length)})</button></div>
      </div>

      <div className="filter-bar" aria-label="Filter external sources by status">{["all", "changed", "unchanged", "baseline", "unknown"].map((value) => <button key={value} type="button" className={status === value ? "active" : ""} aria-pressed={status === value} onClick={() => setStatus(value)}><span>{value}</span><strong>{formatNumber(counts[value] || 0)}</strong></button>)}</div>
      <div className="data-toolbar">
        <SearchField label="Search external sources" placeholder="Search repository or file path…" value={query} onChange={setQuery} />
        <label className="select-field"><span>Sort</span><select value={sort} onChange={(event) => setSort(event.target.value)}><option value="date_desc">Newest commit</option><option value="date_asc">Oldest commit</option><option value="repo">Repository A–Z</option><option value="path">Local path A–Z</option><option value="status">Status A–Z</option></select></label>
      </div>

      <div className="table-wrap">
        <table className="data-table external-table">
          <caption className="sr-only">External repositories and tracked README files</caption>
          <thead><tr><th>Status</th><th>Local file</th><th>External repository</th><th>Source file</th><th>Commit</th><th>Commit date</th></tr></thead>
          <tbody>{visibleFiles.length === 0 ? <tr><td colSpan="6"><div className="empty-state">{loading ? "Loading external sources…" : files.length ? "No sources match these filters." : "No external sources are available."}</div></td></tr> : pageItems.map((file) => <tr key={`${file.path}-${file.external_repo}`}><td><span className={`status-badge ${file.change_state || "unknown"}`}>{file.change_state || "unknown"}</span></td><td><code className="path-code">{file.path}</code></td><td><a className="repo-link" href={`https://github.com/${file.external_repo}`} target="_blank" rel="noreferrer">{file.external_repo}<Icon name="external" size={14} /></a></td><td><code className="path-code">{file.tracked_path || "README.md"}</code></td><td><code>{shortSha(file.latest_sha)}</code></td><td>{formatDate(file.latest_commit_date)}</td></tr>)}</tbody>
        </table>
      </div>
      <Pager page={page} pages={pages} start={start + 1} end={end} total={visibleFiles.length} onPrevious={() => setPage((value) => Math.max(1, value - 1))} onNext={() => setPage((value) => Math.min(pages, value + 1))} />
    </section>
  );
}
