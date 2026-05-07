import Link from "next/link";
import Footer from "../components/Footer";

export default function ChangelogPage() {
  return (
    <div className="simple-page">
      <div className="box simple-header">
        <Link href="/" className="back-button">
          ← Back to home
        </Link>
      </div>

      <div className="box simple-content">
        <h1>Changelog</h1>

        <h3>v0.1.0</h3>
        <p>May 2026</p>
        <p>First public version with service connectivity checks and latency monitoring.</p>
      </div>

      <Footer />
    </div>
  );
}
