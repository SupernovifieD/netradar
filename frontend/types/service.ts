export interface ServiceCheck {
  id: number;
  service: string;
  latency: string;
  packet_loss: string;
  dns: string;
  tcp: string;
  status: string;
  probe_reason?: string | null;
  http_status_code?: number | null;
  date: string; // "2026-04-29"
  time: string; // "20:12:51"
}

export interface ServiceMeta {
  id?: string; // optional in current services.json
  name: string; // display name, e.g. "Google"
  domain: string; // e.g. "google.com"
  group: string; // e.g. "International Service"
  category: string; // e.g. "General Services"
}

export interface ServiceBuckets {
  service: string;
  buckets: {
    start: string;
    end: string;
    upPercent: number;
    avgLatency: number | null;
    color: string;
  }[];
}

export interface FullServiceCardData {
  meta: ServiceMeta;
  buckets: ServiceBuckets["buckets"];
}

export interface DailyServiceInterval {
  service: string;
  day_utc: string; // YYYY-MM-DD (UTC day)
  interval_type: "DOWN" | "NO_DATA";
  start_at_utc: string;
  end_at_utc: string;
  duration_seconds: number;
}

export interface DailyServiceSummary {
  service: string;
  day_utc: string;
  overall_status: "UP" | "DEGRADED" | "DOWN" | "NO_DATA";
  uptime_rate_pct: number;
  uptime_seconds: number;
  downtime_seconds: number;
  no_data_seconds: number;
  expected_seconds: number;
  observed_seconds: number;
  coverage_rate_pct: number;
  checks_total: number;
  checks_up: number;
  checks_down: number;
  checks_no_data: number;
  avg_latency_ms: number | null;
  min_latency_ms: number | null;
  max_latency_ms: number | null;
  p95_latency_ms: number | null;
  first_check_at_utc: string | null;
  last_check_at_utc: string | null;
  computed_at_utc: string;
  algo_version: number;
  intervals: DailyServiceInterval[];
}

export interface TimeSeriesPoint {
  timestamp: number;
  value: number;
}
