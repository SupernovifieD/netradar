import "./globals.css";
import { frontendConfig, statusTimelineConfig } from "@/lib/config";
import type { CSSProperties } from "react";

export const metadata = {
  title: "NetRadar",
  description: "Availability and performance dashboard for internet services",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const cssVars: Record<string, string> = {
    "--timeline-green": statusTimelineConfig.tokens.green.hex,
    "--timeline-darkgreen": statusTimelineConfig.tokens.darkgreen.hex,
    "--timeline-orange": statusTimelineConfig.tokens.orange.hex,
    "--timeline-blue": statusTimelineConfig.tokens.blue.hex,
    "--timeline-darkblue": statusTimelineConfig.tokens.darkblue.hex,
    "--timeline-red": statusTimelineConfig.tokens.red.hex,
    "--timeline-grey": statusTimelineConfig.tokens.grey.hex,
    "--calendar-up-bg": frontendConfig.calendarColors.upCellBg,
    "--calendar-up-fg": frontendConfig.calendarColors.upCellFg,
    "--calendar-degraded-bg": frontendConfig.calendarColors.degradedCellBg,
    "--calendar-degraded-fg": frontendConfig.calendarColors.degradedCellFg,
    "--calendar-down-bg": frontendConfig.calendarColors.downCellBg,
    "--calendar-down-fg": frontendConfig.calendarColors.downCellFg,
    "--calendar-nodata-bg": frontendConfig.calendarColors.nodataCellBg,
    "--calendar-nodata-fg": frontendConfig.calendarColors.nodataCellFg,
    "--calendar-future-bg": frontendConfig.calendarColors.futureCellBg,
    "--calendar-future-fg": frontendConfig.calendarColors.futureCellFg,
    "--calendar-today-ring": frontendConfig.calendarColors.todayRing,
  };

  return (
    <html lang="en" dir="ltr">
      <body style={cssVars as CSSProperties}>
        <div className="page-wrapper">
          {children}
        </div>
      </body>
    </html>
  );
}
