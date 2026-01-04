import { useMemo } from "react";

/**
 * TopicHeatmap Component
 * 
 * Visual heatmap showing performance across different topics.
 * Color intensity indicates score level.
 */

export default function TopicHeatmap({ topics }) {
  const getHeatmapColor = (score) => {
    if (score >= 85) return "bg-green-500";
    if (score >= 75) return "bg-green-400";
    if (score >= 65) return "bg-amber-400";
    if (score >= 55) return "bg-amber-500";
    if (score >= 45) return "bg-orange-500";
    return "bg-red-500";
  };

  const getTextColor = (score) => {
    return score >= 65 ? "text-white" : "text-white";
  };

  // Sort topics by score for better visualization
  const sortedTopics = useMemo(() => {
    return [...topics].sort((a, b) => b.score - a.score);
  }, [topics]);

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Topic Performance Heatmap</h3>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-red-500" />
            Low
          </span>
          <span className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-amber-500" />
            Medium
          </span>
          <span className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-green-500" />
            High
          </span>
        </div>
      </div>

      {topics.length === 0 ? (
        <p className="text-center text-gray-500 py-8">
          Complete some tests to see your topic performance.
        </p>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {sortedTopics.map((topic, i) => (
            <div
              key={i}
              className={`relative p-4 rounded-xl ${getHeatmapColor(topic.score)} ${getTextColor(topic.score)} transition-transform hover:scale-105 cursor-default`}
              title={`${topic.topic}: ${topic.score}% (${topic.tests} tests)`}
            >
              <p className="text-sm font-medium truncate mb-1">{topic.topic}</p>
              <p className="text-2xl font-bold">{topic.score}%</p>
              <p className="text-xs opacity-75">{topic.tests} tests</p>
            </div>
          ))}
        </div>
      )}

      {/* Legend */}
      <div className="mt-6 pt-4 border-t border-gray-100">
        <div className="flex items-center justify-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-full h-2 rounded bg-gradient-to-r from-red-500 via-amber-500 to-green-500" style={{ width: '150px' }} />
          </div>
          <span className="text-gray-500">0%</span>
          <span className="text-gray-400">→</span>
          <span className="text-gray-500">100%</span>
        </div>
      </div>
    </div>
  );
}
