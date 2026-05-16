import rawConfig from "@/netradar.config.json";

type JsonObject = Record<string, unknown>;

function asObject(value: unknown): JsonObject {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as JsonObject) : {};
}

function readNumber(
  object: JsonObject,
  key: string,
  fallback: number,
  minimum = Number.NEGATIVE_INFINITY
): number {
  const value = object[key];
  if (typeof value !== "number" || !Number.isFinite(value)) return fallback;
  return value < minimum ? minimum : value;
}

function readString(object: JsonObject, key: string, fallback: string): string {
  const value = object[key];
  return typeof value === "string" && value.trim() ? value : fallback;
}

const defaults = {
  statusTimeline: {
    upStableThresholdPct: 80,
    upDegradedThresholdPct: 20,
    highLatencyThresholdMs: 40,
    fallbackToken: "grey",
    outageToken: "red",
    tokens: {
      green: { hex: "#2ecc71", label: "Stable" },
      darkgreen: { hex: "#1e8c4e", label: "Minor instability" },
      orange: { hex: "#e67e22", label: "High latency" },
      blue: { hex: "#3498db", label: "No ping data" },
      darkblue: { hex: "#1f5f8b", label: "Partial response" },
      red: { hex: "#e74c3c", label: "Outage" },
      grey: { hex: "#555", label: "No data" },
    },
  },
  frontend: {
    api: {
      defaultBrowserBase: "/api",
      defaultServerBase: "http://localhost:5001/api",
      defaultInternalBase: "http://localhost:5001/api",
    },
    timeline: {
      bucketCount: 48,
      mobileBucketCount: 24,
      bucketWindowMinutes: 30,
      outageConsecutiveRedBuckets: 4,
      markerEveryBuckets: 4,
    },
    serviceData: {
      historyLimit: 8000,
      dailyLimit: 120,
      defaultExportDays: 90,
    },
    refresh: {
      serviceListMs: 60_000,
      serviceDetailMs: 120_000,
      clockMs: 1_000,
    },
    charts: {
      strokes: {
        latency: "#4ea3ff",
        jitter: "#ffd166",
      },
    },
    supportHighlight: {
      minDelayMs: 15_000,
      maxDelayMs: 45_000,
      pulseDurationMs: 2_000,
    },
    calendarColors: {
      upCellBg: "#1e8c4e",
      upCellFg: "#ebfff3",
      degradedCellBg: "#a0611f",
      degradedCellFg: "#fff5ea",
      downCellBg: "#8f2d27",
      downCellFg: "#ffecec",
      nodataCellBg: "#d9d9d9",
      nodataCellFg: "#3f3f3f",
      futureCellBg: "#252525",
      futureCellFg: "#9f9f9f",
      todayRing: "#f2f2f2",
    },
  },
} as const;

const root = asObject(rawConfig);

const shared = asObject(root.shared);
const sharedStatusTimeline = asObject(shared.status_timeline);
const sharedTimelineTokens = asObject(sharedStatusTimeline.tokens);

const frontend = asObject(root.frontend);
const frontendApi = asObject(frontend.api);
const frontendTimeline = asObject(frontend.timeline);
const frontendServiceData = asObject(frontend.service_data);
const frontendRefresh = asObject(frontend.refresh);
const frontendCharts = asObject(frontend.charts);
const frontendChartStrokes = asObject(asObject(frontendCharts.strokes));
const frontendSupportHighlight = asObject(frontend.support_highlight);
const frontendCalendarColors = asObject(frontend.calendar_colors);

const statusTimelineTokens = Object.fromEntries(
  Object.entries(defaults.statusTimeline.tokens).map(([token, fallback]) => {
    const rawToken = asObject(sharedTimelineTokens[token]);
    return [
      token,
      {
        hex: readString(rawToken, "hex", fallback.hex),
        label: readString(rawToken, "label", fallback.label),
      },
    ];
  })
) as typeof defaults.statusTimeline.tokens;

export type StatusTimelineToken = keyof typeof statusTimelineTokens;

export const statusTimelineConfig = {
  upStableThresholdPct: readNumber(
    sharedStatusTimeline,
    "up_stable_threshold_pct",
    defaults.statusTimeline.upStableThresholdPct,
    0
  ),
  upDegradedThresholdPct: readNumber(
    sharedStatusTimeline,
    "up_degraded_threshold_pct",
    defaults.statusTimeline.upDegradedThresholdPct,
    0
  ),
  highLatencyThresholdMs: readNumber(
    sharedStatusTimeline,
    "high_latency_threshold_ms",
    defaults.statusTimeline.highLatencyThresholdMs,
    0
  ),
  fallbackToken: readString(sharedStatusTimeline, "fallback_token", defaults.statusTimeline.fallbackToken),
  outageToken: readString(sharedStatusTimeline, "outage_token", defaults.statusTimeline.outageToken),
  tokens: statusTimelineTokens,
} as const;

