import Head from 'next/head';
import Header from '../components/Header';
import Footer from '../components/Footer';

export default function FAQ() {
  const faqs = [
    {
      q: 'چگونه سرویس جدیدی اضافه کنم؟',
      a: 'سرویس‌ها از فایل services.txt در بکند خوانده می‌شوند. برای افزودن سرویس جدید، آن را به این فایل اضافه کنید.'
    },
    {
      q: 'هر چند وقت یکبار سرویس‌ها چک می‌شوند؟',
      a: 'سیستم هر ۱۵ ثانیه یکبار تمام سرویس‌ها را بررسی می‌کند.'
    },
    {
      q: 'منظور از DNS، TCP و Ping چیست؟',
      a: 'DNS بررسی می‌کند که نام دامنه قابل resolve است، TCP اتصال به پورت مشخص را تست می‌کند، و Ping زمان پاسخ‌دهی سرور را اندازه‌گیری می‌کند.'
    },
    {
      q: 'چرا برخی سرویس‌ها قرمز هستند؟',
      a: 'رنگ قرمز نشان‌دهنده عدم دسترسی یا مشکل در سرویس است. می‌توانید جزئیات بیشتر را در صفحه سرویس ببینید.'
    }
  ];

  return (
    <>
      <Head>
        <title>سوالات متداول - نت رادار</title>
      </Head>
      <div className="min-h-screen bg-gray-900 text-gray-100">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <div className="max-w-3xl mx-auto">
            <h1 className="text-3xl font-bold mb-6 border-b-2 border-blue-500 pb-2">سوالات متداول</h1>
            <div className="space-y-6">
              {faqs.map((faq, idx) => (
                <div key={idx} className="border border-gray-700 p-4 rounded bg-gray-800">
                  <h3 className="text-lg font-bold text-blue-400 mb-2">{faq.q}</h3>
                  <p className="text-gray-300">{faq.a}</p>
                </div>
              ))}
            </div>
          </div>
        </main>
        <Footer />
      </div>
    </>
  );
}
