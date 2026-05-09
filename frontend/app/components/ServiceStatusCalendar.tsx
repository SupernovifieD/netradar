import { DailyServiceSummary } from "@/types/service";

type StatusKey = "UP" | "DEGRADED" | "DOWN" | "NO_DATA";

interface CalendarCell {
  key: string;
  dayLabel: string;
  dayUtc: string;
  status: StatusKey | null;
  isToday: boolean;
  isFuture: boolean;
}

const dayNumberFormatter = new Intl.DateTimeFormat("en-US", { day: "numeric" });
const monthTitleFormatter = new Intl.DateTimeFormat("en-US", { month: "long", year: "numeric" });
const weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function addDays(date: Date, days: number): Date {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}

function normalizeDate(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function formatDayUtc(date: Date): string {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function isSameDay(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

function buildCurrentMonthCalendar(
  summaries: DailyServiceSummary[]
): { monthTitle: string; cells: Array<CalendarCell | null> } {
  const today = normalizeDate(new Date());
  const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
  const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);

  const summaryStatusByDay = new Map<string, StatusKey>();
  for (const summary of summaries) {
    if (
      summary.overall_status === "UP" ||
      summary.overall_status === "DEGRADED" ||
      summary.overall_status === "DOWN" ||
      summary.overall_status === "NO_DATA"
    ) {
      summaryStatusByDay.set(summary.day_utc, summary.overall_status);
    }
  }

  const cells: Array<CalendarCell | null> = [];
  for (let index = 0; index < firstDay.getDay(); index += 1) {
    cells.push(null);
  }

  for (let day = firstDay; day <= lastDay; day = addDays(day, 1)) {
    const dayUtc = formatDayUtc(day);
    cells.push({
      key: dayUtc,
      dayLabel: dayNumberFormatter.format(day),
      dayUtc,
      status: summaryStatusByDay.get(dayUtc) ?? null,
      isToday: isSameDay(day, today),
      isFuture: day > today,
    });
  }

  while (cells.length % 7 !== 0) {
    cells.push(null);
  }

  return {
    monthTitle: monthTitleFormatter.format(today),
    cells,
  };
}

export default function ServiceStatusCalendar({ summaries }: { summaries: DailyServiceSummary[] }) {
  const { monthTitle, cells } = buildCurrentMonthCalendar(summaries);

  return (
    <div className="box service-calendar-box">
      <div className="service-calendar-header">
        <h3>Daily status</h3>
        <div className="service-calendar-month">{monthTitle}</div>
      </div>

      <div className="service-calendar-weekdays">
        {weekdays.map((weekday) => (
          <div key={weekday} className="service-calendar-weekday">
            {weekday}
          </div>
        ))}
      </div>

      <div className="service-calendar-grid">
        {cells.map((cell, index) => {
          if (!cell) {
            return <div key={`empty-${index}`} className="service-calendar-cell service-calendar-cell--empty" />;
          }

          const statusClass =
            cell.isFuture
              ? "service-calendar-cell--future"
              : cell.status === "UP"
                ? "service-calendar-cell--up"
                : cell.status === "DEGRADED"
                  ? "service-calendar-cell--degraded"
                  : cell.status === "DOWN"
                    ? "service-calendar-cell--down"
                    : cell.status === "NO_DATA"
                      ? "service-calendar-cell--nodata"
                    : "service-calendar-cell--nodata";

          return (
            <div
              key={cell.key}
              className={`service-calendar-cell ${statusClass} ${cell.isToday ? "service-calendar-cell--today" : ""}`}
              title={cell.dayUtc}
            >
              {cell.dayLabel}
            </div>
          );
        })}
      </div>

      <div className="service-calendar-legend" aria-label="Daily status color legend">
        <div className="service-calendar-legend-item">
          <span className="service-calendar-dot service-calendar-dot--up" />
          Stable day
        </div>
        <div className="service-calendar-legend-item">
          <span className="service-calendar-dot service-calendar-dot--degraded" />
          Degraded day
        </div>
        <div className="service-calendar-legend-item">
          <span className="service-calendar-dot service-calendar-dot--down" />
          Outage day
        </div>
        <div className="service-calendar-legend-item">
          <span className="service-calendar-dot service-calendar-dot--nodata" />
          No data day
        </div>
      </div>
    </div>
  );
}
