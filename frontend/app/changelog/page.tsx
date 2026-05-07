import Link from "next/link";
import Footer from "../components/Footer";

export default function ChangelogPage() {
  return (
    <div className="simple-page">

      <div className="box simple-header">
        <Link href="/" className="back-button">
          ← بازگشت به صفحه اصلی
        </Link>
      </div>

      <div className="box simple-content">
        <h1>تغییرات</h1>

        <h3>v0.1.0</h3>
        <p>
            اردیبهشت ۱۴۰۵
        </p>
        <p>
            اولین نسخه شامل بررسی اتصال http و سرعت برقراری سرویس‌ها سرویس بارگزاری شد.
        </p>


      </div>

      <Footer />
    </div>
  );
}
