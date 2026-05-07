import { DailyServiceSummary } from "@/types/service";

type StatusKey = "UP" | "DEGRADED" | "DOWN";

interface CalendarCell {
  key: string;
  dayLabel: string;
  dayUtc: string;
  status: StatusKey | null;
  isToday: boolean;
}

const persianYmdNumericFormatter = new Intl.DateTimeFormat("fa-IR-u-ca-persian-nu-latn", {
  year: "numeric",
  month: "numeric",
  day: "numeric",
});

const persianDayFormatter = new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
  day: "numeric",
});

const persianMonthTitleFormatter = new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
  year: "numeric",
  month: "long",
});

const persianWeekdays = ["ش", "ی", "د", "س", "چ", "پ", "ج"];

function addDays(date: Date, days: number): Date {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}

function normalizeDate(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function formatGregorianDay(date: Date): string {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getPersianParts(date: Date): { year: number; month: number; day: number } {
  const parts = persianYmdNumericFormatter.formatToParts(date);
  const year = Number(parts.find((part) => part.type === "year")?.value ?? "0");
  const month = Number(parts.find((part) => part.type === "month")?.value ?? "0");
  const day = Number(parts.find((part) => part.type === "day")?.value ?? "0");
  return { year, month, day };
}

function isSamePersianMonth(a: Date, b: Date): boolean {
  const first = getPersianParts(a);
  const second = getPersianParts(b);
  return first.year === second.year && first.month === second.month;
}

function saturdayBasedWeekIndex(date: Date): number {
  return (date.getDay() + 1) % 7;
}

function isSameGregorianDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

function buildCurrentPersianMonthCalendar(
  summaries: DailyServiceSummary[]
): {
  monthTitle: string;
  cells: Array<CalendarCell | null>;
} {
  const today = normalizeDate(new Date());

  let firstDay = today;
  while (isSamePersianMonth(addDays(firstDay, -1), today)) {
    firstDay = addDays(firstDay, -1);
  }

  let lastDay = today;
  while (isSamePersianMonth(addDays(lastDay, 1), today)) {
    lastDay = addDays(lastDay, 1);
  }

  const summaryStatusByDay = new Map<string, StatusKey>();
  for (const summary of summaries) {
    if (summary.overall_status === "UP" || summary.overall_status === "DEGRADED" || summary.overall_status === "DOWN") {
      summaryStatusByDay.set(summary.day_utc, summary.overall_status);
    }
  }

  const cells: Array<CalendarCell | null> = [];
  const leadingEmpty = saturdayBasedWeekIndex(firstDay);

  for (let index = 0; index < leadingEmpty; index += 1) {
    cells.push(null);
  }

  for (let day = firstDay; day <= lastDay; day = addDays(day, 1)) {
    const dayUtc = formatGregorianDay(day);
    cells.push({
      key: dayUtc,
      dayLabel: persianDayFormatter.format(day),
      dayUtc,
      status: summaryStatusByDay.get(dayUtc) ?? null,
      isToday: isSameGregorianDay(day, today),
    });
  }

  while (cells.length % 7 !== 0) {
    cells.push(null);
  }

  return {
    monthTitle: persianMonthTitleFormatter.format(today),
    cells,
  };
}

export default function PersianStatusCalendar({
  summaries,
}: {
  summaries: DailyServiceSummary[];
}) {
  const { monthTitle, cells } = buildCurrentPersianMonthCalendar(summaries);

  return (
    <div className="box service-calendar-box">
      <div className="service-calendar-header">
        <h3>وضعیت روزانه</h3>
        <div className="service-calendar-month">{monthTitle}</div>
      </div>

      <div className="service-calendar-weekdays">
        {persianWeekdays.map((weekday) => (
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
            cell.status === "UP"
              ? "service-calendar-cell--up"
              : cell.status === "DEGRADED"
                ? "service-calendar-cell--degraded"
                : cell.status === "DOWN"
                  ? "service-calendar-cell--down"
                  : "service-calendar-cell--nodata";

          return (
            <div
              key={cell.key}
              className={`service-calendar-cell ${statusClass} ${cell.isToday ? "service-calendar-cell--today" : ""}`}
              title={`${cell.dayUtc}`}
            >
              {cell.dayLabel}
            </div>
          );
        })}
      </div>

      <div className="service-calendar-legend" aria-label="راهنمای رنگ وضعیت روزانه">
        <div className="service-calendar-legend-item">
          <span className="service-calendar-dot service-calendar-dot--up" />
          روز پایدار
        </div>
        <div className="service-calendar-legend-item">
          <span className="service-calendar-dot service-calendar-dot--degraded" />
          روز ناپایدار
        </div>
        <div className="service-calendar-legend-item">
          <span className="service-calendar-dot service-calendar-dot--down" />
          روز قطع
        </div>
      </div>
    </div>
  );
}
