import { ScrollArea } from "../../components/ui/scroll-area";
import { Button } from "../../components/ui/button";
import { BookOpen, ChevronRight } from "lucide-react";
import { cn } from "../../lib/utils";

/**
 * Lesson Navigation Component
 *
 * Sidebar component displaying list of available lessons.
 *
 * TODO: Backend Integration
 * =========================
 * Add loading states, error handling, and search/filter functionality
 */

export default function LessonNavigation({
  lessons,
  currentLesson,
  onLessonSelect,
}) {
  return (
    <div className="flex flex-col h-full border-r bg-card">
      {/* Header */}
      <div className="px-4 py-4 border-b">
        <div className="flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-primary" />
          <h2 className="font-semibold text-lg">Lessons</h2>
        </div>
      </div>

      {/* Lessons List */}
      <ScrollArea className="flex-1">
        <div className="p-2">
          {lessons.map((lesson) => (
            <Button
              key={lesson.id}
              variant={currentLesson?.id === lesson.id ? "secondary" : "ghost"}
              className={cn(
                "w-full justify-start mb-1 h-auto py-3 px-3",
                currentLesson?.id === lesson.id && "bg-accent"
              )}
              onClick={() => onLessonSelect(lesson)}
            >
              <div className="flex items-start gap-3 w-full">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-xs font-semibold text-primary mt-0.5">
                  {lesson.number}
                </div>
                <div className="flex-1 text-left">
                  <div className="font-medium text-sm line-clamp-2">
                    {lesson.title}
                  </div>
                  {lesson.description && (
                    <div className="text-xs text-muted-foreground mt-1 line-clamp-1">
                      {lesson.description.slice(0, 39)}
                    </div>
                  )}
                </div>
                {currentLesson?.id === lesson.id && (
                  <ChevronRight className="h-4 w-4 flex-shrink-0 mt-1" />
                )}
              </div>
            </Button>
          ))}
        </div>
      </ScrollArea>

      {/* Footer */}
      <div className="px-4 py-3 border-t bg-muted/30">
        <div className="text-xs text-muted-foreground text-center">
          {lessons.length} {lessons.length === 1 ? "Lesson" : "Lessons"}{" "}
          Available
        </div>
      </div>
    </div>
  );
}
