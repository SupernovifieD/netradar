import Link from "next/link";
import Footer from "../components/Footer";

export default function AboutPage() {
  return (
    <div className="simple-page">

      <div className="simple-header">
        <Link href="/" className="back-button">
          ← بازگشت
        </Link>
      </div>

      <div className="box simple-content">
        <h1>درباره</h1>

        <p>
          نت رادار ابزاری برای نمایش وضعیت دسترسی به سرویس‌های پر استفاده در ایران است.
        </p>

        <p>
          این سامانه به صورت دوره‌ای اتصال به سرویس‌های مختلف را بررسی می‌کند و نتیجه
          را به شکل یک داشبورد ساده و قابل فهم نمایش می‌دهد.           هدف نت رادار فراهم کردن دیدی سریع از وضعیت دسترسی به سرویس‌های داخلی و خارجی
          برای کاربران اینترنت در ایران است.
        </p>

        <p>
          نت رادار در زمان جنگ ایران در پایان سال ۱۴۰۴ ایجاد شد. این پروژه به صورت رایگان و به صورت اوپن سورس در اختیار عموم قرار گرفته است.
          لطفا از این پروژه
          <a href="https://daramet.com/netradar" target="_blank" rel="noopener noreferrer"> حمایت </a>
          کنید.
          علاوه بر این، برای ارائه پیشنهاد یا بهبود اجزا این پروژه، به صفحه
          <a href="https://github.com/SupernovifieD/netradar" target="_blank" rel="noopener noreferrer"> گیت‌هاب </a>
          این پروژه مراجعه کنید.
        </p>

        <a href="/changelog" style={{ display: "block", textAlign: "center" }}>
          v0.1.0
        </a>

      </div>

      <Footer />
    </div>
  );
}
