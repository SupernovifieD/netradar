"use client";

import { useEffect, useState } from "react";
import ServiceCard from "./ServiceCard";
import { getFullServiceData } from "@/lib/api";

export default function ServiceList({ initialServices }) {
  const [services, setServices] = useState([]);
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("latency-fast");
  const [filter, setFilter] = useState("all");

  async function refresh() {
    const data = await getFullServiceData();
    setServices(data);
  }

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 60000);
    return () => clearInterval(interval);
  }, []);

  function latestLatency(service) {
    const last = service.buckets[service.buckets.length - 1];
    return last?.avgLatency ?? Infinity;
  }

  function latestColor(service) {
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
      {/* Controls */}
      <div className="controls">

        {/* Sorting - left */}
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

        {/* Filters - center */}
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

        {/* Search - right */}
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


      {/* Service Cards */}
      {filtered.map((s) => (
        <ServiceCard key={s.meta.domain} meta={s.meta} buckets={s.buckets} />
      ))}
    </>
  );
}
