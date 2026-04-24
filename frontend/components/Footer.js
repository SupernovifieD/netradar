// components/Footer.js
export default function Footer() {
  const currentYear = new Intl.DateTimeFormat('fa-IR', { year: 'numeric' }).format(new Date());

  return (
    <footer className="border-t border-gray-800 bg-gray-950 mt-16">
      <div className="container mx-auto px-4 py-6">
        <div className="flex justify-center gap-6 mb-4 text-sm">
          <a href="/about" className="text-gray-400 hover:text-gray-200">درباره</a>
          <a href="/faq" className="text-gray-400 hover:text-gray-200">سؤالات رایج</a>
          <a href="/support" className="text-gray-400 hover:text-gray-200">حمایت</a>
        </div>
        <div className="text-center text-gray-500 text-sm">
          {currentYear} © نت رادار
        </div>
      </div>
    </footer>
  );
}
