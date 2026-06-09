// ============================================================================
// CMS Mock Data - נתוני CMS מדומים
// ============================================================================
// קובץ זה מדמה שרת CMS חיצוני עם נתוני ישיבות.
// בעתיד יוחלף בקריאות API אמיתיות לשרת CMS.
//
// פונקציות:
//   - getMockCmsMeetings(type)       - מחזיר ישיבות לפי סוג
//   - getMockCmsMeetingById(id)      - מחזיר ישיבה לפי meetingId
//   - createMockCmsMeeting(data)     - יוצר ישיבה חדשה
//   - updateMockCmsMeetingPassword() - מעדכן סיסמה
//   - deleteMockCmsMeeting()         - מוחק ישיבה (admin/super_admin בלבד)
//
// כל הפונקציות מדמות delay של 300ms כמו קריאת רשת.
// ============================================================================

let CMS_MEETINGS = [
  {
    id: "cms-1001",
    meetingId: "891245",
    name: "Command Audio Bridge",
    type: "audio",
    group: "Operations",
    accessLevel: "audio",
    status: "active",
    participantsCount: 12,
    duration: 34,
    lastUsedAt: "2026-03-22T08:40:00Z",
    password: "AUDIO-7781",
    passwordMasked: "******",
    cmsNode: "CMS-DC-1",
  },
  {
    id: "cms-1002",
    meetingId: "891246",
    name: "Daily Ops Audio",
    type: "audio",
    group: "NOC",
    accessLevel: "audio",
    status: "idle",
    participantsCount: 0,
    duration: 0,
    lastUsedAt: "2026-04-05T16:20:00Z",
    password: "AUDIO-3394",
    passwordMasked: "******",
    cmsNode: "CMS-DC-2",
  },
  {
    id: "cms-2001",
    meetingId: "771110",
    name: "Leadership Video Room",
    type: "video",
    group: "Management",
    accessLevel: "video",
    status: "active",
    participantsCount: 7,
    duration: 52,
    lastUsedAt: "2026-04-05T09:05:00Z",
    password: "VIDEO-2288",
    passwordMasked: "******",
    cmsNode: "CMS-DC-1",
  },
  {
    id: "cms-2002",
    meetingId: "771111",
    name: "Training Video Hall",
    type: "video",
    group: "HR",
    accessLevel: "video",
    status: "scheduled",
    participantsCount: 0,
    duration: 0,
    lastUsedAt: "2026-04-05T12:35:00Z",
    password: "VIDEO-9915",
    passwordMasked: "******",
    cmsNode: "CMS-DC-3",
  },
  {
    id: "cms-3001",
    meetingId: "551900",
    name: "Mass Notification Dialout",
    type: "blast_dial",
    group: "Emergency",
    accessLevel: "blast_dial",
    status: "active",
    participantsCount: 24,
    duration: 9,
    lastUsedAt: "2026-04-05T07:55:00Z",
    password: "BLAST-1044",
    passwordMasked: "******",
    cmsNode: "CMS-DC-2",
  },
  {
    id: "cms-3002",
    meetingId: "551901",
    name: "Legacy Blast Group",
    type: "blast_dial",
    group: "NOT IN USE",
    accessLevel: "blast_dial",
    status: "not_in_use",
    participantsCount: 0,
    duration: 0,
    lastUsedAt: "2026-04-05T05:10:00Z",
    password: "BLAST-0000",
    passwordMasked: "******",
    cmsNode: "CMS-DC-3",
    
  },
];

// פונקציית עזר - מדמה השהיה של קריאת רשת
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// מחזיר את כל הישיבות, או מסנן לפי סוג (audio/video/blast_dial)
export async function getMockCmsMeetings(type) {
  await wait(300);
  if (!type) {
    return CMS_MEETINGS;
  }
  return CMS_MEETINGS.filter((meeting) => meeting.type === type);
}

// מחזיר ישיבה בודדת לפי meetingId
export async function getMockCmsMeetingById(meetingId) {
  await wait(300);
  return (
    CMS_MEETINGS.find((meeting) => meeting.meetingId === meetingId) || null
  );
}

// יוצר ישיבה חדשה ב-CMS. אם כבר קיימת - מחזיר אותה
export async function createMockCmsMeeting(meetingData) {
  await wait(300);

  const meetingId = String(meetingData?.meetingId || "").trim();
  if (!meetingId) {
    return null;
  }

  const existing = CMS_MEETINGS.find((meeting) => meeting.meetingId === meetingId);
  if (existing) {
    return existing;
  }

  const type = meetingData?.type || "audio";
  const passwordPrefix =
    type === "video" ? "VIDEO" : type === "blast_dial" ? "BLAST" : "AUDIO";

  const randomSuffix = Math.floor(1000 + Math.random() * 9000);
  const password = `${passwordPrefix}-${randomSuffix}`;

  const nextNumericId = CMS_MEETINGS.reduce((max, meeting) => {
    const parsed = Number(String(meeting.id || "").replace("cms-", ""));
    return Number.isFinite(parsed) ? Math.max(max, parsed) : max;
  }, 3000) + 1;

  const created = {
    id: `cms-${nextNumericId}`,
    meetingId,
    name: meetingData?.name || `Meeting ${meetingId}`,
    type,
    group: meetingData?.group || "Unassigned",
    accessLevel: type,
    status: "idle",
    participantsCount: 0,
    duration: 0,
    lastUsedAt: new Date().toISOString(),
    password,
    passwordMasked: "******",
    cmsNode: meetingData?.cmsNode || "CMS-LOCAL-1",
  };

  CMS_MEETINGS.unshift(created);
  return created;
}

// מעדכן סיסמת ישיבה ב-CMS
export async function updateMockCmsMeetingPassword(meetingId, newPassword) {
  await wait(300);

  const meeting = CMS_MEETINGS.find((item) => item.meetingId === meetingId);
  if (!meeting) {
    return null;
  }

  meeting.password = newPassword;
  meeting.passwordMasked = newPassword ? "******" : "-";
  meeting.lastUsedAt = new Date().toISOString();

  return meeting;
}

// מוחק ישיבה מה-CMS. רק admin (בעלי הקבוצה) או super_admin יכולים למחוק
export async function deleteMockCmsMeeting(meetingId, actor = null) {
  await wait(300);

  const index = CMS_MEETINGS.findIndex((item) => item.meetingId === meetingId);
  if (index === -1) {
    return { deleted: false, reason: "not_found" };
  }

  const meeting = CMS_MEETINGS[index];
  const role = actor?.role || "";

  if (role !== "super_admin" && role !== "admin") {
    return { deleted: false, reason: "forbidden" };
  }

  if (role === "admin") {
    const ownedGroups = (actor?.ownedGroups || []).map((name) =>
      (name || "").toLowerCase().trim()
    );
    const meetingGroup = (meeting.group || "").toLowerCase().trim();

    if (!ownedGroups.includes(meetingGroup)) {
      return { deleted: false, reason: "forbidden" };
    }
  }

  CMS_MEETINGS.splice(index, 1);
  return { deleted: true, reason: "ok" };
}
