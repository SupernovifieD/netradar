import StatusBar from "./StatusBar";

export default function ServiceCard({
  meta,
  buckets,
  showMeta = true,
}: {
  meta: {
    name: string;
    domain: string;
    category: string;
    group: string;
  };
  buckets: { start: string; end: string; color: string }[];
  showMeta?: boolean;
}) {
  function hasLatestReds(
    bucketList: { start: string; end: string; color: string }[],
    limit: number
  ): boolean {
    if (bucketList.length < limit) return false;
    const latestBuckets = bucketList.slice(-limit);
    return latestBuckets.every((bucket) => bucket.color === "red");
  }

  const manyReds = hasLatestReds(buckets, 4);

  return (
    <div
      className="box"
      style={{
        marginBottom: "14px",
        padding: "12px",
        borderRadius: "8px",
      }}
    >
      {showMeta && (
        <>
          <div
            style={{
              fontWeight: "bold",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              fontSize: "18px",
              marginBottom: "6px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span>{meta.name}</span>
              {manyReds && <span style={{ color: "red", fontSize: "14px" }}>Outage</span>}
            </div>
          </div>

          <div
            style={{
              fontSize: "14px",
              color: "#9c9c9c",
              marginBottom: "10px",
              lineHeight: "1.5",
            }}
          >
            <div style={{ marginBottom: "8px" }}>{meta.domain}</div>

            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <span
                style={{
                  background: "#eef",
                  padding: "2px 8px",
                  borderRadius: "6px",
                  color: "#334",
                  fontSize: "13px",
                }}
              >
                {meta.group}
              </span>

              <span
                style={{
                  background: "#e8f7ff",
                  padding: "2px 8px",
                  borderRadius: "6px",
                  color: "#245",
                  fontSize: "13px",
                }}
              >
                {meta.category}
              </span>
            </div>
          </div>
        </>
      )}

      {!showMeta && <div style={{ marginBottom: "2px" }} />}

      <StatusBar buckets={buckets} />
    </div>
  );
}
