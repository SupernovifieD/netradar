// components/Header.js
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

export default function Header() {
  const [jalaliDate, setJalaliDate] = useState('');
  const router = useRouter();

  useEffect(() => {
    updateDate();
    const interval = setInterval(updateDate, 60000);
    return () => clearInterval(interval);
  }, []);

  const updateDate = () => {
    const now = new Date();
    const jalali = new Intl.DateTimeFormat('fa-IR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }).format(now);
    setJalaliDate(jalali);
  };

  return (
    <header className="border-b border-gray-800 bg-gray-950">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <div className="text-sm text-gray-400">
          <button 
            onClick={() => router.push('/history')}
            className="hover:text-gray-200 transition-colors"
          >
            {jalaliDate}
          </button>
          <div className="mt-2">
            {/* Placeholder for Buy Me Coffee button */}
          </div>
        </div>
        <div className="text-2xl font-bold">نت رادار</div>
      </div>
    </header>
  );
}
