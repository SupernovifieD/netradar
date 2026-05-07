import Link from "next/link";
import Footer from "../components/Footer";

export default function FAQPage() {
  return (
    <div className="simple-page">
      <div className="box simple-header">
        <Link href="/" className="back-button">
          ← Back to home
        </Link>
      </div>

      <div className="box simple-content">
        <h1>Frequently Asked Questions</h1>

        <h3>What does NetRadar measure?</h3>
        <p>
          NetRadar checks service reachability (DNS and HTTP/TCP) and network latency, then
          displays results as status timelines and charts.
        </p>

        <h3>Are results always exact for every user?</h3>
        <p>
          No. Measurements are automated from monitoring nodes and may differ from an individual
          user’s local network conditions unless run locally. On a local machine, the numbers reflect availability
          based on your network connectivity.
        </p>

        <h3>Why can a service appear unstable?</h3>
        <p>
          Instability usually means part of the checks failed or latency varied significantly
          during the selected time window.
        </p>
      </div>

      <Footer />
    </div>
  );
}
