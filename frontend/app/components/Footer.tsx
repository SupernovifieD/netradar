export default function Footer() {

  const year = new Date().getFullYear();

  return (
    <footer style={{marginTop:"40px",textAlign:"center"}}>

      <div style={{display:"flex",justifyContent:"center",gap:"20px"}}>

        <a href="#">درباره</a>
        <a href="#">سؤالات رایج</a>
        <a href="https://daramet.com/netradar">حمایت</a>

      </div>

      <div style={{marginTop:"10px"}}>
        {year}
      </div>

    </footer>
  );
}
