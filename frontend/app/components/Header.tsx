"use client";

import { useEffect, useState } from "react";
import Clock from "./Clock";
import ColorGuide from "./ColorGuide";

export default function Header() {
  const [highlightSupport, setHighlightSupport] = useState(false);

  useEffect(() => {
    let timeoutId: NodeJS.Timeout;

    const scheduleNext = () => {
      const min = 15_000;
      const max = 45_000;
      const delay = Math.floor(Math.random() * (max - min + 1)) + min;

      timeoutId = setTimeout(() => {
        setHighlightSupport(true);

        setTimeout(() => {
          setHighlightSupport(false);
          scheduleNext();
        }, 2000);
      }, delay);
    };

    scheduleNext();

    return () => {
      clearTimeout(timeoutId);
    };
  }, []);

  const now = new Date();
  const dateParts = new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "long",
    day: "2-digit",
  }).formatToParts(now);

  const year = dateParts.find((p) => p.type === "year")?.value ?? "";
  const month = dateParts.find((p) => p.type === "month")?.value ?? "";
  const day = dateParts.find((p) => p.type === "day")?.value ?? "";
  const date = `${day} ${month}, ${year}`;

  return (
    <div className="header">
      <div className="box header-info">
        <h1>NetRadar</h1>

        <p>Live availability tracking for popular internet services</p>

        <p className="header-description">
          NetRadar monitors service reachability and basic performance. Click any service card
          to view detailed daily history, charts, and export options.
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
              Support
            </div>
          </a>
        </div>

        <ColorGuide className="box header-guide" />
      </div>
    </div>
  );
}
