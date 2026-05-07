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
  function hasConsecutiveReds(
    bucketList: { start: string; end: string; color: string }[],
    limit: number
  ): boolean {
    let c = 0;
    for (const x of bucketList) {
      if (x.color === "red") {
        c++;
        if (c >= limit) return true;
      } else c = 0;
    }
    return false;
  }

  const manyReds = hasConsecutiveReds(buckets, 4);

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
          {/* Row 1: Name + outage */}
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

              {manyReds && (
                <span style={{ color: "red", fontSize: "14px", direction: "rtl" }}>
                  خارج از دسترس
                </span>
              )}
            </div>
          </div>

          {/* Row 2: Metadata (RTL) */}
          <div
            style={{
              direction: "rtl",
              fontSize: "14px",
              color: "#555",
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

      {/* Row 3: Status buckets */}
      <StatusBar buckets={buckets} />
    </div>
  );
}
