import Link from "next/link";
import Footer from "../components/Footer";

export default function AboutPage() {
  return (
    <div className="simple-page">
      <div className="box simple-header">
        <Link href="/" className="back-button">
          ← Back to home
        </Link>
      </div>

      <div className="box simple-content">
        <h1>About</h1>

        <p>
          NetRadar is an open-source project for monitoring internet service availability and
          basic performance.
        </p>

        <p>
          The platform runs scheduled checks, stores raw probe results, and presents them in
          a simple dashboard so users can quickly understand service health over time.
        </p>

        <p>
          NetRadar is free to use and open source. If you want to support the project,
          visit the <a href="https://daramet.com/netradar" target="_blank" rel="noopener noreferrer">support page</a>.
          You can also contribute ideas or code on
          <a href="https://github.com/SupernovifieD/netradar" target="_blank" rel="noopener noreferrer"> GitHub</a>.
        </p>

        <Link href="/changelog" style={{ display: "block", textAlign: "center" }}>
          v0.1.0
        </Link>
      </div>

      <Footer />
    </div>
  );
}
