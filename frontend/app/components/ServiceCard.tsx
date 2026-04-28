import StatusBar from "./StatusBar";

export default function ServiceCard({name, buckets}:{
  name:string;
  buckets:{start:string;end:string;color:string}[];
}) {

  function hasConsecutiveReds(buckets:any[], limit:number){

    let count = 0;

    for(const b of buckets){

      if(b.color === "red"){
        count++
        if(count >= limit) return true
      }
      else{
        count = 0
      }

    }

    return false
  }

  const manyReds = hasConsecutiveReds(buckets,4);

  return (
  <div className="box" style={{ marginBottom: "10px" }}>
    <div style={{ fontWeight: "bold", display: "flex", alignItems: "center", gap: "8px" }}>
      
      <span>{name}</span>

      {manyReds && (
        <span
          style={{
            color: "red",
            fontSize: "14px",
            direction: "ltr",
            unicodeBidi: "isolate"
          }}
        >
          خارج از دسترس
        </span>
      )}

    </div>

    <StatusBar buckets={buckets} />
  </div>

  );
}
