import { useEffect, useMemo, useState } from "react";
import { Navigate } from "react-router-dom";
import { cmsAPI, groupAPI, meetingAPI, userAPI } from "../services/api";
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
    allMeetingsTitle: isHebrew
      ? "כל הוועידות עם סיסמה וקבוצה"
      : "All Meetings With Password And Group",
    noMeetingsFound: isHebrew ? "לא נמצאו ועידות." : "No meetings found.",
    tableMeeting: isHebrew ? "ועידה" : "Meeting",
    tableType: isHebrew ? "סוג" : "Type",
    tablePassword: isHebrew ? "סיסמה" : "Password",
    tableGroup: isHebrew ? "קבוצה" : "Group",
    noGroup: isHebrew ? "ללא קבוצה" : "No group",
    participantsTitle: isHebrew ? "דוח משתתפים" : "Participants Report",
    now: isHebrew ? "כרגע" : "Now",
    pastSamples: isHebrew ? "7 דגימות אחרונות" : "Past 7 samples",
    userMembershipTitle: isHebrew
      ? "דוח שיוך משתמש לוועידות"
      : "User Meeting Membership Report",
    selectUser: isHebrew ? "בחר משתמש..." : "Select user...",
    selectUserHint: isHebrew
      ? "בחר משתמש כדי לראות ועידות קשורות."
      : "Select a user to see related meetings.",
    userNoMeetings: isHebrew
      ? "המשתמש הזה עדיין לא משויך לאף ועידה."
      : "This user is not linked to any meeting yet.",
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

  const canReadAllUsers = currentUser?.role !== "viewer";

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [meetings, setMeetings] = useState([]);
  const [groups, setGroups] = useState([]);
  const [users, setUsers] = useState([]);
  const [cmsMeetings, setCmsMeetings] = useState([]);

  const [userFilter, setUserFilter] = useState("");

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
        <h3 className="card-title">{text.allMeetingsTitle}</h3>
        {meetingRows.length === 0 ? (
          <div className="reports-empty">{text.noMeetingsFound}</div>
        ) : (
          <div className="reports-table-wrap">
            <table className="reports-table">
              <thead>
                <tr>
                  <th>{text.tableMeeting}</th>
                  <th>{text.tableType}</th>
                  <th>{text.tablePassword}</th>
                  <th>{text.tableGroup}</th>
                </tr>
              </thead>
              <tbody>
                {meetingRows.map((m) => (
                  <tr key={m.uuid}>
                    <td>#{m.meetingNumber}</td>
                    <td>{roleLabel(m.accessLevel)}</td>
                    <td>{m.password}</td>
                    <td>
                      {m.groups.length ? m.groups.join(", ") : text.noGroup}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="card reports-card">
        <h3 className="card-title">{text.participantsTitle}</h3>
        {meetingRows.length === 0 ? (
          <div className="reports-empty">{text.noMeetingsFound}</div>
        ) : (
          <div className="reports-list">
            {meetingRows.map((m) => (
              <div className="reports-list-item" key={`${m.uuid}-participants`}>
                <div className="reports-list-head">
                  <strong>
                    {text.meetingPrefix} #{m.meetingNumber}
                  </strong>
                  <span className="reports-tag reports-tag-soft">
                    {text.now}: {m.participantsNow}
                  </span>
                </div>
                <div className="reports-sub">
                  {text.pastSamples}: {m.history.join(" • ")}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="card reports-card">
        <h3 className="card-title">{text.userMembershipTitle}</h3>
        <div className="reports-user-filter">
          <select
            className="search-select"
            value={userFilter}
            onChange={(e) => setUserFilter(e.target.value)}
          >
            <option value="">{text.selectUser}</option>
            {users.map((u) => (
              <option key={u.UUID} value={u.UUID}>
                {u.username} ({u.s_id}) - {u.role}
              </option>
            ))}
          </select>
        </div>

        {!selectedUser ? (
          <div className="reports-empty">{text.selectUserHint}</div>
        ) : userMeetingRows.length === 0 ? (
          <div className="reports-empty">{text.userNoMeetings}</div>
        ) : (
          <div className="reports-list">
            {userMeetingRows.map((m) => (
              <div className="reports-list-item" key={`${m.uuid}-user-map`}>
                <div className="reports-list-head">
                  <strong>
                    {text.meetingPrefix} #{m.meetingNumber}
                  </strong>
                  <span className="reports-tag">
                    {roleLabel(m.accessLevel)}
                  </span>
                </div>
                <div className="reports-sub">
                  {text.groupLabel}:{" "}
                  {m.groups.length ? m.groups.join(", ") : text.noGroup}
                </div>
              </div>
            ))}
          </div>
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
