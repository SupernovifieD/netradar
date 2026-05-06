export default function Footer() {
  const jalaliYear = new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
    year: "numeric",
  }).format(new Date());

  return (
    <footer className="site-footer">
      <div className="site-footer-links">
        <a href="/about">درباره</a>
        <a href="/faq">سؤالات رایج</a>
        <a href="https://github.com/SupernovifieD/netradar">گیت هاب</a>
        <a href="https://daramet.com/netradar">حمایت</a>
      </div>

      <div className="site-footer-year">
        {jalaliYear}
      </div>
    </footer>
  );
}
