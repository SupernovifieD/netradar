"use client";

import { useEffect, useState } from "react";
import { frontendConfig } from "@/lib/config";

export default function Clock() {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => {
      setTime(new Date());
    }, frontendConfig.refresh.clockMs);

    return () => clearInterval(interval);
  }, []);

  return <div>{time.toLocaleTimeString("en-GB", { hour12: false })}</div>;
}
