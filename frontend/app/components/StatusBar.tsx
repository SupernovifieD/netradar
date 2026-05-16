import {
  frontendConfig,
  statusTokenToHex,
  statusTokenToLabel,
} from "@/lib/config";

export default function StatusBar({
  buckets,
}: {
  buckets: { start: string; end: string; color: string }[];
}) {
  if (!buckets?.length) return null;

  function toTime(value: string) {
    return new Intl.DateTimeFormat("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(new Date(value));
  }

  const markers: string[] = [];
  markers.push(toTime(buckets[0].start));

  for (let i = frontendConfig.timeline.markerEveryBuckets; i < buckets.length; i += frontendConfig.timeline.markerEveryBuckets) {
    markers.push(toTime(buckets[i].start));
  }

  markers.push(toTime(buckets[buckets.length - 1].end));

  const groupCount = markers.length;

  return (
    <div className="status-wrapper">
      <div className="status-grid">
        {buckets.map((bucket, index) => (
          <div
            key={index}
            className="status-bucket"
            style={{ background: statusTokenToHex(bucket.color) }}
            title={
              `From ${toTime(bucket.start)}\n` +
              `To ${toTime(bucket.end)}\n` +
              `Status: ${statusTokenToLabel(bucket.color)}`
            }
          />
        ))}
      </div>

      <div className="timeline" style={{ gridTemplateColumns: `repeat(${groupCount}, 1fr)` }}>
        {markers.map((marker, index) => (
          <div key={index} className="timeline-marker">
            {marker}
          </div>
        ))}
      </div>
    </div>
  );
}
