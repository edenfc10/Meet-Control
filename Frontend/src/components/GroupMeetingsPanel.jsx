import { useMemo, useState, useEffect } from "react";
import { groupAPI, meetingAPI } from "../services/api";

export default function GroupMeetingsPanel({
  language,
  selectedGroup,
  setSelectedGroup,
  allMeetings,
  setAllMeetings,
  groups,
  setGroups,
  setModalError,
  currentUser,
}) {
  const isHebrew = language === "he";

  const accessLevelLabels = {
    audio: isHebrew ? "ועידות אודיו" : "audio",
    video: isHebrew ? "ועידות וידאו" : "video",
    blast_dial: isHebrew ? "ועידות הזנקה" : "blast_dial",
  };
  const formatAccessLevel = (level) => accessLevelLabels[level] || level;

  const text = {
    meetings: isHebrew ? "הוספת ועידות" : "Add Meetings",
    meetingNumber: isHebrew ? "מספר ועידה" : "Meeting #",
    type: isHebrew ? "סוג" : "Type",
    remove: isHebrew ? "הסר" : "Remove",
    add: isHebrew ? "הוסף" : "Add",
    adding: isHebrew ? "מוסיף..." : "Adding...",
    noMeetingsToAdd: isHebrew ? "אין ועידות זמינות להוספה." : "No meetings available to add.",
    noMatchingMeetings: isHebrew ? "לא נמצאו ועידות מתאימות." : "No matching meetings.",
    meetingUnavailable: isHebrew ? "הוועידה הזאת לא זמינה לקבוצה הזו." : "This meeting is not available for this group.",
    addMeetingError: isHebrew ? "הוספת הוועידה נכשלה." : "Failed to add meeting.",
    removeMeetingError: isHebrew ? "הסרת הוועידה נכשלה." : "Failed to remove meeting.",
  };

  const [addMeetingId, setAddMeetingId] = useState("");
  const [addMeetingLoading, setAddMeetingLoading] = useState(false);
  const [searchMeetingText, setSearchMeetingText] = useState("");
  const [meetingTypeFilter, setMeetingTypeFilter] = useState("all");

  useEffect(() => {
    setAddMeetingId("");
    setSearchMeetingText("");
    setMeetingTypeFilter("all");
  }, [selectedGroup?.UUID]);

  const selectedGroupMeetingKeys = useMemo(() => {
    return new Set((selectedGroup?.meetings || []).map((id) => String(id)));
  }, [selectedGroup?.meetings]);

  const addableMeetingsForSelectedGroup = useMemo(() => {
    return (allMeetings || []).filter((meeting) => {
      const compositeKey = `${meeting.m_number}:${(meeting.accessLevel || "").toLowerCase()}`;
      if (selectedGroupMeetingKeys.has(compositeKey)) return false;
      if (currentUser?.role === "admin") {
        const mt = (meeting.accessLevel || "").toLowerCase();
        if (mt === "audio" && !currentUser?.can_audio) return false;
        if (mt === "video" && !currentUser?.can_video) return false;
      }
      if (meetingTypeFilter !== "all") {
        if ((meeting.accessLevel || "").toLowerCase() !== meetingTypeFilter) return false;
      }
      return true;
    });
  }, [allMeetings, selectedGroupMeetingKeys, currentUser, meetingTypeFilter]);

  const filteredAddableMeetings = useMemo(() => {
    const q = searchMeetingText.trim().toLowerCase();
    if (!q) return addableMeetingsForSelectedGroup;
    return addableMeetingsForSelectedGroup.filter(
      (m) =>
        String(m.m_number).toLowerCase().includes(q) ||
        (m.name || "").toLowerCase().includes(q) ||
        (m.accessLevel || "").toLowerCase().startsWith(q)
    );
  }, [addableMeetingsForSelectedGroup, searchMeetingText]);

  useEffect(() => {
    if (!addMeetingId) return;
    const stillAvailable = addableMeetingsForSelectedGroup.some(
      (m) => `${m.m_number}:${(m.accessLevel || "").toLowerCase()}` === String(addMeetingId)
    );
    if (!stillAvailable) setAddMeetingId("");
  }, [addMeetingId, addableMeetingsForSelectedGroup]);

  const refreshGroups = async () => {
    const resp = await groupAPI.listGroups();
    const updated = (resp.data || []).find((g) => g.UUID === selectedGroup.UUID);
    if (updated) {
      setSelectedGroup(updated);
      setGroups(resp.data || []);
    }
  };

  const handleAddMeeting = async () => {
    if (!addMeetingId || !selectedGroup) return;
    const selectedMeeting = addableMeetingsForSelectedGroup.find(
      (m) => `${m.m_number}:${(m.accessLevel || "").toLowerCase()}` === String(addMeetingId)
    );
    if (!selectedMeeting) { setModalError(text.meetingUnavailable); return; }
    setAddMeetingLoading(true);
    setModalError("");
    try {
      await groupAPI.addMeeting(selectedGroup.UUID, selectedMeeting.m_number, selectedMeeting.accessLevel);
      setAddMeetingId("");
      await refreshGroups();
      const meetingsResp = await meetingAPI.getAllMeetings();
      setAllMeetings(meetingsResp.data || []);
    } catch (err) {
      setModalError(err.response?.data?.detail || text.addMeetingError);
    } finally {
      setAddMeetingLoading(false);
    }
  };

  const handleRemoveMeeting = async (mNumber, accessLevel) => {
    if (!selectedGroup) return;
    setModalError("");
    try {
      await groupAPI.removeMeeting(selectedGroup.UUID, mNumber, accessLevel);
      await refreshGroups();
    } catch (err) {
      setModalError(err.response?.data?.detail || text.removeMeetingError);
    }
  };

  const totalUnassigned = allMeetings.filter(
    (m) => !selectedGroupMeetingKeys.has(`${m.m_number}:${(m.accessLevel || "").toLowerCase()}`)
  ).length;

  const selMeeting = addMeetingId
    ? allMeetings.find((m) => `${m.m_number}:${(m.accessLevel || "").toLowerCase()}` === String(addMeetingId))
    : null;

  return (
    <div className="groups-modal-section">
      <h4>{text.meetings} ({selectedGroup.meetings?.length ?? 0})</h4>

      {/* פגישות קיימות */}
      {selectedGroup.meetings?.length > 0 && (
        <table className="groups-table">
          <thead>
            <tr>
              <th>{text.meetingNumber}</th>
              <th>{isHebrew ? "שם" : "Name"}</th>
              <th>{text.type}</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {selectedGroup.meetings.map((compositeKey) => {
              const [mNum, mType] = String(compositeKey).split(":");
              const meeting = allMeetings.find(
                (m) => String(m.m_number) === mNum && (m.accessLevel || "").toLowerCase() === (mType || "").toLowerCase()
              );
              return (
                <tr key={compositeKey}>
                  <td>{meeting ? `#${meeting.m_number}` : `#${mNum}`}</td>
                  <td style={{ maxWidth: 160, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {meeting?.name || "—"}
                  </td>
                  <td>{meeting ? formatAccessLevel(meeting.accessLevel) : formatAccessLevel(mType)}</td>
                  <td>
                    <button className="btn-danger btn-sm" onClick={() => handleRemoveMeeting(mNum, mType)}>
                      {text.remove}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}

      {/* הוספת פגישה */}
      {totalUnassigned === 0 ? (
        <div className="groups-empty">{text.noMeetingsToAdd}</div>
      ) : (
        <div className="groups-add-row groups-add-meeting-row">
          {selMeeting && (
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8, padding: "5px 10px", background: "#f0f4ff", borderRadius: 6, fontSize: "0.85em", border: "1px solid #c5d0f5" }}>
              <span style={{ fontWeight: 600 }}>#{selMeeting.m_number}</span>
              <span style={{ color: "#888" }}>({formatAccessLevel(selMeeting.accessLevel)})</span>
              <button type="button" onClick={() => setAddMeetingId("")} style={{ marginLeft: "auto", background: "none", border: "none", cursor: "pointer", color: "#888", fontSize: "1em", lineHeight: 1 }}>✕</button>
            </div>
          )}
          <div style={{ display: "flex", gap: 8, marginBottom: 6 }}>
            <select
              className="meetings-filter-select"
              value={meetingTypeFilter}
              onChange={(e) => { setMeetingTypeFilter(e.target.value); setAddMeetingId(""); }}
              style={{ minWidth: 110 }}
            >
              <option value="all">{isHebrew ? "כל הסוגים" : "All types"}</option>
              <option value="audio">{isHebrew ? "אודיו" : "Audio"}</option>
              <option value="video">{isHebrew ? "וידאו" : "Video"}</option>
              <option value="blast_dial">{isHebrew ? "הזנקה" : "Blast Dial"}</option>
            </select>
          </div>
          <div className="groups-search-select" role="group">
            <input
              className="groups-search-select-input"
              type="text"
              placeholder={isHebrew ? "חיפוש לפי מספר, שם או סוג..." : "Search by number, name or type..."}
              value={searchMeetingText}
              onChange={(e) => setSearchMeetingText(e.target.value)}
              aria-label="Search meetings"
            />
            <div className="groups-search-select-list" role="listbox" aria-label="Available meetings">
              {filteredAddableMeetings.length > 0 ? (
                filteredAddableMeetings.map((m) => {
                  const compositeKey = `${m.m_number}:${(m.accessLevel || "").toLowerCase()}`;
                  const selected = String(addMeetingId) === compositeKey;
                  return (
                    <button
                      key={compositeKey}
                      type="button"
                      role="option"
                      aria-selected={selected}
                      className={`groups-search-select-option ${selected ? "is-selected" : ""}`}
                      onClick={() => { setAddMeetingId(compositeKey); setSearchMeetingText(""); }}
                    >
                      #{m.m_number}{m.name ? ` — ${m.name}` : ""} ({formatAccessLevel(m.accessLevel)})
                    </button>
                  );
                })
              ) : (
                <div className="groups-empty" style={{ padding: "8px" }}>
                  {searchMeetingText || meetingTypeFilter !== "all" ? text.noMatchingMeetings : ""}
                </div>
              )}
            </div>
          </div>
          <button
            className="btn-primary"
            onClick={handleAddMeeting}
            disabled={addMeetingLoading || !addMeetingId}
          >
            {addMeetingLoading ? text.adding : text.add}
          </button>
        </div>
      )}
    </div>
  );
}
