import { useEffect, useMemo, useRef, useState } from "react";
import { Navigate } from "react-router-dom";
import { cmsAPI, groupAPI, meetingAPI, reportsAPI, userAPI } from "../services/api";
import { useAuth } from "../context/AuthContext";
import "./Reports.css";

const DAY_MS = 24 * 60 * 60 * 1000;

function roleLabel(value) {
  return (value || "").toString().toUpperCase();
}

function sameUser(member, user) {
  if (!member || !user) return false;
  return (
    (member.UUID && user.UUID && String(member.UUID) === String(user.UUID)) ||
    (member.s_id && user.s_id && String(member.s_id) === String(user.s_id))
  );
}

function buildHistorySeries(current, seedText) {
  const base = Number(current) || 0;
  const seed = (seedText || "")
    .split("")
    .reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
  const result = [];
  for (let i = 6; i >= 0; i -= 1) {
    const delta = ((seed + i * 7) % 5) - 2;
    result.push(Math.max(0, base + delta));
  }
  return result;
}

export default function Reports({ language = "en" }) {
  const { currentUser } = useAuth();
  const isHebrew = language === "he";

  const text = {
    loadReportsError: isHebrew
      ? "טעינת נתוני הדוחות נכשלה."
      : "Failed to load reports data.",
    pageTitle: isHebrew ? "דוחות" : "Reports",
    refresh: isHebrew ? "רענון" : "Refresh",
    loadingReports: isHebrew ? "טוען דוחות..." : "Loading reports...",
    latestUploadTitle: isHebrew
      ? "הוועידה האחרונה שעלתה"
      : "Last Meeting Upload",
    meetingPrefix: isHebrew ? "ועידה" : "Meeting",
    lastActivity: isHebrew ? "פעילות אחרונה" : "Last activity",
    noMeetingActivity: isHebrew
      ? "עדיין אין נתוני פעילות על ועידות."
      : "No meeting activity data available yet.",
    userMembershipTitle: isHebrew
      ? " דוח משתתף   לפי טלפון"
      : "Participant Report",
    phonePlaceholder: isHebrew ? "הכנס מספר טלפון..." : "Enter phone number...",
    searchBtn: isHebrew ? "חיפוש" : "Search",
    searching: isHebrew ? "מחפש..." : "Searching...",
    cdrHint: isHebrew
      ? "הכנס מספר טלפון של משתתף כדי לראות את היסטוריית השיחות שלו."
      : "Enter a participant phone number to view their call history.",
    cdrNoResults: isHebrew
      ? "לא נמצאו שיחות עבור מספר זה."
      : "No calls found for this number.",
    cdrError: isHebrew ? "החיפוש נכשל." : "Search failed.",
    colMeeting: isHebrew ? "ועידה" : "Meeting",
    colDate: isHebrew ? "תאריך התחלה" : "Start Time",
    colDuration: isHebrew ? "משך (שניות)" : "Duration (s)",
    colStatus: isHebrew ? "סטטוס" : "Status",
    groupLabel: isHebrew ? "קבוצה" : "Group",
    unusedTitle: isHebrew ? "ועידות שלא בשימוש" : "Unused Meetings",
    noUnused: isHebrew
      ? "לא זוהו ועידות לא פעילות."
      : "No unused meetings detected.",
    unusedTag: isHebrew ? "לא בשימוש" : "Unused",
    never: isHebrew ? "מעולם לא" : "Never",
  };

  // Only super_admin and admin can access reports
  if (!["super_admin", "admin"].includes(currentUser?.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  const canReadAllUsers = true;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [meetings, setMeetings] = useState([]);
  const [groups, setGroups] = useState([]);
  const [users, setUsers] = useState([]);
  const [cmsMeetings, setCmsMeetings] = useState([]);

  const [userFilter, setUserFilter] = useState("");

  const [cdrPhone, setCdrPhone] = useState("");
  const [cdrResults, setCdrResults] = useState(null);
  const [cdrLoading, setCdrLoading] = useState(false);
  const [cdrError, setCdrError] = useState("");
  const cdrInputRef = useRef(null);

  const handleCdrSearch = async () => {
    const phone = cdrPhone.trim();
    if (!phone) return;
    setCdrLoading(true);
    setCdrError("");
    setCdrResults(null);
    try {
      const resp = await reportsAPI.getCdrByPhone(phone);
      setCdrResults(resp.data || []);
    } catch (err) {
      setCdrError(err?.response?.data?.detail || text.cdrError);
    } finally {
      setCdrLoading(false);
    }
  };

  const loadReports = async () => {
    try {
      setLoading(true);
      setError("");

      const [meetingsResp, groupsResp, usersResp, cmsResp] =
        await Promise.allSettled([
          meetingAPI.getAllMeetings(),
          groupAPI.listGroups(),
          canReadAllUsers
            ? userAPI.getAllUsers()
            : Promise.resolve({ data: [] }),
          cmsAPI.getMeetings(),
        ]);

      if (meetingsResp.status === "fulfilled") {
        setMeetings(meetingsResp.value.data || []);
      } else {
        setMeetings([]);
      }

      if (groupsResp.status === "fulfilled") {
        setGroups(groupsResp.value.data || []);
      } else {
        setGroups([]);
      }

      if (usersResp.status === "fulfilled") {
        setUsers(usersResp.value.data || []);
      } else {
        setUsers([]);
      }

      if (cmsResp.status === "fulfilled") {
        setCmsMeetings(cmsResp.value.data || []);
      } else {
        setCmsMeetings([]);
      }

      const allFailed =
        meetingsResp.status === "rejected" &&
        groupsResp.status === "rejected" &&
        usersResp.status === "rejected";

      if (allFailed) {
        setError(text.loadReportsError);
      }
    } catch {
      setError(text.loadReportsError);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, [canReadAllUsers]);

  const groupsById = useMemo(() => {
    const map = {};
    (groups || []).forEach((g) => {
      if (g?.UUID) map[g.UUID] = g;
    });
    return map;
  }, [groups]);

  const cmsByMeetingNumber = useMemo(() => {
    const map = {};
    (cmsMeetings || []).forEach((m) => {
      if (m?.meetingId) map[String(m.meetingId)] = m;
    });
    return map;
  }, [cmsMeetings]);

  const meetingRows = useMemo(() => {
    return (meetings || []).map((m) => {
      const cms = cmsByMeetingNumber[String(m.m_number)] || null;
      const groupNames = (m.groups || []).map(
        (gId) => groupsById[gId]?.name || gId,
      );
      const participantsNow = cms?.participantsCount ?? 0;
      const history = buildHistorySeries(participantsNow, String(m.m_number));

      return {
        uuid: m.UUID,
        meetingNumber: String(m.m_number || "-"),
        accessLevel: m.accessLevel || "unknown",
        password: m.password || cms?.password || "No password",
        groups: groupNames,
        lastUsedAt: cms?.lastUsedAt || null,
        status: cms?.status || "unknown",
        participantsNow,
        history,
      };
    });
  }, [meetings, cmsByMeetingNumber, groupsById]);

  const latestMeeting = useMemo(() => {
    if (!meetingRows.length) return null;
    return (
      [...meetingRows]
        .filter((m) => m.lastUsedAt)
        .sort(
          (a, b) =>
            new Date(b.lastUsedAt).getTime() - new Date(a.lastUsedAt).getTime(),
        )[0] || null
    );
  }, [meetingRows]);

  const unusedMeetings = useMemo(() => {
    const now = Date.now();
    return meetingRows.filter((m) => {
      const stale =
        !m.lastUsedAt || now - new Date(m.lastUsedAt).getTime() > 30 * DAY_MS;
      return m.status === "not_in_use" || (m.participantsNow === 0 && stale);
    });
  }, [meetingRows]);

  const selectedUser = useMemo(
    () => users.find((u) => String(u.UUID) === String(userFilter)) || null,
    [users, userFilter],
  );

  const userMeetingRows = useMemo(() => {
    if (!selectedUser) return [];

    const groupIds = (groups || [])
      .filter((g) =>
        (g.members || []).some((member) => sameUser(member, selectedUser)),
      )
      .map((g) => g.UUID);

    return meetingRows.filter((m) =>
      (m.groups || []).some((nameOrId) => {
        if (groupIds.includes(nameOrId)) return true;
        const group = (groups || []).find((g) => g.name === nameOrId);
        return !!group && groupIds.includes(group.UUID);
      }),
    );
  }, [selectedUser, groups, meetingRows]);

  return (
    <div className="page reports-page">
      <h2 className="page-header">{text.pageTitle}</h2>

      <div className="reports-actions">
        <button
          className="btn-secondary refresh-soft-button"
          type="button"
          onClick={loadReports}
        >
          {text.refresh}
        </button>
      </div>

      {loading ? (
        <div className="reports-info">{text.loadingReports}</div>
      ) : null}
      {error ? <div className="reports-error">{error}</div> : null}

      <section className="card reports-card">
        <h3 className="card-title">{text.latestUploadTitle}</h3>
        {latestMeeting ? (
          <div className="reports-grid-two">
            <div>
              <div className="reports-value">
                {text.meetingPrefix} #{latestMeeting.meetingNumber}
              </div>
              <div className="reports-sub">
                {text.lastActivity}:{" "}
                {new Date(latestMeeting.lastUsedAt).toLocaleString()}
              </div>
            </div>
            <div className="reports-tag">
              {roleLabel(latestMeeting.accessLevel)}
            </div>
          </div>
        ) : (
          <div className="reports-empty">{text.noMeetingActivity}</div>
        )}
      </section>

      <section className="card reports-card">
        <h3 className="card-title">{text.userMembershipTitle}</h3>

        <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
          <input
            ref={cdrInputRef}
            className="search-input"
            type="text"
            placeholder={text.phonePlaceholder}
            value={cdrPhone}
            onChange={(e) => setCdrPhone(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleCdrSearch()}
            style={{ flex: 1 }}
          />
          <button
            className="search-button"
            type="button"
            onClick={handleCdrSearch}
            disabled={cdrLoading || !cdrPhone.trim()}
          >
            {cdrLoading ? text.searching : text.searchBtn}
          </button>
        </div>

        {!cdrResults && !cdrError && (
          <div className="reports-empty">{text.cdrHint}</div>
        )}

        {cdrError && <div className="reports-error">{cdrError}</div>}

        {cdrResults !== null && !cdrError && (
          cdrResults.length === 0 ? (
            <div className="reports-empty">{text.cdrNoResults}</div>
          ) : (
            <div className="reports-table-wrap">
              <table className="reports-servers-table">
                <thead>
                  <tr>
                    <th>{text.colMeeting}</th>
                    <th>{text.colDate}</th>
                    <th>{text.colDuration}</th>
                    <th>{text.colStatus}</th>
                  </tr>
                </thead>
                <tbody>
                  {cdrResults.map((row, i) => (
                    <tr key={i}>
                      <td>{row.meeting_number ?? "—"}</td>
                      <td>{row.start_time ?? "—"}</td>
                      <td>{row.duration ?? "—"}</td>
                      <td>{row.status ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        )}
      </section>

      <section className="card reports-card">
        <h3 className="card-title">{text.unusedTitle}</h3>
        {unusedMeetings.length === 0 ? (
          <div className="reports-empty">{text.noUnused}</div>
        ) : (
          <div className="reports-list">
            {unusedMeetings.map((m) => (
              <div className="reports-list-item" key={`${m.uuid}-unused`}>
                <div className="reports-list-head">
                  <strong>
                    {text.meetingPrefix} #{m.meetingNumber}
                  </strong>
                  <span className="reports-tag reports-tag-warn">
                    {text.unusedTag}
                  </span>
                </div>
                <div className="reports-sub">
                  {text.lastActivity}:{" "}
                  {m.lastUsedAt
                    ? new Date(m.lastUsedAt).toLocaleString()
                    : text.never}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
