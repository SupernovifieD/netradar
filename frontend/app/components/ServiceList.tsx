"use client";

import { useEffect, useState } from "react";
import ServiceCard from "./ServiceCard";
import { getFullServiceData } from "@/lib/api";

export default function ServiceList({ initialServices }) {
  const [services, setServices] = useState([]);

  async function refresh() {
    const data = await getFullServiceData();
    setServices(data);
  }

  useEffect(() => {
    refresh();   // load correct structure immediately

    const interval = setInterval(refresh, 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      {services.map((s) => (
        <ServiceCard
          key={s.meta.domain}
          meta={s.meta}
          buckets={s.buckets}
        />
      ))}
    </>
  );
}
