"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getFullServiceData } from "@/lib/api";
import { frontendConfig, statusTimelineConfig } from "@/lib/config";
import type { FullServiceCardData } from "@/types/service";
import ServiceCard from "./ServiceCard";

interface ServiceListProps {
  initialServices: FullServiceCardData[];
}

type SortKey = "latency-fast" | "latency-slow" | "status-up" | "status-down";
type FilterKey = "all" | "general" | "developer" | "streaming";

export default function ServiceList({ initialServices }: ServiceListProps) {
  const [services, setServices] = useState<FullServiceCardData[]>(initialServices ?? []);
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<SortKey>("latency-fast");
  const [filter, setFilter] = useState<FilterKey>("all");
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
    }, frontendConfig.refresh.serviceListMs);
    return () => clearInterval(interval);
  }, []);

  function latestLatency(service: FullServiceCardData): number {
    const last = service.buckets[service.buckets.length - 1];
    return last?.avgLatency ?? Number.POSITIVE_INFINITY;
  }

  function latestColor(service: FullServiceCardData): string {
    const last = service.buckets[service.buckets.length - 1];
    return last?.color ?? statusTimelineConfig.fallbackToken;
  }

  let filtered = services.filter((service) => {
    const text = `${service.meta.name} ${service.meta.domain}`.toLowerCase();

    if (!text.includes(search.toLowerCase())) return false;

    if (filter === "all") return true;
    if (filter === "general") return service.meta.category === "General Services";
    if (filter === "developer") return service.meta.category === "Developer Tools";
    if (filter === "streaming") return service.meta.category === "Streaming Services";

    return true;
  });

  filtered = [...filtered].sort((a, b) => {
    if (sort === "latency-fast") return latestLatency(a) - latestLatency(b);
    if (sort === "latency-slow") return latestLatency(b) - latestLatency(a);
    if (sort === "status-up") return latestColor(a) === statusTimelineConfig.outageToken ? 1 : -1;
    if (sort === "status-down") return latestColor(a) === statusTimelineConfig.outageToken ? -1 : 1;
    return 0;
  });

  return (
    <>
      <div className="controls">
        <div className="controls-left">
          <select className="control-input" value={sort} onChange={(e) => setSort(e.target.value as SortKey)}>
            <option value="latency-fast">Lowest latency</option>
            <option value="latency-slow">Highest latency</option>
            <option value="status-up">Most available</option>
            <option value="status-down">Most unavailable</option>
          </select>
        </div>

        <div className="controls-center">
          <button className={`filter-btn ${filter === "all" ? "active" : ""}`} onClick={() => setFilter("all")}>
            All
          </button>
          <button
            className={`filter-btn ${filter === "general" ? "active" : ""}`}
            onClick={() => setFilter("general")}
          >
            General
          </button>
          <button
            className={`filter-btn ${filter === "developer" ? "active" : ""}`}
            onClick={() => setFilter("developer")}
          >
            Developer
          </button>
          <button
            className={`filter-btn ${filter === "streaming" ? "active" : ""}`}
            onClick={() => setFilter("streaming")}
          >
            Streaming
          </button>
        </div>

        <div className="controls-right">
          <input
            className="control-input"
            type="text"
            placeholder="Search services..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="controls-mobile-search">
        <input
          className="control-input"
          type="text"
          placeholder="Search services..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="controls-mobile">
        <div className="controls-mobile-filters">
          <button className={`filter-btn ${filter === "all" ? "active" : ""}`} onClick={() => setFilter("all")}>
            All
          </button>
          <button
            className={`filter-btn ${filter === "general" ? "active" : ""}`}
            onClick={() => setFilter("general")}
          >
            General
          </button>
          <button
            className={`filter-btn ${filter === "developer" ? "active" : ""}`}
            onClick={() => setFilter("developer")}
          >
            Developer
          </button>
          <button
            className={`filter-btn ${filter === "streaming" ? "active" : ""}`}
            onClick={() => setFilter("streaming")}
          >
            Streaming
          </button>
        </div>

        <div className="controls-mobile-sort">
          <select className="control-input" value={sort} onChange={(e) => setSort(e.target.value as SortKey)}>
            <option value="latency-fast">Lowest latency</option>
            <option value="latency-slow">Highest latency</option>
            <option value="status-up">Most available</option>
            <option value="status-down">Most unavailable</option>
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
            buckets={
              isMobile
                ? serviceData.buckets.slice(-frontendConfig.timeline.mobileBucketCount)
                : serviceData.buckets
            }
          />
        </Link>
      ))}
    </>
  );
}
