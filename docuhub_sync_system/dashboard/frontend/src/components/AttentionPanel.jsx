import { Icon } from "./Common.jsx";

export default function AttentionPanel({ items }) {
  const criticalCount = items.filter((item) => item.tone === "critical").length;
  const warningCount = items.filter((item) => item.tone === "warning").length;

  return (
    <section className={`attention-panel ${items.length === 0 ? "all-clear" : ""}`} aria-labelledby="attention-title">
      <div className="attention-heading">
        <div className="attention-icon"><Icon name={items.length ? "alert" : "check"} /></div>
        <div>
          <div className="eyebrow">Operator focus</div>
          <h2 id="attention-title">{items.length ? "Needs attention" : "All checks clear"}</h2>
          <p>{items.length ? `${criticalCount} critical · ${warningCount} warnings · ${items.length} total signals` : "No current failures, stale data, or unresolved source changes were detected."}</p>
        </div>
      </div>
      {items.length > 0 && (
        <div className="attention-list">
          {items.map((item) => (
            <a className={`attention-item ${item.tone}`} href={item.target} key={item.key}>
              <span className="attention-indicator" />
              <span><strong>{item.title}</strong><small>{item.detail}</small></span>
              <Icon name="chevron" size={16} />
            </a>
          ))}
        </div>
      )}
    </section>
  );
}
