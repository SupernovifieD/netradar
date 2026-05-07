export default function StatusBar({
  buckets,
}: {
  buckets: { start: string; end: string; color: string }[];
}) {
  if (!buckets?.length) return null;

  // Newest on the left.
  const reversed = [...buckets].reverse();

  function colorToHex(c: string) {
    switch (c) {
      case "green":
        return "#2ecc71";
      case "darkgreen":
        return "#1e8c4e";
      case "orange":
        return "#e67e22";
      case "blue":
        return "#3498db";
      case "darkblue":
        return "#1f5f8b";
      case "red":
        return "#e74c3c";
      case "grey":
        return "#555";
      default:
        return "#444";
    }
  }

  function translateStatus(c: string) {
    switch (c) {
      case "green":
        return "Stable";
      case "darkgreen":
        return "Minor instability";
      case "orange":
        return "High latency";
      case "blue":
        return "No ping data";
      case "darkblue":
        return "Partial response";
      case "red":
        return "Outage";
      case "grey":
        return "No data";
      default:
        return "Unknown";
    }
  }

  function toTime(value: string) {
    return new Intl.DateTimeFormat("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(new Date(value));
  }

  const markers: string[] = [];
  markers.push(toTime(reversed[0].start));

  for (let i = 4; i < reversed.length; i += 4) {
    markers.push(toTime(reversed[i].start));
  }

  markers.push(toTime(reversed[reversed.length - 1].end));

  const reversedMarkers = [...markers].reverse();
  const groupCount = reversedMarkers.length;

  return (
    <div className="status-wrapper">
      <div className="status-grid">
        {reversed.map((bucket, index) => (
          <div
            key={index}
            className="status-bucket"
            style={{ background: colorToHex(bucket.color) }}
            title={
              `From ${toTime(bucket.start)}\n` +
              `To ${toTime(bucket.end)}\n` +
              `Status: ${translateStatus(bucket.color)}`
            }
          />
        ))}
      </div>

      <div className="timeline" style={{ gridTemplateColumns: `repeat(${groupCount}, 1fr)` }}>
        {reversedMarkers.map((marker, index) => (
          <div key={index} className="timeline-marker">
            {marker}
          </div>
        ))}
      </div>
    </div>
  );
}
