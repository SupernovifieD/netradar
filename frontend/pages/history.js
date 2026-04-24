import Head from 'next/head';
import Header from '../components/Header';
import Footer from '../components/Footer';

export default function History() {
  return (
    <>
      <Head>
        <title>تاریخچه - نت رادار</title>
      </Head>
      <div className="min-h-screen bg-gray-900 text-gray-100">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            <h1 className="text-3xl font-bold mb-6 border-b-2 border-blue-500 pb-2">تاریخچه کلی</h1>
            <p className="text-gray-400 mb-6">نمایش تاریخچه تمام سرویس‌ها - در حال توسعه</p>
            <div className="border border-gray-700 p-6 rounded bg-gray-800 text-center">
              <p className="text-gray-500">این بخش به زودی اضافه خواهد شد</p>
            </div>
          </div>
        </main>
        <Footer />
      </div>
    </>
  );
}
