import React from "react";
import useAnnotationStore from "../../stores/annotationStore";
import { Sparkles, StickyNote, Bookmark } from "lucide-react";

/**
 * Highlight Overlay Component
 * 
 * Displays annotation markers as bookmark ribbons on the right edge of the PDF page.
 * AI annotations appear as violet ribbons, Notes as emerald ribbons.
 */

export default function HighlightOverlay({ pageNumber, scale, currentLesson }) {
  const getAnnotationsByPage = useAnnotationStore(
    (state) => state.getAnnotationsByPage
  );
  const setViewingAnnotation = useAnnotationStore(
    (state) => state.setViewingAnnotation
  );
  const setActivePanel = useAnnotationStore((state) => state.setActivePanel);

  const annotations = getAnnotationsByPage(currentLesson?.id, pageNumber);

  const handleBookmarkClick = (annotation) => {
    setViewingAnnotation(annotation);
    setActivePanel("history");
  };

  // Calculate vertical spacing for bookmarks
  const getBookmarkPosition = (index, total) => {
    const baseTop = 60; // Starting position from top
    const spacing = 80; // Space between bookmarks
    return baseTop + index * spacing;
  };

  if (annotations.length === 0) return null;

  return (
    <div className="absolute inset-0 pointer-events-none z-20 overflow-visible">
      {/* Bookmark Ribbons on Right Edge */}
      {annotations.map((annotation, index) => {
        const isNote = annotation.type === "note";
        const ribbonType = isNote ? "note" : "ai";
        const Icon = isNote ? StickyNote : Sparkles;

        // Get heading text
        const headingText = isNote
          ? (annotation.heading || "Note")
          : (annotation.action?.charAt(0).toUpperCase() + annotation.action?.slice(1) || "AI");

        return (
          <div
            key={annotation.id}
            className={`bookmark-ribbon ${ribbonType} pointer-events-auto`}
            style={{
              top: `${getBookmarkPosition(index, annotations.length)}px`,
            }}
            onClick={() => handleBookmarkClick(annotation)}
            title={`${headingText}: ${annotation.text?.substring(0, 50)}...`}
          >
            {/* Icon and Heading */}
            <div className="flex items-center gap-2">
              <Icon className="h-3.5 w-3.5" />
              <span className="text-xs font-semibold max-w-[80px] truncate">
                {headingText}
              </span>
            </div>

            {/* Preview Text */}
            <div className="text-[10px] opacity-80 mt-0.5 max-w-[100px] truncate">
              {annotation.text?.substring(0, 25)}...
            </div>
          </div>
        );
      })}

      {/* Badge Counter for Multiple Annotations */}
      {annotations.length > 3 && (
        <div
          className="absolute right-0 bottom-4 pointer-events-auto cursor-pointer"
          style={{
            right: -5
          }}
          onClick={() => setActivePanel("history")}
        >
          <div className="bg-primary text-primary-foreground text-xs font-bold px-3 py-1.5 rounded-l-full shadow-lg hover:scale-105 transition-transform">
            +{annotations.length - 3} more
          </div>
        </div>
      )}
    </div>
  );
}
