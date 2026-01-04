import { useMemo } from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

/**
 * PerformanceChart Component
 * 
 * Line/Bar chart showing performance over time.
 * Uses SVG for simple visualization without external libraries.
 */

export default function PerformanceChart({ data, title = "Performance Over Time" }) {
  const maxScore = 100;
  const chartHeight = 200;
  const chartWidth = 600;

  // Calculate chart points
  const points = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    const stepX = chartWidth / (data.length - 1 || 1);
    
    return data.map((item, index) => ({
      x: index * stepX,
      y: chartHeight - (item.score / maxScore) * chartHeight,
      score: item.score,
      date: item.date,
      label: item.label
    }));
  }, [data]);

  // Create SVG path
  const linePath = useMemo(() => {
    if (points.length === 0) return "";
    
    return points.reduce((path, point, index) => {
      if (index === 0) return `M ${point.x} ${point.y}`;
      return `${path} L ${point.x} ${point.y}`;
    }, "");
  }, [points]);

  // Area path for gradient fill
  const areaPath = useMemo(() => {
    if (points.length === 0) return "";
    
    const line = points.reduce((path, point, index) => {
      if (index === 0) return `M ${point.x} ${point.y}`;
      return `${path} L ${point.x} ${point.y}`;
    }, "");
    
    return `${line} L ${points[points.length - 1].x} ${chartHeight} L 0 ${chartHeight} Z`;
  }, [points]);

  // Calculate trend
  const trend = useMemo(() => {
    if (data.length < 2) return "stable";
    const recentAvg = data.slice(-3).reduce((sum, d) => sum + d.score, 0) / Math.min(3, data.length);
    const earlierAvg = data.slice(0, 3).reduce((sum, d) => sum + d.score, 0) / Math.min(3, data.length);
    
    if (recentAvg > earlierAvg + 5) return "up";
    if (recentAvg < earlierAvg - 5) return "down";
    return "stable";
  }, [data]);

  const TrendIcon = trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus;
  const trendColor = trend === "up" ? "text-green-500" : trend === "down" ? "text-red-500" : "text-gray-400";
  const trendText = trend === "up" ? "Improving" : trend === "down" ? "Needs attention" : "Stable";

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
        <div className={`flex items-center gap-1 ${trendColor}`}>
          <TrendIcon className="w-4 h-4" />
          <span className="text-sm font-medium">{trendText}</span>
        </div>
      </div>

      {data.length === 0 ? (
        <div className="h-[200px] flex items-center justify-center text-gray-500">
          No performance data available yet.
        </div>
      ) : (
        <div className="relative">
          {/* Y-axis labels */}
          <div className="absolute left-0 top-0 h-[200px] flex flex-col justify-between text-xs text-gray-400 -ml-8">
            <span>100%</span>
            <span>75%</span>
            <span>50%</span>
            <span>25%</span>
            <span>0%</span>
          </div>

          {/* Chart */}
          <div className="ml-2 overflow-x-auto">
            <svg
              viewBox={`0 0 ${chartWidth} ${chartHeight + 30}`}
              className="w-full min-w-[400px]"
              preserveAspectRatio="xMidYMid meet"
            >
              <defs>
                <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#a855f7" stopOpacity="0.3" />
                  <stop offset="100%" stopColor="#a855f7" stopOpacity="0" />
                </linearGradient>
              </defs>

              {/* Grid lines */}
              {[0, 25, 50, 75, 100].map((percent) => (
                <line
                  key={percent}
                  x1="0"
                  y1={chartHeight - (percent / 100) * chartHeight}
                  x2={chartWidth}
                  y2={chartHeight - (percent / 100) * chartHeight}
                  stroke="#e5e7eb"
                  strokeDasharray="4 4"
                />
              ))}

              {/* Area fill */}
              <path d={areaPath} fill="url(#areaGradient)" />

              {/* Line */}
              <path
                d={linePath}
                fill="none"
                stroke="#a855f7"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              {/* Data points */}
              {points.map((point, index) => (
                <g key={index}>
                  <circle
                    cx={point.x}
                    cy={point.y}
                    r="6"
                    fill="#a855f7"
                    stroke="white"
                    strokeWidth="2"
                    className="cursor-pointer hover:r-8 transition-all"
                  />
                  <title>{`${point.label}: ${point.score}%`}</title>
                </g>
              ))}

              {/* X-axis labels */}
              {points.map((point, index) => (
                <text
                  key={index}
                  x={point.x}
                  y={chartHeight + 20}
                  textAnchor="middle"
                  className="text-xs fill-gray-400"
                >
                  {point.label || point.date}
                </text>
              ))}
            </svg>
          </div>
        </div>
      )}

      {/* Summary stats */}
      {data.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-100 grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-sm text-gray-500">Average</p>
            <p className="text-lg font-semibold text-gray-800">
              {Math.round(data.reduce((sum, d) => sum + d.score, 0) / data.length)}%
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Highest</p>
            <p className="text-lg font-semibold text-green-600">
              {Math.max(...data.map(d => d.score))}%
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Lowest</p>
            <p className="text-lg font-semibold text-red-500">
              {Math.min(...data.map(d => d.score))}%
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
