export const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8001";

export const emptySummary = {
  changes: {
    repo: "CIROH-UA/ciroh_hub", last_checked: null, latest_sha: null,
    latest_commit_date: null, latest_commit_message: null,
    changed_files_count: 0, changed_files: []
  },
  status_counts: { added: 0, modified: 0, removed: 0, renamed: 0, other: 0 },
  top_paths: [],
  metrics: { signal_score: 0, freshness_hours: null, cadence: "weekly" },
  file_stats: {
    generated_at: null, last_checked: null, external_last_checked: null,
    windows: { daily_start: null, weekly_start: null, now: null },
    profile: { total_files: 0, md: 0, mdx: 0, images: 0, page_components: 0, yml: 0 },
    change_profile: { total_changes: 0, by_type: {} },
    table: { rows: [], sources: {} }
  }
};

export const emptyExternal = {
  last_checked: null, total_repos: 0, rendered_files: [], repos: {},
  repo_root: null, download_root: null
};

export const formatNumber = (value) => new Intl.NumberFormat().format(Number(value) || 0);

export const formatDate = (value) => {
  if (!value) return "Not available";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
};

export const formatDateShort = (value) => {
  if (!value) return "Not available";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(date);
};

export const formatDuration = (hours) => {
  if (hours == null) return "Unknown";
  const total = Math.max(0, Math.floor(hours));
  const days = Math.floor(total / 24);
  const remainder = total % 24;
  if (days > 0) return `${days}d ${remainder}h`;
  return `${remainder}h`;
};

export const formatSeconds = (seconds) => {
  if (seconds == null) return "Not available";
  const value = Math.max(0, Math.round(Number(seconds) || 0));
  if (value < 60) return `${value}s`;
  const minutes = Math.floor(value / 60);
  const remainder = value % 60;
  if (minutes < 60) return `${minutes}m ${remainder}s`;
  return `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
};

export const signalLabel = (score) => {
  if (score >= 90) return "Very high";
  if (score >= 75) return "High";
  if (score >= 50) return "Moderate";
  if (score >= 25) return "Low";
  return "Minimal";
};

export const freshnessLabel = (hours) => {
  if (hours == null) return "Unknown";
  if (hours < 24) return "Fresh";
  if (hours < 72) return "Warm";
  return "Stale";
};

export const shortSha = (sha) => (sha ? sha.slice(0, 8) : "Not available");

export const fileTypeForPath = (path = "") => {
  const extension = path.toLowerCase().split(".").pop();
  if (extension === "md") return "md";
  if (extension === "mdx") return "mdx";
  if (["png", "jpg", "jpeg", "gif", "svg", "webp", "bmp", "tif", "tiff", "ico"].includes(extension)) return "images";
  if (["js", "jsx", "mjs", "cjs", "ts", "tsx", "css", "scss", "sass", "less"].includes(extension)) return "page_components";
  if (["yml", "yaml"].includes(extension)) return "yml";
  return "other";
};

const csvEscape = (value) => {
  if (value == null) return "";
  const text = String(value);
  if (/[",\n]/.test(text)) return `"${text.replace(/"/g, '""')}"`;
  return text;
};

export const buildExternalCsv = (rows, repoRoot, downloadRoot) => {
  const headers = [
    ["repo_root", "repo_root"], ["download_root", "download_root"],
    ["local_path", "path"], ["external_repo", "external_repo"],
    ["repo_file", "tracked_path"], ["downloaded_path", "downloaded_path"],
    ["change_state", "change_state"], ["latest_sha", "latest_sha"],
    ["latest_commit_date", "latest_commit_date"], ["previous_sha", "previous_sha"],
    ["previous_commit_date", "previous_commit_date"]
  ];
  const lines = [headers.map(([label]) => label).join(",")];
  for (const row of rows || []) {
    const hydrated = { ...row, repo_root: repoRoot || "", download_root: downloadRoot || "" };
    lines.push(headers.map(([, key]) => csvEscape(hydrated[key] ?? "")).join(","));
  }
  return lines.join("\n");
};

export const downloadTextFile = (content, filename, type = "text/plain;charset=utf-8;") => {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
};
