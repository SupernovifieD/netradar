"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import ServiceCard from "./ServiceCard";
import { getFullServiceData } from "@/lib/api";
import type { FullServiceCardData } from "@/types/service";

interface ServiceListProps {
  initialServices: FullServiceCardData[];
}

export default function ServiceList({ initialServices }: ServiceListProps) {
  const [services, setServices] = useState<FullServiceCardData[]>(initialServices ?? []);
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("latency-fast");
  const [filter, setFilter] = useState("all");
  const [isMobile, setIsMobile] = useState(false);

  async function refresh() {
    const data = await getFullServiceData();
    setServices(data);
  }

  useEffect(() => {
    const media = window.matchMedia("(max-width: 600px)");
    const onChange = () => setIsMobile(media.matches);

    onChange();
    media.addEventListener("change", onChange);

    return () => {
      media.removeEventListener("change", onChange);
    };
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      void refresh();
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  function latestLatency(service: FullServiceCardData): number {
    const last = service.buckets[service.buckets.length - 1];
    return last?.avgLatency ?? Infinity;
  }

  function latestColor(service: FullServiceCardData): string {
    const last = service.buckets[service.buckets.length - 1];
    return last?.color ?? "grey";
  }

  let filtered = services.filter((s) => {
    const text =
      s.meta.name.toLowerCase() + " " + s.meta.domain.toLowerCase();

    if (!text.includes(search.toLowerCase())) return false;

    if (filter === "all") return true;
    if (filter === "iranian") return s.meta.group === "Iranian Service";
    if (filter === "international") return s.meta.group === "International Service";

    return true;
  });

  filtered = [...filtered].sort((a, b) => {
    if (sort === "latency-fast") return latestLatency(a) - latestLatency(b);
    if (sort === "latency-slow") return latestLatency(b) - latestLatency(a);

    if (sort === "status-up") {
      return latestColor(a) === "red" ? 1 : -1;
    }

    if (sort === "status-down") {
      return latestColor(a) === "red" ? -1 : 1;
    }

    return 0;
  });

  return (
    <>
      <div className="controls">
        <div className="controls-left">
          <select
            className="control-input"
            value={sort}
            onChange={(e) => setSort(e.target.value)}
          >
            <option value="latency-fast">سریعترین سرویس</option>
            <option value="latency-slow">کندترین سرویس</option>
            <option value="status-up">سرویس‌های در دسترس</option>
            <option value="status-down">سرویس‌های خارج از دسترس</option>
          </select>
        </div>

        <div className="controls-center">
          <button
            className={`filter-btn ${filter === "all" ? "active" : ""}`}
            onClick={() => setFilter("all")}
          >
            همه
          </button>

          <button
            className={`filter-btn ${filter === "iranian" ? "active" : ""}`}
            onClick={() => setFilter("iranian")}
          >
            سرویس‌های داخلی
          </button>

          <button
            className={`filter-btn ${filter === "international" ? "active" : ""}`}
            onClick={() => setFilter("international")}
          >
            سرویس‌های خارجی
          </button>
        </div>

        <div className="controls-right">
          <input
            className="control-input"
            type="text"
            placeholder="جستجوی سرویس ..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="controls-mobile-search">
        <input
          className="control-input"
          type="text"
          placeholder="جستجوی سرویس ..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="controls-mobile">
        <div className="controls-mobile-filters">
          <button
            className={`filter-btn ${filter === "all" ? "active" : ""}`}
            onClick={() => setFilter("all")}
          >
            همه
          </button>

          <button
            className={`filter-btn ${filter === "iranian" ? "active" : ""}`}
            onClick={() => setFilter("iranian")}
          >
            سرویس‌های داخلی
          </button>

          <button
            className={`filter-btn ${filter === "international" ? "active" : ""}`}
            onClick={() => setFilter("international")}
          >
            سرویس‌های خارجی
          </button>
        </div>

        <div className="controls-mobile-sort">
          <select
            className="control-input"
            value={sort}
            onChange={(e) => setSort(e.target.value)}
          >
            <option value="latency-fast">سریعترین سرویس</option>
            <option value="latency-slow">کندترین سرویس</option>
            <option value="status-up">سرویس‌های در دسترس</option>
            <option value="status-down">سرویس‌های خارج از دسترس</option>
          </select>
        </div>
      </div>

      {filtered.map((serviceData) => (
        <Link
          key={serviceData.meta.domain}
          href={`/${encodeURIComponent(serviceData.meta.domain)}`}
          className="service-card-link"
        >
          <ServiceCard
            meta={serviceData.meta}
            buckets={isMobile ? serviceData.buckets.slice(-24) : serviceData.buckets}
          />
        </Link>
      ))}
    </>
  );
}
