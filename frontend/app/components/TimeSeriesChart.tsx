import { TimeSeriesPoint } from "@/types/service";

const CHART_WIDTH = 640;
const CHART_HEIGHT = 260;
const MARGIN = { top: 16, right: 14, bottom: 34, left: 50 };

function formatTime(timestamp: number): string {
  return new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(timestamp));
}

function formatNumber(value: number, decimals = 1): string {
  return value.toLocaleString("en-US", {
    maximumFractionDigits: decimals,
    minimumFractionDigits: 0,
  });
}

function buildLinePath(points: Array<{ x: number; y: number }>): string {
  if (points.length === 0) return "";
  return points
    .map((point, index) => `${index === 0 ? "M" : "L"}${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
    .join(" ");
}

export default function TimeSeriesChart({
  title,
  points,
  unit,
  stroke,
  emptyLabel,
  chartId,
  windowHours,
}: {
  title: string;
  points: TimeSeriesPoint[];
  unit: string;
  stroke: string;
  emptyLabel: string;
  chartId: string;
  windowHours: 6 | 12 | 24;
}) {
  if (points.length < 2) {
    return (
      <div className="box service-chart-card">
        <div className="service-chart-title">{title}</div>
        <div className="service-chart-empty">{emptyLabel}</div>
      </div>
    );
  }

  const xMin = points[0].timestamp;
  const xMax = points[points.length - 1].timestamp;

  const yValues = points.map((point) => point.value);
  const rawMinY = Math.min(...yValues);
  const rawMaxY = Math.max(...yValues);

  const yPadding = (rawMaxY - rawMinY) * 0.15;
  const yMin = Math.max(0, rawMinY - yPadding);
  const yMax = rawMaxY + yPadding || 1;

  const chartInnerWidth = CHART_WIDTH - MARGIN.left - MARGIN.right;
  const chartInnerHeight = CHART_HEIGHT - MARGIN.top - MARGIN.bottom;

  const projectX = (timestamp: number): number => {
    if (xMax === xMin) return MARGIN.left;
    return MARGIN.left + ((timestamp - xMin) / (xMax - xMin)) * chartInnerWidth;
  };

  const projectY = (value: number): number => {
    if (yMax === yMin) return MARGIN.top + chartInnerHeight / 2;
    return MARGIN.top + ((yMax - value) / (yMax - yMin)) * chartInnerHeight;
  };

  const linePoints = points.map((point) => ({
    x: projectX(point.timestamp),
    y: projectY(point.value),
  }));

  const linePath = buildLinePath(linePoints);
  const areaPath = `${linePath} L ${linePoints[linePoints.length - 1].x.toFixed(2)} ${(MARGIN.top + chartInnerHeight).toFixed(2)} L ${linePoints[0].x.toFixed(2)} ${(MARGIN.top + chartInnerHeight).toFixed(2)} Z`;

  const yTicks = 5;
  const yTickValues = Array.from({ length: yTicks }, (_, index) => {
    const ratio = index / (yTicks - 1);
    return yMax - ratio * (yMax - yMin);
  });

  const xTickCount = Math.max(2, Math.floor(windowHours / 6) + 1);
  const xTickTimestamps = Array.from({ length: xTickCount }, (_, index) => {
    if (xTickCount === 1) return xMin;
    const ratio = index / (xTickCount - 1);
    return xMin + (xMax - xMin) * ratio;
  });

  return (
    <div className="box service-chart-card">
      <div className="service-chart-title">{title}</div>

      <svg
        id={chartId}
        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
        className="service-chart-svg"
        role="img"
        aria-label={title}
      >
        {yTickValues.map((tickValue) => {
          const y = projectY(tickValue);
          return (
            <g key={`y-${tickValue}`}>
              <line
                x1={MARGIN.left}
                y1={y}
                x2={CHART_WIDTH - MARGIN.right}
                y2={y}
                className="service-chart-grid-line"
              />
              <text x={MARGIN.left - 8} y={y + 4} textAnchor="end" className="service-chart-axis-label">
                {formatNumber(tickValue)}
              </text>
            </g>
          );
        })}

        <path d={areaPath} fill={stroke} opacity="0.15" />
        <path d={linePath} fill="none" stroke={stroke} strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round" />

        {xTickTimestamps.map((timestamp) => (
          <g key={`x-${timestamp}`}>
            <line
              x1={projectX(timestamp)}
              y1={MARGIN.top + chartInnerHeight}
              x2={projectX(timestamp)}
              y2={MARGIN.top + chartInnerHeight + 5}
              className="service-chart-grid-line"
            />
            <text x={projectX(timestamp)} y={CHART_HEIGHT - 8} textAnchor="middle" className="service-chart-axis-label">
              {formatTime(timestamp)}
            </text>
          </g>
        ))}

        <text x={MARGIN.left} y={14} textAnchor="start" className="service-chart-unit">
          {unit}
        </text>
      </svg>
    </div>
  );
}
