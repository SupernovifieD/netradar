export interface ServiceCheck {
  id: number;
  service: string;
  latency: string;
  packet_loss: string;
  dns: string;
  tcp: string;
  status: string;
  date: string;   // "2026-04-29"
  time: string;   // "20:12:51"
}

export interface ServiceMeta {
  id: string;            // unique id e.g. "google", "digikala"
  name: string;          // Display name e.g. "Digikala"
  domain: string;        // digikala.com
  group: string;         // "Iranian"
  category: string;      // "general services"
}

export interface ServiceBuckets {
  service: string;  // domain
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
