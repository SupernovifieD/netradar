import {
  DailyServiceSummary,
  FullServiceCardData,
  ServiceCheck,
  ServiceMeta,
  TimeSeriesPoint,
} from "@/types/service";
import { frontendConfig, statusTimelineConfig } from "@/lib/config";

const DEFAULT_BROWSER_API_BASE = frontendConfig.api.defaultBrowserBase;
const DEFAULT_SERVER_API_BASE = frontendConfig.api.defaultServerBase;
const HALF_HOUR_MS = frontendConfig.timeline.bucketWindowMinutes * 60 * 1000;

interface Bucket {
  start: Date;
  end: Date;
  checks: ServiceCheck[];
}

type BucketSummary = {
  start: string;
  end: string;
  upPercent: number;
  avgLatency: number | null;
  color: string;
};

function trimTrailingSlash(value: string): string {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

function getApiBase(): string {
  if (typeof window === "undefined") {
    return trimTrailingSlash(
      process.env.NETRADAR_API_INTERNAL_URL ??
        process.env.NETRADAR_API_URL ??
        DEFAULT_SERVER_API_BASE
    );
  }

  return trimTrailingSlash(process.env.NEXT_PUBLIC_NETRADAR_API_URL ?? DEFAULT_BROWSER_API_BASE);
}

async function fetchApi<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(`${getApiBase()}${path}`, {
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as T;
  } catch {
    return null;
  }
}

function parseCheckTimestamp(check: ServiceCheck): number | null {
  const timestamp = new Date(`${check.date}T${check.time}Z`).getTime();
  return Number.isFinite(timestamp) ? timestamp : null;
}

function parseLatencyMs(latency: string): number | null {
  const value = Number.parseFloat(latency);
  return Number.isFinite(value) ? value : null;
}

function floorToHalfHour(timestamp: number): number {
  const date = new Date(timestamp);
  date.setSeconds(0);
  date.setMilliseconds(0);
  const bucketMinutes = frontendConfig.timeline.bucketWindowMinutes;
  date.setMinutes(Math.floor(date.getMinutes() / bucketMinutes) * bucketMinutes);
  return date.getTime();
}

function generateBuckets(bucketCount: number): Bucket[] {
  const nowAligned = floorToHalfHour(Date.now());
  const oldestStart = nowAligned - (bucketCount - 1) * HALF_HOUR_MS;
  const buckets: Bucket[] = [];

  for (let index = 0; index < bucketCount; index += 1) {
    const start = new Date(oldestStart + index * HALF_HOUR_MS);
    const end = new Date(start.getTime() + HALF_HOUR_MS);
    buckets.push({ start, end, checks: [] });
  }

  return buckets;
}

function attachChecksToBuckets(checks: ServiceCheck[], buckets: Bucket[]): void {
  if (!buckets.length) return;

  const firstStart = buckets[0].start.getTime();
  const endExclusive = buckets[buckets.length - 1].end.getTime();

  for (const check of checks) {
    const timestamp = parseCheckTimestamp(check);
    if (timestamp === null) continue;
    if (timestamp < firstStart || timestamp >= endExclusive) continue;

    const bucketIndex = Math.floor((timestamp - firstStart) / HALF_HOUR_MS);
    if (bucketIndex >= 0 && bucketIndex < buckets.length) {
      buckets[bucketIndex].checks.push(check);
    }
  }
}

function summarizeBuckets(buckets: Bucket[]): BucketSummary[] {
  return buckets.map((bucket) => {
    const total = bucket.checks.length;

    if (total === 0) {
      return {
        start: bucket.start.toISOString(),
        end: bucket.end.toISOString(),
        upPercent: 0,
        avgLatency: null,
        color: statusTimelineConfig.fallbackToken,
      };
    }

    const upCount = bucket.checks.filter((check) => check.status === "UP").length;
    const upPercent = (upCount / total) * 100;

    const latencySamples = bucket.checks
      .map((check) => parseLatencyMs(check.latency))
      .filter((value): value is number => value !== null);

    const avgLatency =
      latencySamples.length > 0
        ? latencySamples.reduce((sum, value) => sum + value, 0) / latencySamples.length
        : null;

    return {
      start: bucket.start.toISOString(),
      end: bucket.end.toISOString(),
      upPercent,
      avgLatency,
      color: determineColor(upPercent, avgLatency),
    };
  });
}

function buildBucketSummaries(
  checks: ServiceCheck[],
  bucketCount = frontendConfig.timeline.bucketCount
): BucketSummary[] {
  const buckets = generateBuckets(bucketCount);
  attachChecksToBuckets(checks, buckets);
  return summarizeBuckets(buckets);
}

export function buildServiceBucketsFromChecks(
  checks: ServiceCheck[],
  bucketCount: number
): BucketSummary[] {
  return buildBucketSummaries(checks, bucketCount);
}

function downsampleSeries(points: TimeSeriesPoint[], maxPoints = 360): TimeSeriesPoint[] {
  if (points.length <= maxPoints) return points;

  const sampled: TimeSeriesPoint[] = [];
  const step = Math.ceil(points.length / maxPoints);

  for (let index = 0; index < points.length; index += step) {
    sampled.push(points[index]);
  }

  const last = points[points.length - 1];
  if (sampled[sampled.length - 1]?.timestamp !== last.timestamp) {
    sampled.push(last);
  }

  return sampled;
}

// --- Color logic ---
export function determineColor(upPercent: number, avgLatency: number | null): string {
  const stableThreshold = statusTimelineConfig.upStableThresholdPct;
  const degradedThreshold = statusTimelineConfig.upDegradedThresholdPct;
  const highLatencyThreshold = statusTimelineConfig.highLatencyThresholdMs;

  if (upPercent >= stableThreshold && avgLatency !== null && avgLatency < highLatencyThreshold) return "green";
  if (upPercent >= degradedThreshold && upPercent < stableThreshold && avgLatency !== null && avgLatency < highLatencyThreshold) return "darkgreen";
  if (upPercent >= stableThreshold && avgLatency !== null && avgLatency >= highLatencyThreshold) return "orange";
  if (upPercent >= stableThreshold && avgLatency === null) return "blue";
  if (upPercent >= degradedThreshold && avgLatency === null) return "darkblue";
  if (upPercent < degradedThreshold) return statusTimelineConfig.outageToken;
  return statusTimelineConfig.fallbackToken;
}

// --- Fetch 24h raw checks across services ---
export async function getRawStatus(): Promise<ServiceCheck[]> {
  const json = await fetchApi<{ data?: ServiceCheck[]; checks?: ServiceCheck[] } | ServiceCheck[]>(
    "/history/24h"
  );

  if (!json) return [];
  if (Array.isArray(json)) return json;
  if (Array.isArray(json.data)) return json.data;
  if (Array.isArray(json.checks)) return json.checks;
  return [];
}

// --- Fetch metadata ---
export async function getServiceMeta(): Promise<ServiceMeta[]> {
  const json = await fetchApi<{ data?: ServiceMeta[]; services?: ServiceMeta[] }>("/services");
  if (!json) return [];
  return json.data ?? json.services ?? [];
}

export async function getServiceByDomain(domain: string): Promise<ServiceMeta | null> {
  const services = await getServiceMeta();
  return services.find((service) => service.domain === domain) ?? null;
}

export async function getServiceHistory(
  service: string,
  limit = frontendConfig.serviceData.historyLimit
): Promise<ServiceCheck[]> {
  const json = await fetchApi<{ data?: ServiceCheck[] }>(
    `/service/${encodeURIComponent(service)}?limit=${limit}`
  );
  return json?.data ?? [];
}

export async function getServiceDailyHistory(
  service: string,
  limit = frontendConfig.serviceData.dailyLimit
): Promise<DailyServiceSummary[]> {
  const json = await fetchApi<{ data?: DailyServiceSummary[] }>(
    `/service/${encodeURIComponent(service)}/daily?limit=${limit}`
  );
  return json?.data ?? [];
}

export async function exportServiceRawHistory(
  service: string,
  days = frontendConfig.serviceData.defaultExportDays
): Promise<ServiceCheck[]> {
  const json = await fetchApi<{ data?: ServiceCheck[] }>(
    `/service/${encodeURIComponent(service)}/export/raw?days=${days}`
  );
  return json?.data ?? [];
}

export async function exportServiceDailyHistory(
  service: string,
  days = frontendConfig.serviceData.defaultExportDays
): Promise<DailyServiceSummary[]> {
  const json = await fetchApi<{ data?: DailyServiceSummary[] }>(
    `/service/${encodeURIComponent(service)}/export/daily?days=${days}`
  );
  return json?.data ?? [];
}

export function buildLatencySeries(
  checks: ServiceCheck[],
  windowHours: 6 | 12 | 24
): TimeSeriesPoint[] {
  const windowStart = Date.now() - windowHours * 60 * 60 * 1000;

  const points = checks
    .map((check) => {
      const timestamp = parseCheckTimestamp(check);
      const latency = parseLatencyMs(check.latency);
      if (timestamp === null || latency === null) return null;
      if (timestamp < windowStart) return null;
      return { timestamp, value: latency };
    })
    .filter((point): point is TimeSeriesPoint => point !== null)
    .sort((a, b) => a.timestamp - b.timestamp);

  return downsampleSeries(points);
}

export function buildJitterSeries(latencyPoints: TimeSeriesPoint[]): TimeSeriesPoint[] {
  if (latencyPoints.length < 2) return [];

  const jitterPoints: TimeSeriesPoint[] = [];

  for (let index = 1; index < latencyPoints.length; index += 1) {
    const previous = latencyPoints[index - 1];
    const current = latencyPoints[index];
    jitterPoints.push({
      timestamp: current.timestamp,
      value: Math.abs(current.value - previous.value),
    });
  }

  return downsampleSeries(jitterPoints);
}

// --- Combine metadata + buckets (for ServiceList) ---
export async function getFullServiceData(): Promise<FullServiceCardData[]> {
  const [metaList, checks] = await Promise.all([getServiceMeta(), getRawStatus()]);

  const checksByService: Record<string, ServiceCheck[]> = {};
  for (const check of checks) {
    if (!checksByService[check.service]) {
      checksByService[check.service] = [];
    }
    checksByService[check.service].push(check);
  }

  return metaList.map((meta) => ({
    meta,
    buckets: buildBucketSummaries(checksByService[meta.domain] ?? [], frontendConfig.timeline.bucketCount),
  }));
}

export async function getServiceCardData(service: string): Promise<FullServiceCardData | null> {
  const [meta, checks] = await Promise.all([
    getServiceByDomain(service),
    getServiceHistory(service, frontendConfig.serviceData.historyLimit),
  ]);

  if (!meta) return null;

  return {
    meta,
    buckets: buildBucketSummaries(checks, frontendConfig.timeline.bucketCount),
  };
}
