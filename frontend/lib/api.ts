import { ServiceCheck, ServiceMeta } from "@/types/service";

// --- Fetch 24h raw checks ---
export async function getRawStatus(): Promise<ServiceCheck[]> {
  const res = await fetch("http://localhost:5001/api/history/24h", {
    cache: "no-store",
  });

  const json = await res.json();

  if (Array.isArray(json.data)) return json.data;
  if (Array.isArray(json.checks)) return json.checks;
  if (Array.isArray(json)) return json;

  console.error("Unexpected API format:", json);
  return [];
}

// --- Fetch metadata ---
export async function getServiceMeta(): Promise<ServiceMeta[]> {
  const res = await fetch("http://localhost:5001/api/services", {
    cache: "no-store",
  });

  if (!res.ok) return [];
  const json = await res.json();

  return json.data ?? json.services ?? [];
}

// -------- TIME BUCKETING --------

function floorToHalfHour(timestamp: number): number {
  const date = new Date(timestamp);
  date.setSeconds(0);
  date.setMilliseconds(0);
  const m = date.getMinutes();
  date.setMinutes(m < 30 ? 0 : 30);
  return date.getTime();
}

interface Bucket {
  start: Date;
  end: Date;
  checks: ServiceCheck[];
}

function generateBuckets(): Bucket[] {
  const now = floorToHalfHour(Date.now());
  const buckets: Bucket[] = [];
  const HALF = 30 * 60 * 1000;
  for (let i = 47; i >= 0; i--) {
    const start = new Date(now - i * HALF);
    const end = new Date(start.getTime() + HALF);
    buckets.push({ start, end, checks: [] });
  }
  return buckets;
}

// --- Attach checks to buckets ---

export async function getServiceBuckets() {
  const data = await getRawStatus();

  // group by domain
  const services: Record<string, ServiceCheck[]> = {};
  data.forEach((c) => {
    if (!services[c.service]) services[c.service] = [];
    services[c.service].push(c);
  });

  const results: any[] = [];

  for (const [domain, checks] of Object.entries(services)) {
    const buckets = generateBuckets();

    checks.forEach((c) => {
      const ts = new Date(`${c.date} ${c.time}`).getTime();


      buckets.forEach((b) => {
        if (ts >= b.start.getTime() && ts < b.end.getTime()) {
          b.checks.push(c);
        }
      });
    });

    const bucketSummaries = buckets.map((b) => {
      const total = b.checks.length;
      if (total === 0)
        return { start: b.start, end: b.end, upPercent: 0, avgLatency: null, color: "grey" };

      const ups = b.checks.filter((x) => x.status === "UP").length;
      const upPercent = (ups / total) * 100;

      const lats = b.checks
        .map((x) => parseFloat(x.latency))
        .filter((x) => !isNaN(x));

      const avgLatency = lats.length ? lats.reduce((a, b) => a + b) / lats.length : null;

      const color = determineColor(upPercent, avgLatency);

      return {
        start: b.start.toISOString(),
        end: b.end.toISOString(),
        upPercent,
        avgLatency,
        color,
      };
    });

    results.push({
      service: domain,
      buckets: bucketSummaries,
    });
  }

  return results;
}

// --- Color logic ---
function determineColor(up: number, lat: number | null) {
  if (up >= 80 && lat !== null && lat < 40) return "green";
  if (up >= 20 && up < 80 && lat !== null && lat < 40) return "darkgreen";
  if (up >= 80 && lat !== null && lat >= 40) return "orange";
  if (up >= 80 && lat === null) return "blue";
  if (up >= 20 && lat === null) return "darkblue";
  if (up < 20) return "red";
  return "grey";
}

// --- Combine metadata + buckets (for ServiceList) ---
export async function getFullServiceData() {
  const [metaList, checks] = await Promise.all([
    getServiceMeta(),
    getRawStatus(),
  ]);

  // group checks by service
  const checksByService: Record<string, ServiceCheck[]> = {};
  checks.forEach((c) => {
    if (!checksByService[c.service]) checksByService[c.service] = [];
    checksByService[c.service].push(c);
  });

  const results = metaList.map((meta) => {
    const buckets = generateBuckets();
    const serviceChecks = checksByService[meta.domain] || [];

    serviceChecks.forEach((c) => {
      const ts = new Date(`${c.date} ${c.time}`).getTime();


      buckets.forEach((b) => {
        if (ts >= b.start.getTime() && ts < b.end.getTime()) {
          b.checks.push(c);
        }
      });
    });

    const bucketSummaries = buckets.map((b) => {
      const total = b.checks.length;

      if (total === 0) {
        return {
          start: b.start,
          end: b.end,
          upPercent: 0,
          avgLatency: null,
          color: "grey",
        };
      }

      const ups = b.checks.filter((x) => x.status === "UP").length;
      const upPercent = (ups / total) * 100;

      const lats = b.checks
        .map((x) => parseFloat(x.latency))
        .filter((x) => !isNaN(x));

      const avgLatency =
        lats.length > 0
          ? lats.reduce((a, b) => a + b, 0) / lats.length
          : null;

      const color = determineColor(upPercent, avgLatency);

      return {
        start: b.start.toISOString(),
        end: b.end.toISOString(),
        upPercent,
        avgLatency,
        color,
      };
    });

    return {
      meta,
      buckets: bucketSummaries,
    };
  });

  return results;
}
