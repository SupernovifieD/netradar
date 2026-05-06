"use client";

import { useEffect, useState } from "react";
import Clock from "./Clock";

export default function Header() {
  const [highlightSupport, setHighlightSupport] = useState(false);

  useEffect(() => {
    let timeoutId: NodeJS.Timeout;

    const scheduleNext = () => {
      // Random time between 15 to 45 seconds
      const min = 15_000;
      const max = 45_000;
      const delay = Math.floor(Math.random() * (max - min + 1)) + min;

      timeoutId = setTimeout(() => {
        
        setHighlightSupport(true);

        setTimeout(() => {
          setHighlightSupport(false);
          scheduleNext();
        }, 2000); // pulse duration 
      }, delay);
    };

    scheduleNext();

    return () => {
      clearTimeout(timeoutId);
    };
  }, []);

  const now = new Date();

  const date = now.toLocaleDateString("fa-IR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="header" style={{ display: "flex", gap: "10px" }}>
      <div className="box" style={{ flex: 2 }}>
        <h1>نت رادار</h1>

        <p>وضعیت برقراری سرویس‌های پر استفاده در ایران</p>

        <p style={{ fontSize: "14px" }}>
          نت رادار وضعیت دسترسی به برخی از سرویس‌های داخلی و خارجی را نشان
          می‌دهد. برای دریافت اطلاعات بیشتر در مورد هر سرویس، روی آن کلیک کنید.
        </p>
      </div>

      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "10px" }}>
        <div className="box" style={{ direction: "ltr", textAlign: "left" }}>
          <div>{date}</div>
          <Clock />
        </div>

        <a href="https://daramet.com/netradar" target="_blank">
          <div
            className={`box support-button ${highlightSupport ? "support-button--highlight" : ""}`}
            style={{ textAlign: "center" }}
          >
            حمایت
          </div>
        </a>

        <div className="box" style={{ fontSize: "13px", lineHeight: "1.7" }}>
          راهنمای رنگ‌ها:
          <div>🟢 سرویس در دسترس</div>
          <div>🔵 سرویس در دسترس اما بدون داده پینگ</div>
          <div>🟡 ناپایداری در دسترسی</div>
          <div>🔴 قطعی سرویس</div>
        </div>
      </div>
    </div>
  );
}
