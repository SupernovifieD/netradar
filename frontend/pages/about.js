import Head from 'next/head';
import Header from '../components/Header';
import Footer from '../components/Footer';

export default function About() {
  return (
    <>
      <Head>
        <title>درباره - نت رادار</title>
      </Head>
      <div className="min-h-screen bg-gray-900 text-gray-100">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <div className="max-w-3xl mx-auto">
            <h1 className="text-3xl font-bold mb-6 border-b-2 border-blue-500 pb-2">درباره نت رادار</h1>
            <div className="space-y-4 text-gray-300 leading-relaxed">
              <p>
                نت رادار یک سیستم نظارت بر سرویس‌های آنلاین است که به صورت خودکار وضعیت دسترسی به سرویس‌های مختلف را بررسی می‌کند.
              </p>
              <p>
                این سیستم هر ۱۵ ثانیه یکبار سرویس‌ها را چک کرده و نتایج را در پایگاه داده ذخیره می‌کند.
              </p>
              <h2 className="text-xl font-bold mt-6 mb-3">قابلیت‌ها:</h2>
              <ul className="list-disc list-inside space-y-2 mr-4">
                <li>بررسی DNS</li>
                <li>بررسی اتصال TCP</li>
                <li>تست Ping</li>
                <li>نمایش تاریخچه وضعیت</li>
                <li>رابط کاربری ساده و کاربردی</li>
              </ul>
            </div>
          </div>
        </main>
        <Footer />
      </div>
    </>
  );
}
