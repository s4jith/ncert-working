import { Brain, Clock, BookOpen, Zap, ChevronRight, Star } from "lucide-react";
import { Button } from "../ui/button";

/**
 * AITestCard Component
 * 
 * Displays an AI test option for a chapter.
 */

export default function AITestCard({ test, onStart }) {
  const getDifficultyColor = () => {
    switch (test.difficulty) {
      case "Easy":
        return "bg-green-100 text-green-700";
      case "Medium":
        return "bg-amber-100 text-amber-700";
      case "Hard":
        return "bg-red-100 text-red-700";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  const getDifficultyStars = () => {
    const count = test.difficulty === "Easy" ? 1 : test.difficulty === "Medium" ? 2 : 3;
    return Array(count).fill(0).map((_, i) => (
      <Star key={i} className="w-3 h-3 fill-current" />
    ));
  };

  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-all group">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="p-2.5 bg-purple-100 rounded-xl">
          <Brain className="w-5 h-5 text-purple-600" />
        </div>
        <span className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor()}`}>
          {getDifficultyStars()}
          <span className="ml-1">{test.difficulty}</span>
        </span>
      </div>

      {/* Content */}
      <div className="mb-4">
        <p className="text-xs text-purple-600 font-medium mb-1">Chapter {test.chapter}</p>
        <h3 className="font-semibold text-gray-800 mb-1 line-clamp-2">
          {test.chapterName}
        </h3>
        <p className="text-sm text-gray-500">{test.topic}</p>
      </div>

      {/* Meta */}
      <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
        <span className="flex items-center gap-1">
          <BookOpen className="w-4 h-4" />
          {test.questionsCount} Questions
        </span>
        <span className="flex items-center gap-1">
          <Clock className="w-4 h-4" />
          {test.duration} min
        </span>
      </div>

      {/* Start Button */}
      <Button
        onClick={onStart}
        className="w-full gap-2 bg-purple-600 hover:bg-purple-700 group-hover:shadow-lg transition-all"
      >
        <Zap className="w-4 h-4" />
        Start Test
        <ChevronRight className="w-4 h-4 ml-auto group-hover:translate-x-1 transition-transform" />
      </Button>
    </div>
  );
}
