import Link from "next/link";

export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="site-footer">
      <div className="site-footer-links">
        <Link href="/about">About</Link>
        <Link href="/faq">FAQ</Link>
        <a href="https://github.com/SupernovifieD/netradar">GitHub</a>
        <a href="https://daramet.com/netradar">Support</a>
      </div>

      <div className="site-footer-year">{year}</div>
    </footer>
  );
}
