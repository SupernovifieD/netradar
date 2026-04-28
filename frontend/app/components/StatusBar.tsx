export default function StatusBar({
  buckets
}:{
  buckets:{start:string;end:string;color:string}[]
}) {

  function colorToHex(c:string){
    switch(c){
      case "green": return "#2ecc71";
      case "darkgreen": return "#1e8c4e";
      case "orange": return "#e67e22";
      case "blue": return "#3498db";
      case "darkblue": return "#1f5f8b";
      case "red": return "#e74c3c";
      case "grey": return "#555";
      default: return "#444";
    }
  }

  function translateStatus(c:string){
    switch(c){
      case "green": return "پایدار"
      case "darkgreen": return "اختلال جزئی"
      case "orange": return "کندی سرویس"
      case "blue": return "بدون داده پینگ"
      case "darkblue": return "پاسخ ناقص"
      case "red": return "قطع"
      case "grey": return "بدون داده"
      default: return "نامشخص"
    }

  }

  return (
    <div style={{display:"flex",gap:"3px",marginTop:"10px"}}>

      {[...buckets].reverse().map((b,i)=>(
        <div
          key={i}
          title={
            `${new Date(b.start).toLocaleTimeString("fa-IR",{hour:'2-digit',minute:'2-digit'})}
            \nتا
            \n${new Date(b.end).toLocaleTimeString("fa-IR",{hour:'2-digit',minute:'2-digit'})}
            \nوضعیت: ${translateStatus(b.color)}`
            }
          style={{
            flex:1,
            height:"30px",
            background:colorToHex(b.color),
            borderRadius:"2px"
          }}
        />
      ))}

    </div>
  );
}
