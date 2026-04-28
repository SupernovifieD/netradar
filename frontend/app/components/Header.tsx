export default function Header() {
  const now = new Date();

  const date = now.toLocaleDateString("fa-IR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  const time = now.toLocaleTimeString("fa-IR");

  return (
    <div className="header" style={{display:"flex",gap:"10px"}}>

      <div className="box" style={{flex:2}}>
        <h1>نت رادار</h1>
        <p>
        وضعیت برقراری سرویس‌های پر استفاده در ایران
        </p>

        <p style={{fontSize:"14px"}}>
        نت رادار وضعیت دسترسی به برخی از سرویس‌های داخلی و خارجی را نشان می‌دهد.
        برای دریافت اطلاعات بیشتر در مورد هر سرویس، روی آن کلیک کنید.
        </p>
      </div>

      <div style={{flex:1,display:"flex",flexDirection:"column",gap:"10px"}}>

        <div className="box" style={{direction:"ltr",textAlign:"left"}}>
          <div>{date}</div>
          <div>{time}</div>
        </div>

        <a
          href="https://daramet.com/netradar"
          target="_blank"
        >
          <div className="box" style={{textAlign:"center"}}>
            حمایت
          </div>
        </a>

      </div>

    </div>
  );
}
