"use client";

import { useEffect, useState } from "react";
import Clock from "./Clock";
import ColorGuide from "./ColorGuide";

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

  const dateParts = new Intl.DateTimeFormat("fa-IR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(now);

  const year = dateParts.find((p) => p.type === "year")?.value ?? "";
  const month = dateParts.find((p) => p.type === "month")?.value ?? "";
  const day = dateParts.find((p) => p.type === "day")?.value ?? "";
  const date = `${year}, ${month}, ${day}`;

  return (
    <div className="header">
      <div className="box header-info">
        <h1>نت رادار</h1>

        <p>وضعیت برقراری سرویس‌های پر استفاده در ایران</p>

        <p className="header-description">
          نت رادار وضعیت دسترسی به برخی از سرویس‌های داخلی و خارجی را نشان
          می‌دهد. برای دریافت اطلاعات بیشتر در مورد هر سرویس، روی آن کلیک کنید.
        </p>
      </div>

      <div className="header-side">
        <div className="header-top-row">
          <div className="box header-datetime">
            <div>{date}</div>
            <Clock />
          </div>

          <a
            href="https://daramet.com/netradar"
            target="_blank"
            rel="noopener noreferrer"
            className="header-support-link"
          >
            <div
              className={`box support-button header-support-button ${highlightSupport ? "support-button--highlight" : ""}`}
            >
              حمایت
            </div>
          </a>
        </div>

        <ColorGuide className="box header-guide" />
      </div>
    </div>
  );
}
