export function Icon({ name, size = 18 }) {
  let path;
  if (name === "refresh") path = <><path d="M20 11a8.1 8.1 0 0 0-15.5-3M4 4v4h4" /><path d="M4 13a8.1 8.1 0 0 0 15.5 3M20 20v-4h-4" /></>;
  else if (name === "play") path = <path d="m8 5 11 7-11 7V5Z" />;
  else if (name === "download") path = <><path d="M12 3v12" /><path d="m7 10 5 5 5-5" /><path d="M5 21h14" /></>;
  else if (name === "branch") path = <><circle cx="6" cy="5" r="2" /><circle cx="18" cy="6" r="2" /><circle cx="6" cy="19" r="2" /><path d="M6 7v10M8 9c5 0 5-3 8-3" /></>;
  else if (name === "clock") path = <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>;
  else if (name === "folder") path = <path d="M3 7h7l2 2h9v10H3V7Z" />;
  else if (name === "external") path = <><path d="M14 4h6v6" /><path d="m20 4-9 9" /><path d="M18 13v6H5V6h6" /></>;
  else if (name === "chevron") path = <path d="m9 18 6-6-6-6" />;
  else if (name === "search") path = <><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></>;
  else if (name === "alert") path = <><path d="M12 3 2.8 20h18.4L12 3Z" /><path d="M12 9v4M12 17h.01" /></>;
  else if (name === "check") path = <path d="m5 12 4 4L19 6" />;
  else if (name === "history") path = <><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5M12 7v5l3 2" /></>;
  else if (name === "close") path = <path d="m6 6 12 12M18 6 6 18" />;
  else path = <><path d="M4 18V9M10 18V5M16 18v-7M22 18H2" /></>;
  return <svg aria-hidden="true" className="icon" fill="none" height={size} viewBox="0 0 24 24" width={size} stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8">{path}</svg>;
}

export function MetricCard({ icon, label, value, detail, tone = "blue" }) {
  return <article className={`metric-card tone-${tone}`}><div className="metric-icon"><Icon name={icon} /></div><div><div className="metric-label">{label}</div><div className="metric-value">{value}</div><div className="metric-detail">{detail}</div></div></article>;
}

export function Pager({ page, pages, start, end, total, onPrevious, onNext }) {
  if (pages <= 1) return null;
  return <nav className="pagination" aria-label="Table pagination"><button className="pager-btn" onClick={onPrevious} disabled={page === 1} type="button">Previous</button><div className="pager-info"><strong>{start}-{end}</strong> of {total} <span aria-hidden="true">·</span> Page {page} of {pages}</div><button className="pager-btn" onClick={onNext} disabled={page === pages} type="button">Next</button></nav>;
}

export function SearchField({ value, onChange, placeholder, label }) {
  return <label className="search-field"><span className="sr-only">{label}</span><Icon name="search" size={16} /><input type="search" value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} /></label>;
}
