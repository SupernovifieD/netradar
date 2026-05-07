"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";

import ColorGuide from "../components/ColorGuide";
import Footer from "../components/Footer";
import ServiceStatusCalendar from "../components/ServiceStatusCalendar";
import ServiceCard from "../components/ServiceCard";
import TimeSeriesChart from "../components/TimeSeriesChart";
import {
  buildJitterSeries,
  buildLatencySeries,
  buildServiceBucketsFromChecks,
  exportServiceDailyHistory,
  exportServiceRawHistory,
  getServiceByDomain,
  getServiceDailyHistory,
  getServiceHistory,
} from "@/lib/api";
import { DailyServiceSummary, ServiceCheck, ServiceMeta } from "@/types/service";

function downloadJson(filename: string, payload: unknown): void {
  const json = JSON.stringify(payload, null, 2);
  const blob = new Blob([json], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);

  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();

  URL.revokeObjectURL(url);
}

function downloadSvgById(svgId: string, filename: string): void {
  const element = document.getElementById(svgId);
  if (!(element instanceof SVGSVGElement)) {
    return;
  }

  const serializer = new XMLSerializer();
  const source = serializer.serializeToString(element);
  const blob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);

  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();

  URL.revokeObjectURL(url);
}

function formatPercent(value: number): string {
  return value.toLocaleString("en-US", {
    maximumFractionDigits: 2,
    minimumFractionDigits: 0,
  });
}

function formatLatency(value: number | null): string {
  if (value === null) return "N/A";
  return value.toLocaleString("en-US", {
    maximumFractionDigits: 1,
    minimumFractionDigits: 0,
  });
}

function toDailyStatusLabel(status: DailyServiceSummary["overall_status"]): string {
  if (status === "UP") return "Up";
  if (status === "DEGRADED") return "Degraded";
  return "Down";
}

