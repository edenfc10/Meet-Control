// ============================================================================
// Help Page - מדריך מלא למשתמש עם הסבר על המערכת, מודולים, הרשאות ושאלות נפוצות
// ============================================================================

import { useAuth } from "../context/AuthContext";

export default function Help({ language = "en" }) {
  const { currentUser } = useAuth();
  const isHebrew = language === "he";
  const role = currentUser?.role;
  const canAudio = currentUser?.can_audio ?? false;
  const canVideo = currentUser?.can_video ?? false;

  const meetingType = canAudio && canVideo
    ? (isHebrew ? "אודיו ווידאו" : "audio and video")
    : canAudio
      ? (isHebrew ? "אודיו" : "audio")
      : canVideo
        ? (isHebrew ? "וידאו" : "video")
        : (isHebrew ? "לא מוגדר" : "not set");

  const t = isHebrew ? {
    title: "עזרה",
    systemTitle: "אודות המערכת",
    systemDesc: "Meet-Control היא מערכת לניהול פגישות ועידה על שרתי Cisco Meeting Server (CMS). המערכת מתחברת ל-CMS ומאפשרת ניהול מרכזי של פגישות אודיו, וידאו והזנקה, ניהול משתמשים, מדורים, דוחות ומועדפים - הכל מממשק אחד.",
    modulesTitle: "מודולים עיקריים",
    modules: [
      { name: "לוח בקרה (Dashboard)", desc: "תצוגת סטטיסטיקות חיות - מספר פגישות פעילות, משתתפים מחוברים, ומועדפים אישיים. מתעדכן אוטומטית כל 30 שניות." },
      { name: "פגישות", desc: "יצירה, עריכה, מחיקה וחיפוש פגישות לפי מספר או שם. כל פגישה מקבלת מספר ייחודי שמשמש כמזהה (callId) בשרת CMS. ניתן לקבוע סיסמה לפגישה (מינימום 8 ספרות)." },
      { name: "מדורים (Groups)", desc: "יצירת קבוצות, שיוך חברים עם רמת גישה (אודיו/וידאו/הזנקה), ושיוך פגישות לקבוצה. מאפשר ארגון והרשאות מדויקות לכל משתמש." },
      { name: "מועדפים", desc: "סימון פגישות כמועדפות לגישה מהירה מה-Dashboard. המועדפים מוצגים בלוח הבקרה ומתעדכנים אוטומטית." },
      { name: "דוחות", desc: "דוחות שימוש וסטטיסטיקות על פגישות ופעילות במערכת." },
      { name: "משתמשים", desc: "ניהול משתמשים - יצירה, עריכה ומחיקה. זמין ל-super_admin ו-admin בלבד." },
      { name: "שרתים", desc: "ניהול שרתי CMS - הוספה, עריכה ומחיקה. זמין ל-super_admin בלבד." },
    ],
    rolesTitle: "הרשאות לפי תפקיד",
    yourRole: "התפקיד שלך",
    yourMeetingType: "סוג פגישות מורשה",
    roles: {
      super_admin: {
        title: "Super Admin - מנהל על",
        desc: "מנהל על הוא בעל הרשאות מלאות במערכת. יכול לנהל כל דבר.",
        items: [
          "ניהול משתמשים מלא - יצירת admin ו-agent, עריכה ומחיקת משתמשים",
          "ניהול שרתי CMS - הוספה, עריכה ומחיקת שרתים, קביעת עדיפות וסוג",
          "צפייה בלוגים של המערכת - לוגי שגיאות ומידע",
          "ניהול כל סוגי הפגישות - אודיו, וידאו והזנקה (blast-dial)",
          "יצירה, עריכה ומחיקת פגישות מכל סוג",
          "ניהול מדורים - יצירה, עריכה, מחיקה, שיוך חברים ופגישות",
          "צפייה בדוחות",
          "ניהול מועדפים אישיים",
        ],
      },
      admin: {
        title: "Admin - מנהל",
        desc: "מנהל אחראי על סוג פגישות ספציפי (אודיו או וידאו). יכול ליצור agents ולנהל מדורים.",
        items: [
          "יצירת משתמשי agent בלבד - ה-agent יורש את סוג הפגישות של ה-admin היוצר",
          "עריכת משתמשים (לא ניתן לשנות תפקיד לרמה שווה או גבוהה יותר)",
          `ניהול פגישות ${meetingType} בלבד`,
          "יצירה, עריכה ומחיקת פגישות בתחום ההרשאה",
          "ניהול מדורים - יצירה, עריכה, מחיקה, שיוך חברים ופגישות",
          "צפייה בדוחות",
          "ניהול מועדפים אישיים",
        ],
      },
      agent: {
        title: "Agent - סוכן",
        desc: "סוכן הוא משתמש עם הרשאות צפייה בלבד. סוג הפגישות שהוא יכול לראות נקבע על ידי ה-admin שיצר אותו או על ידי שיוך למדור.",
        items: [
          `צפייה בפגישות ${meetingType} בלבד`,
          "צפייה במדורים (Groups) המשויכים אליו בלבד",
          "ניהול מועדפים אישיים - סימון והסרת פגישות ממועדפים",
        ],
      },
    },
    faqTitle: "שאלות נפוצות",
    faqs: [
      { q: "איך יוצרים פגישה חדשה?", a: "נווטו לעמוד הפגישות הרצוי (אודיו/וידאו), לחצו על כפתור 'צור פגישה', מלאו את השם, מספר הפגישה והסיסמה (אופציונלי, מינימום 8 ספרות)." },
      { q: "איך משייכים פגישה למדור?", a: "נווטו לעמוד המדורים, בחרו מדור, ובלשונית 'פגישות' חפשו והוסיפו את הפגישה הרצויה." },
      { q: "איך מוסיפים agent למדור?", a: "נווטו לעמוד המדורים, בחרו מדור, ובלשונית 'חברים' חפשו את ה-agent והוסיפו אותו עם רמת גישה מתאימה." },
      { q: "מה ההבדל בין admin audio ל-admin video?", a: "admin audio יכול לנהל רק פגישות אודיו, ו-admin video יכול לנהל רק פגישות וידאו. כש-admin יוצר agent, ה-agent יורש את סוג הפגישות של ה-admin." },
      { q: "איך מסמנים פגישה כמועדפת?", a: "בעמוד הפגישות, לחצו על סמל הכוכב ליד הפגישה. הפגישה תופיע בלוח הבקרה תחת מועדפים." },
      { q: "מה קורה כששרת CMS לא זמין?", a: "המערכת עוברת אוטומטית לשרת הבא בעדיפות. שרת שנכשל מסומן כ'לא זמין' למשך 2 דקות ואז נבדק מחדש." },
    ],
  } : {
    title: "Help",
    systemTitle: "About the System",
    systemDesc: "Meet-Control is a meeting management system for Cisco Meeting Server (CMS). It connects to CMS and provides centralized management of audio, video, and blast-dial meetings, users, groups, reports, and favorites - all from a single interface.",
    modulesTitle: "Main Modules",
    modules: [
      { name: "Dashboard", desc: "Live statistics - active meetings, connected participants, and personal favorites. Auto-refreshes every 30 seconds." },
      { name: "Meetings", desc: "Create, edit, delete, and search meetings by number or name. Each meeting gets a unique number used as the callId in CMS. Optional password (minimum 8 digits)." },
      { name: "Groups", desc: "Create groups, assign members with access levels (audio/video/blast-dial), and assign meetings to groups. Enables precise per-user permissions." },
      { name: "Favorites", desc: "Mark meetings as favorites for quick access from the Dashboard. Favorites are displayed on the dashboard and auto-update." },
      { name: "Reports", desc: "Usage reports and statistics on meetings and system activity." },
      { name: "Users", desc: "User management - create, edit, and delete. Available to super_admin and admin only." },
      { name: "Servers", desc: "CMS server management - add, edit, and delete. Available to super_admin only." },
    ],
    rolesTitle: "Permissions by Role",
    yourRole: "Your role",
    yourMeetingType: "Permitted meeting type",
    roles: {
      super_admin: {
        title: "Super Admin",
        desc: "Super Admin has full system access. Can manage everything.",
        items: [
          "Full user management - create admins and agents, edit and delete users",
          "CMS server management - add, edit, and delete servers, set priority and type",
          "View system logs - error and info logs",
          "Manage all meeting types - audio, video, and blast-dial",
          "Create, edit, and delete meetings of any type",
          "Group management - create, edit, delete, assign members and meetings",
          "View reports",
          "Manage personal favorites",
        ],
      },
      admin: {
        title: "Admin",
        desc: "Admin is responsible for a specific meeting type (audio or video). Can create agents and manage groups.",
        items: [
          "Create agent users only - the agent inherits the creating admin's meeting type",
          "Edit users (cannot assign equal or higher roles)",
          `Manage ${meetingType} meetings only`,
          "Create, edit, and delete meetings within permitted scope",
          "Group management - create, edit, delete, assign members and meetings",
          "View reports",
          "Manage personal favorites",
        ],
      },
      agent: {
        title: "Agent",
        desc: "Agent is a read-only user. The meeting types they can view are determined by the admin who created them or by group assignments.",
        items: [
          `View ${meetingType} meetings only`,
          "View assigned groups only",
          "Manage personal favorites - add and remove meetings from favorites",
        ],
      },
    },
    faqTitle: "FAQ",
    faqs: [
      { q: "How do I create a new meeting?", a: "Navigate to the desired meetings page (audio/video), click 'Create Meeting', fill in the name, meeting number, and optional password (minimum 8 digits)." },
      { q: "How do I assign a meeting to a group?", a: "Go to the Groups page, select a group, and in the 'Meetings' tab search and add the desired meeting." },
      { q: "How do I add an agent to a group?", a: "Go to the Groups page, select a group, and in the 'Members' tab search for the agent and add them with the appropriate access level." },
      { q: "What is the difference between audio admin and video admin?", a: "Audio admin can only manage audio meetings, and video admin can only manage video meetings. When an admin creates an agent, the agent inherits the admin's meeting type." },
      { q: "How do I mark a meeting as favorite?", a: "On the meetings page, click the star icon next to the meeting. It will appear on the dashboard under favorites." },
      { q: "What happens when a CMS server is unavailable?", a: "The system automatically fails over to the next server by priority. A failed server is marked 'dead' for 2 minutes and then retried automatically." },
    ],
  };

  const section = t.roles[role] || t.roles.agent;

  return (
    <div className="page help-page">
      <h2 className="page-header">{t.title}</h2>

      {/* System Overview */}
      <div className="help-card">
        <h3 className="help-card-title">{t.systemTitle}</h3>
        <p className="help-text">{t.systemDesc}</p>
      </div>

      {/* Modules */}
      <div className="help-card">
        <h3 className="help-card-title">{t.modulesTitle}</h3>
        <div className="help-modules">
          {t.modules.map((mod, idx) => (
            <div key={idx} className="help-module">
              <span className="help-module-name">{mod.name}</span>
              <span className="help-module-desc">{mod.desc}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Role-based permissions */}
      <div className="help-card">
        <h3 className="help-card-title">{t.rolesTitle}</h3>
        <div className="help-role-info">
          <span className="help-role-badge">
            {t.yourRole}: <strong>{role}</strong>
          </span>
          <span className="help-role-badge">
            {t.yourMeetingType}: <strong>{meetingType}</strong>
          </span>
        </div>
        <h4 className="help-section-title">{section.title}</h4>
        <p className="help-text">{section.desc}</p>
        <ul className="help-list">
          {section.items.map((item, idx) => (
            <li key={idx} className="help-list-item">{item}</li>
          ))}
        </ul>
      </div>

      {/* FAQ */}
      <div className="help-card">
        <h3 className="help-card-title">{t.faqTitle}</h3>
        <div className="help-faq">
          {t.faqs.map((faq, idx) => (
            <div key={idx} className="help-faq-item">
              <div className="help-faq-q">{faq.q}</div>
              <div className="help-faq-a">{faq.a}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
