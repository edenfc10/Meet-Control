import { useEffect, useState } from "react";
import { logsAPI } from "../services/api";
import "./Logs.css";

const LOG_TABS = [
  { key: "info",     label: "Info",     labelHe: "פעולות",  cls: "log-tab--info" },
  { key: "warnings", label: "Warnings", labelHe: "אזהרות",  cls: "log-tab--warning" },
  { key: "errors",   label: "Errors",   labelHe: "שגיאות",  cls: "log-tab--error" },
];

function LogEntry({ date, isHebrew }) {
  const [open, setOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("info");
  const [cache, setCache] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadTab = async (type) => {
    if (cache[type] !== undefined) return;
    setLoading(true);
    setError("");
    try {
      const resp = await logsAPI.getLogByDateAndType(date, type);
      setCache((prev) => ({ ...prev, [type]: (resp.data.lines || []).slice().reverse() }));
    } catch {
      setError(isHebrew ? "טעינת לוג נכשלה." : "Failed to load log.");
    } finally {
      setLoading(false);
    }
  };

  const toggle = async () => {
    if (!open) await loadTab(activeTab);
    setOpen((prev) => !prev);
  };

  const handleTabChange = async (type) => {
    setActiveTab(type);
    await loadTab(type);
  };

  const lines = cache[activeTab];

  return (
    <div className="log-accordion">
      <div className="log-accordion-header-row">
        <button
          className={`log-accordion-header${open ? " open" : ""}`}
          onClick={toggle}
        >
          <span className="log-accordion-arrow">{open ? "▼" : "▶"}</span>
          <span>{date}</span>
        </button>
        <button
          className="log-download-btn"
          type="button"
          onClick={() => logsAPI.downloadLog(date)}
        >
          {isHebrew ? "הורד" : "Download"}
        </button>
      </div>

      {open && (
        <div className="log-accordion-body">
          <div className="log-tabs">
            {LOG_TABS.map((tab) => (
              <button
                key={tab.key}
                className={`log-tab ${tab.cls}${activeTab === tab.key ? " active" : ""}`}
                onClick={() => handleTabChange(tab.key)}
              >
                {isHebrew ? tab.labelHe : tab.label}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="logs-loading">{isHebrew ? "טוען..." : "Loading..."}</div>
          ) : error ? (
            <div className="logs-error">{error}</div>
          ) : !lines || lines.length === 0 ? (
            <div className="logs-empty">{isHebrew ? "אין שורות" : "No entries"}</div>
          ) : (
            <pre className="logs-pre">
              {lines.map((line, i) => (
                <div key={i} className="log-line">{line}</div>
              ))}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}

export default function Logs({ language = "en" }) {
  const isHebrew = language === "he";
  const [dates, setDates] = useState([]);
  const [loadingDates, setLoadingDates] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchDates = async () => {
      try {
        const resp = await logsAPI.getDates();
        setDates(resp.data || []);
      } catch {
        setError(isHebrew ? "טעינת תאריכים נכשלה." : "Failed to load log dates.");
      } finally {
        setLoadingDates(false);
      }
    };
    fetchDates();
  }, []);

  return (
    <div className="logs-page">
      <h2 className="logs-title">{isHebrew ? "לוגים" : "Logs"}</h2>

      <div className="logs-actions">
        <button
          className="logs-download-all-btn"
          type="button"
          onClick={() => logsAPI.downloadAllLogs()}
        >
          {isHebrew ? "הורד את כל הלוגים" : "Download all logs"}
        </button>
      </div>

      {error && <div className="logs-error">{error}</div>}

      {loadingDates ? (
        <div className="logs-loading">{isHebrew ? "טוען..." : "Loading..."}</div>
      ) : dates.length === 0 ? (
        <div className="logs-empty">{isHebrew ? "אין לוגים" : "No logs found"}</div>
      ) : (
        <div className="logs-accordion-list">
          {dates.map((date) => (
            <LogEntry key={date} date={date} isHebrew={isHebrew} />
          ))}
        </div>
      )}
    </div>
  );
}