export default function ServiceDetailPage() {
  const params = useParams<{ service: string }>();
  const rawServiceParam = params?.service ?? "";
  const serviceDomain = decodeURIComponent(rawServiceParam);

  const [serviceMeta, setServiceMeta] = useState<ServiceMeta | null>(null);
  const [rawChecks, setRawChecks] = useState<ServiceCheck[]>([]);
  const [dailySummaries, setDailySummaries] = useState<DailyServiceSummary[]>([]);
  const [windowHours, setWindowHours] = useState<6 | 12 | 24>(6);
  const [isMobile, setIsMobile] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isExportingRaw, setIsExportingRaw] = useState(false);
  const [isExportingDaily, setIsExportingDaily] = useState(false);

  const refreshData = useCallback(async () => {
    if (!serviceDomain) {
      setErrorMessage("Invalid service name.");
      setIsLoading(false);
      return;
    }

    try {
      const [meta, checks, daily] = await Promise.all([
        getServiceByDomain(serviceDomain),
        getServiceHistory(serviceDomain, 8000),
        getServiceDailyHistory(serviceDomain, 120),
      ]);

      if (!meta) {
        setErrorMessage("This service does not exist in the configured list.");
        setServiceMeta(null);
        setRawChecks([]);
        setDailySummaries([]);
        return;
      }

      setServiceMeta(meta);
      setRawChecks(checks);
      setDailySummaries(daily);
      setErrorMessage(null);
    } catch {
      setErrorMessage("Failed to fetch service data.");
    } finally {
      setIsLoading(false);
    }
  }, [serviceDomain]);

  useEffect(() => {
    const media = window.matchMedia("(max-width: 600px)");
    const handleMediaChange = () => setIsMobile(media.matches);

    handleMediaChange();
    media.addEventListener("change", handleMediaChange);

    return () => media.removeEventListener("change", handleMediaChange);
  }, []);

  useEffect(() => {
    const initialTimeout = setTimeout(() => {
      void refreshData();
    }, 0);

    const interval = setInterval(() => {
      void refreshData();
    }, 120_000);

    return () => {
      clearTimeout(initialTimeout);
      clearInterval(interval);
    };
  }, [refreshData]);

  const cardBuckets = useMemo(() => buildServiceBucketsFromChecks(rawChecks, 48), [rawChecks]);

  const visibleBuckets = useMemo(() => (isMobile ? cardBuckets.slice(-24) : cardBuckets), [cardBuckets, isMobile]);

  const latestDaily = dailySummaries[0] ?? null;

  const latencySeries = useMemo(() => buildLatencySeries(rawChecks, windowHours), [rawChecks, windowHours]);

  const jitterSeries = useMemo(() => buildJitterSeries(latencySeries), [latencySeries]);

  const handleRawExport = async () => {
    if (!serviceMeta || isExportingRaw) return;

    try {
      setIsExportingRaw(true);
      const rows = await exportServiceRawHistory(serviceMeta.domain, 90);
      downloadJson(`netradar-raw-${serviceMeta.domain}-90d.json`, rows);
    } finally {
      setIsExportingRaw(false);
    }
  };

  const handleDailyExport = async () => {
    if (!serviceMeta || isExportingDaily) return;

    try {
      setIsExportingDaily(true);
      const rows = await exportServiceDailyHistory(serviceMeta.domain, 90);
      downloadJson(`netradar-daily-${serviceMeta.domain}-90d.json`, rows);
    } finally {
      setIsExportingDaily(false);
    }
  };

  const handleChartDownload = () => {
    if (!serviceMeta) return;
    downloadSvgById("chart-jitter", `netradar-jitter-${serviceMeta.domain}-${windowHours}h.svg`);
    downloadSvgById("chart-latency", `netradar-latency-${serviceMeta.domain}-${windowHours}h.svg`);
  };

  return (
    <main className="container service-detail-page">
      <div className="box simple-header service-simple-header">
        <Link href="/" className="back-button">
          ← Back to home
        </Link>
      </div>

      {isLoading && <div className="box">Loading service data...</div>}

      {errorMessage && <div className="box service-error-box">{errorMessage}</div>}

      {!isLoading && !errorMessage && serviceMeta && (
        <>
          <div className="service-top-row">
            <div className="box service-meta-box">
              <h2 className="service-meta-name">{serviceMeta.name}</h2>
              <div className="service-meta-domain">{serviceMeta.domain}</div>

              <div className="service-meta-tags">
                <span className="service-meta-tag service-meta-tag--group">{serviceMeta.group}</span>
                <span className="service-meta-tag service-meta-tag--category">{serviceMeta.category}</span>
              </div>

              {latestDaily && (
                <div className="service-meta-daily-summary">
                  <div>Latest daily status: {toDailyStatusLabel(latestDaily.overall_status)}</div>
                  <div>Uptime rate: {formatPercent(latestDaily.uptime_rate_pct)}%</div>
                  <div>Average latency: {formatLatency(latestDaily.avg_latency_ms)} ms</div>
                </div>
              )}
            </div>

            <ServiceStatusCalendar summaries={dailySummaries} />
          </div>

          <ServiceCard meta={serviceMeta} buckets={visibleBuckets} showMeta={false} />

          <div className="service-info-row">
            <ColorGuide className="box service-guide-block" />

            <div className="box service-download-box">
              <h3>Download data</h3>
              <p>
                You can download up to 90 days from both databases. For longer periods, you can
                do so by querying the local database.
              </p>
              <div className="service-download-actions">
                <button className="filter-btn" onClick={() => void handleRawExport()} disabled={isExportingRaw}>
                  {isExportingRaw ? "Preparing..." : "Download raw data (90 days)"}
                </button>
                <button className="filter-btn" onClick={() => void handleDailyExport()} disabled={isExportingDaily}>
                  {isExportingDaily ? "Preparing..." : "Download daily summary (90 days)"}
                </button>
              </div>
            </div>
          </div>

          <section className="service-graphs-section">
            <div className="service-graphs-grid">
              <TimeSeriesChart
                chartId="chart-jitter"
                title="Jitter"
                points={jitterSeries}
                unit="ms"
                stroke="#ffd166"
                windowHours={windowHours}
                emptyLabel="Not enough data in this window to compute jitter."
              />

              <TimeSeriesChart
                chartId="chart-latency"
                title="Latency"
                points={latencySeries}
                unit="ms"
                stroke="#4ea3ff"
                windowHours={windowHours}
                emptyLabel="No latency data available in this window."
              />
            </div>

            <div className="service-graph-toolbar">
              <button className="filter-btn service-chart-download" onClick={handleChartDownload}>
                Download charts (SVG)
              </button>

              <div className="service-graph-controls">
                <button className={`filter-btn ${windowHours === 6 ? "active" : ""}`} onClick={() => setWindowHours(6)}>
                  6h
                </button>
                <button className={`filter-btn ${windowHours === 12 ? "active" : ""}`} onClick={() => setWindowHours(12)}>
                  12h
                </button>
                <button className={`filter-btn ${windowHours === 24 ? "active" : ""}`} onClick={() => setWindowHours(24)}>
                  24h
                </button>
              </div>
            </div>
          </section>

          <div className="box service-metrics-description">
            <h3>Metrics explained</h3>
            <p>
              Latency is the time required for a response to reach the monitoring point. It is
              measured in milliseconds, and lower values usually mean a faster experience.
            </p>
            <p>
              Jitter is the amount of variation between consecutive latency samples. Higher jitter
              means the connection quality is less consistent, which can hurt calls, streaming,
              and real-time applications.
            </p>
          </div>
        </>
      )}

      <Footer />
    </main>
  );
}
