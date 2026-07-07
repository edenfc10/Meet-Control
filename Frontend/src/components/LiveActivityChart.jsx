import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const labels = {
  en: {
    audio: "Audio",
    video: "Video",
    blast_dial: "Blast Dial",
    meetings: "Meetings",
    participants: "Participants",
  },
  he: {
    audio: "אודיו",
    video: "וידאו",
    blast_dial: "הזנקה",
    meetings: "פגישות",
    participants: "משתתפים",
  },
};

export default function LiveActivityChart({ data = {}, language = "en" }) {
  const text = labels[language] || labels.en;

  const chartData = [
    {
      name: text.audio,
      meetings: data.audio?.meetings ?? 0,
      participants: data.audio?.participants ?? 0,
    },
    {
      name: text.video,
      meetings: data.video?.meetings ?? 0,
      participants: data.video?.participants ?? 0,
    },
    {
      name: text.blast_dial,
      meetings: data.blast_dial?.meetings ?? 0,
      participants: data.blast_dial?.participants ?? 0,
    },
  ];

  const hasData = chartData.some(
    (d) => d.meetings > 0 || d.participants > 0
  );

  if (!hasData) {
    return (
      <div className="live-chart-empty">
        {language === "he" ? "אין נתונים חיים להצגה" : "No live data to display"}
      </div>
    );
  }

  return (
    <div className="live-chart-container" style={{ width: "100%", height: 320 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{ top: 16, right: 16, left: 8, bottom: 8 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="name" tick={{ fontSize: 12 }} />
          <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
          <Tooltip />
          <Legend />
          <Bar
            dataKey="meetings"
            name={text.meetings}
            fill="#3b82f6"
            radius={[4, 4, 0, 0]}
          />
          <Bar
            dataKey="participants"
            name={text.participants}
            fill="#10b981"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
