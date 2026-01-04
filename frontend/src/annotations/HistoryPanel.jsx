import React from "react";
import { History, StickyNote, Sparkles, Trash2, Clock } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "../../components/ui/sheet";
import { ScrollArea } from "../../components/ui/scroll-area";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Card } from "../../components/ui/card";
import useAnnotationStore from "../../stores/annotationStore";

/**
 * History Panel Component
 *
 * TODO: Backend Integration
 * =========================
 * 1. Add pagination for large annotation lists
 * 2. Add search/filter functionality
 * 3. In deleteAnnotation, add API call:
 *    await annotationService.delete(id);
 */

export default function HistoryPanel({ open, onClose, currentLesson }) {
  const getAnnotationsByLesson = useAnnotationStore(
    (state) => state.getAnnotationsByLesson
  );
  const deleteAnnotation = useAnnotationStore(
    (state) => state.deleteAnnotation
  );

  const lessonAnnotations = currentLesson
    ? getAnnotationsByLesson(currentLesson.id)
    : [];

  const noteAnnotations = lessonAnnotations.filter((a) => a.type === "note");
  const aiAnnotations = lessonAnnotations.filter((a) => a.type === "ai");

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const handleDelete = (id) => {
    if (confirm("Are you sure you want to delete this annotation?")) {
      deleteAnnotation(id);
    }
  };

  return (
    <Sheet open={open} onOpenChange={onClose}>
      <SheetContent
        side="right"
        onClose={onClose}
        className="w-[600px] max-w-[90vw]"
      >
        <SheetHeader className="mb-6">
          <SheetTitle className="flex items-center gap-2">
            <History className="h-5 w-5" />
            Annotations History
          </SheetTitle>
        </SheetHeader>

        <ScrollArea className="h-[calc(100vh-120px)]">
          <div className="space-y-6 pr-4">
            {/* Notes Section */}
            <div>
              <div className="flex items-center gap-2 mb-4">
                <StickyNote className="h-4 w-4 text-green-600" />
                <h3 className="font-semibold text-sm">
                  Notes ({noteAnnotations.length})
                </h3>
              </div>

              {noteAnnotations.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No notes yet
                </p>
              ) : (
                <div className="space-y-3">
                  {noteAnnotations.map((annotation) => (
                    <Card
                      key={annotation.id}
                      className="p-4 border-l-4 border-l-green-500"
                    >
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <h4 className="font-medium text-sm">
                          {annotation.heading}
                        </h4>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0"
                          onClick={() => handleDelete(annotation.id)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>

                      <div className="text-xs text-muted-foreground mb-2 flex items-center gap-2">
                        <Clock className="h-3 w-3" />
                        Page {annotation.pageNumber} •{" "}
                        {formatDate(annotation.timestamp)}
                      </div>

                      <div className="bg-muted/30 rounded p-2 mb-2">
                        <p className="text-xs text-muted-foreground mb-1">
                          Selected:
                        </p>
                        <p className="text-sm line-clamp-2">
                          {annotation.text}
                        </p>
                      </div>

                      {annotation.content && (
                        <div className="mt-2">
                          <p className="text-xs text-muted-foreground mb-1">
                            Your notes:
                          </p>
                          <p className="text-sm">{annotation.content}</p>
                        </div>
                      )}
                    </Card>
                  ))}
                </div>
              )}
            </div>

            {/* AI Annotations Section */}
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Sparkles className="h-4 w-4 text-violet-600" />
                <h3 className="font-semibold text-sm">
                  AI Annotations ({aiAnnotations.length})
                </h3>
              </div>

              {aiAnnotations.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No AI annotations yet
                </p>
              ) : (
                <div className="space-y-3">
                  {aiAnnotations.map((annotation) => (
                    <Card
                      key={annotation.id}
                      className="p-4 border-l-4 border-l-violet-500"
                    >
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <Badge variant="ai" className="capitalize">
                          {annotation.action}
                        </Badge>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0"
                          onClick={() => handleDelete(annotation.id)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>

                      <div className="text-xs text-muted-foreground mb-2 flex items-center gap-2">
                        <Clock className="h-3 w-3" />
                        Page {annotation.pageNumber} •{" "}
                        {formatDate(annotation.timestamp)}
                      </div>

                      <div className="bg-muted/30 rounded p-2 mb-2">
                        <p className="text-xs text-muted-foreground mb-1">
                          Selected:
                        </p>
                        <p className="text-sm line-clamp-2">
                          {annotation.text}
                        </p>
                      </div>

                      {annotation.response && (
                        <div className="mt-2 bg-violet-50 dark:bg-violet-950/20 rounded p-3">
                          <p className="text-xs text-muted-foreground mb-1">
                            AI Response:
                          </p>
                          <p className="text-sm whitespace-pre-wrap line-clamp-4">
                            {annotation.response}
                          </p>
                        </div>
                      )}
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
