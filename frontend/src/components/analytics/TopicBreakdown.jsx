import { useMemo } from "react";
import { AlertTriangle, CheckCircle, Target, BookOpen } from "lucide-react";

/**
 * TopicBreakdown Component
 * 
 * Shows detailed breakdown of performance by topic.
 * Highlights weak areas that need focus and strong areas.
 */

export default function TopicBreakdown({ topics }) {
  // Categorize topics
  const { weakTopics, moderateTopics, strongTopics } = useMemo(() => {
    const weak = topics.filter(t => t.score < 60);
    const moderate = topics.filter(t => t.score >= 60 && t.score < 80);
    const strong = topics.filter(t => t.score >= 80);
    
    return {
      weakTopics: weak.sort((a, b) => a.score - b.score),
      moderateTopics: moderate.sort((a, b) => a.score - b.score),
      strongTopics: strong.sort((a, b) => b.score - a.score)
    };
  }, [topics]);

  const TopicItem = ({ topic, type }) => {
    const bgColor = type === "weak" ? "bg-red-50" : type === "moderate" ? "bg-amber-50" : "bg-green-50";
    const borderColor = type === "weak" ? "border-red-200" : type === "moderate" ? "border-amber-200" : "border-green-200";
    const progressColor = type === "weak" ? "bg-red-500" : type === "moderate" ? "bg-amber-500" : "bg-green-500";
    const textColor = type === "weak" ? "text-red-700" : type === "moderate" ? "text-amber-700" : "text-green-700";

    return (
      <div className={`p-4 rounded-xl border ${bgColor} ${borderColor}`}>
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-medium text-gray-800 truncate flex-1">{topic.topic}</h4>
          <span className={`text-lg font-bold ${textColor}`}>{topic.score}%</span>
        </div>
        
        {/* Progress bar */}
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden mb-2">
          <div
            className={`h-full ${progressColor} rounded-full transition-all`}
            style={{ width: `${topic.score}%` }}
          />
        </div>
        
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>{topic.tests} test{topic.tests !== 1 ? 's' : ''} taken</span>
          <span>{topic.questions || 0} questions</span>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center gap-2 mb-6">
        <BookOpen className="w-5 h-5 text-purple-600" />
        <h3 className="text-lg font-semibold text-gray-800">Topic Analysis</h3>
      </div>

      {topics.length === 0 ? (
        <p className="text-center text-gray-500 py-8">
          Complete some tests to see your topic analysis.
        </p>
      ) : (
        <div className="space-y-6">
          {/* Weak Topics - Need Focus */}
          {weakTopics.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="w-4 h-4 text-red-500" />
                <h4 className="text-sm font-medium text-red-700">Needs Improvement ({weakTopics.length})</h4>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {weakTopics.slice(0, 4).map((topic, i) => (
                  <TopicItem key={i} topic={topic} type="weak" />
                ))}
              </div>
              {weakTopics.length > 4 && (
                <p className="text-xs text-gray-400 mt-2">+{weakTopics.length - 4} more topics</p>
              )}
            </div>
          )}

          {/* Moderate Topics */}
          {moderateTopics.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-4 h-4 text-amber-500" />
                <h4 className="text-sm font-medium text-amber-700">Room for Growth ({moderateTopics.length})</h4>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {moderateTopics.slice(0, 4).map((topic, i) => (
                  <TopicItem key={i} topic={topic} type="moderate" />
                ))}
              </div>
              {moderateTopics.length > 4 && (
                <p className="text-xs text-gray-400 mt-2">+{moderateTopics.length - 4} more topics</p>
              )}
            </div>
          )}

          {/* Strong Topics */}
          {strongTopics.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <h4 className="text-sm font-medium text-green-700">Strong Performance ({strongTopics.length})</h4>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {strongTopics.slice(0, 4).map((topic, i) => (
                  <TopicItem key={i} topic={topic} type="strong" />
                ))}
              </div>
              {strongTopics.length > 4 && (
                <p className="text-xs text-gray-400 mt-2">+{strongTopics.length - 4} more topics</p>
              )}
            </div>
          )}

          {/* Summary */}
          <div className="mt-6 pt-4 border-t border-gray-100">
            <h4 className="text-sm font-medium text-gray-600 mb-3">Quick Summary</h4>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="p-3 rounded-lg bg-red-50">
                <p className="text-2xl font-bold text-red-600">{weakTopics.length}</p>
                <p className="text-xs text-red-500">Need Focus</p>
              </div>
              <div className="p-3 rounded-lg bg-amber-50">
                <p className="text-2xl font-bold text-amber-600">{moderateTopics.length}</p>
                <p className="text-xs text-amber-500">Average</p>
              </div>
              <div className="p-3 rounded-lg bg-green-50">
                <p className="text-2xl font-bold text-green-600">{strongTopics.length}</p>
                <p className="text-xs text-green-500">Strong</p>
              </div>
            </div>
          </div>

          {/* Recommendation */}
          {weakTopics.length > 0 && (
            <div className="p-4 rounded-xl bg-purple-50 border border-purple-200">
              <h4 className="text-sm font-medium text-purple-800 mb-2">📚 Study Recommendation</h4>
              <p className="text-sm text-purple-700">
                Focus on <strong>{weakTopics[0].topic}</strong> first. 
                You've scored {weakTopics[0].score}% in this topic. 
                Review the concepts and take more practice tests.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
