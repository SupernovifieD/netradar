export default function Footer() {

  const jalaliYear = new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
    year: "numeric"
  }).format(new Date());

  return (
    <footer style={{marginTop:"40px",textAlign:"center"}}>

      <div style={{display:"flex",justifyContent:"center",gap:"20px"}}>

        <a href="#">درباره</a>
        <a href="#">سؤالات رایج</a>
        <a href="https://daramet.com/netradar">حمایت</a>

      </div>

      <div style={{marginTop:"10px", textAlign:"center", opacity:0.7}}>
        {jalaliYear}
      </div>


    </footer>
  );
}
