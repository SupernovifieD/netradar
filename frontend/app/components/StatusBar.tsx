export default function StatusBar({
  buckets,
}: {
  buckets: { start: string; end: string; color: string }[];
}) {
  if (!buckets?.length) return null;

  // Reverse buckets so newest is left (your original behavior)
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
        return "پایدار";
      case "darkgreen":
        return "اختلال جزئی";
      case "orange":
        return "کندی سرویس";
      case "blue":
        return "بدون داده پینگ";
      case "darkblue":
        return "پاسخ ناقص";
      case "red":
        return "قطع";
      case "grey":
        return "بدون داده";
      default:
        return "نامشخص";
    }
  }

  function toFaTime(t: string) {
    return new Intl.DateTimeFormat("fa-IR", {
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(t));
  }

  // === Timeline markers ===
  // first + every 4 buckets + last
  const markers: string[] = [];
  markers.push(toFaTime(reversed[0].start));

  for (let i = 4; i < reversed.length; i += 4) {
    markers.push(toFaTime(reversed[i].start));
  }

  markers.push(toFaTime(reversed[reversed.length - 1].end));

  // Needed for grid alignment
  const reversedMarkers = [...markers].reverse();
  const groupCount = reversedMarkers.length;


  return (
    <div className="status-wrapper">

      {/* Buckets */}
      <div className="status-grid">
        {reversed.map((b, i) => (
          <div
            key={i}
            className="status-bucket"
            style={{
              background: colorToHex(b.color),
            }}
            title={
              `از ${toFaTime(b.start)}\n` +
              `تا ${toFaTime(b.end)}\n` +
              `وضعیت: ${translateStatus(b.color)}`
            }
          >
          </div>
        ))}
      </div>

      {/* Timeline markers */}
      <div
        className="timeline"
        style={{ gridTemplateColumns: `repeat(${groupCount}, 1fr)` }}
      >
        {reversedMarkers.map((m, i) => (
          <div key={i} className="timeline-marker">
            {m}
          </div>
        ))}
      </div>
    </div>
  );
}

// export default function StatusBar({
//   buckets
// }:{
//   buckets:{start:string;end:string;color:string}[]
// }) {

//   function colorToHex(c:string){
//     switch(c){
//       case "green": return "#2ecc71";
//       case "darkgreen": return "#1e8c4e";
//       case "orange": return "#e67e22";
//       case "blue": return "#3498db";
//       case "darkblue": return "#1f5f8b";
//       case "red": return "#e74c3c";
//       case "grey": return "#555";
//       default: return "#444";
//     }
//   }

//   function translateStatus(c:string){
//     switch(c){
//       case "green": return "پایدار"
//       case "darkgreen": return "اختلال جزئی"
//       case "orange": return "کندی سرویس"
//       case "blue": return "بدون داده پینگ"
//       case "darkblue": return "پاسخ ناقص"
//       case "red": return "قطع"
//       case "grey": return "بدون داده"
//       default: return "نامشخص"
//     }

//   }

//   return (
//     <div style={{display:"flex",gap:"3px",marginTop:"10px"}}>

//       {[...buckets].reverse().map((b,i)=>(
//         <div
//           key={i}
//           title={
//             `${new Date(b.start).toLocaleTimeString("fa-IR",{hour:'2-digit',minute:'2-digit'})}
//             \nتا
//             \n${new Date(b.end).toLocaleTimeString("fa-IR",{hour:'2-digit',minute:'2-digit'})}
//             \nوضعیت: ${translateStatus(b.color)}`
//             }
//           style={{
//             flex:1,
//             height:"30px",
//             background:colorToHex(b.color),
//             borderRadius:"2px"
//           }}
//         />
//       ))}

//     </div>
//   );
// }
