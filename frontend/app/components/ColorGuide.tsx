export default function ColorGuide({ className = "" }: { className?: string }) {
  return (
    <div className={className}>
      راهنمای رنگ‌ها:
      <div>🟢 سرویس در دسترس</div>
      <div>🔵 سرویس در دسترس اما بدون داده پینگ</div>
      <div>🟡 ناپایداری در دسترسی</div>
      <div>🔴 قطعی سرویس</div>
    </div>
  );
}