export const frontendConfig = {
  api: {
    defaultBrowserBase: readString(
      frontendApi,
      "default_browser_base",
      defaults.frontend.api.defaultBrowserBase
    ),
    defaultServerBase: readString(frontendApi, "default_server_base", defaults.frontend.api.defaultServerBase),
    defaultInternalBase: readString(
      frontendApi,
      "default_internal_base",
      defaults.frontend.api.defaultInternalBase
    ),
  },
  timeline: {
    bucketCount: readNumber(frontendTimeline, "bucket_count", defaults.frontend.timeline.bucketCount, 1),
    mobileBucketCount: readNumber(
      frontendTimeline,
      "mobile_bucket_count",
      defaults.frontend.timeline.mobileBucketCount,
      1
    ),
    bucketWindowMinutes: readNumber(
      frontendTimeline,
      "bucket_window_minutes",
      defaults.frontend.timeline.bucketWindowMinutes,
      1
    ),
    outageConsecutiveRedBuckets: readNumber(
      frontendTimeline,
      "outage_consecutive_red_buckets",
      defaults.frontend.timeline.outageConsecutiveRedBuckets,
      1
    ),
    markerEveryBuckets: readNumber(
      frontendTimeline,
      "marker_every_buckets",
      defaults.frontend.timeline.markerEveryBuckets,
      1
    ),
  },
  serviceData: {
    historyLimit: readNumber(frontendServiceData, "history_limit", defaults.frontend.serviceData.historyLimit, 1),
    dailyLimit: readNumber(frontendServiceData, "daily_limit", defaults.frontend.serviceData.dailyLimit, 1),
    defaultExportDays: readNumber(
      frontendServiceData,
      "default_export_days",
      defaults.frontend.serviceData.defaultExportDays,
      1
    ),
  },
  refresh: {
    serviceListMs: readNumber(frontendRefresh, "service_list_ms", defaults.frontend.refresh.serviceListMs, 1000),
    serviceDetailMs: readNumber(
      frontendRefresh,
      "service_detail_ms",
      defaults.frontend.refresh.serviceDetailMs,
      1000
    ),
    clockMs: readNumber(frontendRefresh, "clock_ms", defaults.frontend.refresh.clockMs, 100),
  },
  charts: {
    strokes: {
      latency: readString(
        frontendChartStrokes,
        "latency",
        defaults.frontend.charts.strokes.latency
      ),
      jitter: readString(frontendChartStrokes, "jitter", defaults.frontend.charts.strokes.jitter),
    },
  },
  supportHighlight: {
    minDelayMs: readNumber(
      frontendSupportHighlight,
      "min_delay_ms",
      defaults.frontend.supportHighlight.minDelayMs,
      0
    ),
    maxDelayMs: readNumber(
      frontendSupportHighlight,
      "max_delay_ms",
      defaults.frontend.supportHighlight.maxDelayMs,
      0
    ),
    pulseDurationMs: readNumber(
      frontendSupportHighlight,
      "pulse_duration_ms",
      defaults.frontend.supportHighlight.pulseDurationMs,
      0
    ),
  },
  calendarColors: {
    upCellBg: readString(frontendCalendarColors, "up_cell_bg", defaults.frontend.calendarColors.upCellBg),
    upCellFg: readString(frontendCalendarColors, "up_cell_fg", defaults.frontend.calendarColors.upCellFg),
    degradedCellBg: readString(
      frontendCalendarColors,
      "degraded_cell_bg",
      defaults.frontend.calendarColors.degradedCellBg
    ),
    degradedCellFg: readString(
      frontendCalendarColors,
      "degraded_cell_fg",
      defaults.frontend.calendarColors.degradedCellFg
    ),
    downCellBg: readString(frontendCalendarColors, "down_cell_bg", defaults.frontend.calendarColors.downCellBg),
    downCellFg: readString(frontendCalendarColors, "down_cell_fg", defaults.frontend.calendarColors.downCellFg),
    nodataCellBg: readString(
      frontendCalendarColors,
      "nodata_cell_bg",
      defaults.frontend.calendarColors.nodataCellBg
    ),
    nodataCellFg: readString(
      frontendCalendarColors,
      "nodata_cell_fg",
      defaults.frontend.calendarColors.nodataCellFg
    ),
    futureCellBg: readString(
      frontendCalendarColors,
      "future_cell_bg",
      defaults.frontend.calendarColors.futureCellBg
    ),
    futureCellFg: readString(
      frontendCalendarColors,
      "future_cell_fg",
      defaults.frontend.calendarColors.futureCellFg
    ),
    todayRing: readString(frontendCalendarColors, "today_ring", defaults.frontend.calendarColors.todayRing),
  },
} as const;

export function statusTokenToHex(token: string): string {
  const entry = statusTimelineConfig.tokens[token as StatusTimelineToken];
  if (entry) return entry.hex;
  const fallback = statusTimelineConfig.tokens[statusTimelineConfig.fallbackToken as StatusTimelineToken];
  return fallback ? fallback.hex : "#444";
}

export function statusTokenToLabel(token: string): string {
  const entry = statusTimelineConfig.tokens[token as StatusTimelineToken];
  if (entry) return entry.label;
  return "Unknown";
}
