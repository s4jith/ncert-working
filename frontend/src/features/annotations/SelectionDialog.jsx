import React from "react";
import { Sparkles, StickyNote, Highlighter } from "lucide-react";
import { Button } from "../../components/ui/button";
import { cn } from "../../lib/utils";

/**
 * Selection Dialog Component
 * 
 * Appears after text selection with AI and Note options.
 * Features glassmorphism styling and smooth animations.
 */
export default function SelectionDialog({ position, onAI, onNote }) {
  if (!position) return null;

  return (
    <div
      className="fixed z-50 animate-in fade-in zoom-in-95 slide-in-from-bottom-2 duration-200"
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        transform: "translate(-50%, -100%) translateY(-12px)",
      }}
    >
      {/* Main Dialog Container with Glassmorphism */}
      <div className="selection-dialog rounded-xl p-1.5 flex items-center gap-1">
        {/* Hint Text */}
        <div className="px-3 py-1.5 flex items-center gap-2 text-muted-foreground">
          <Highlighter className="h-3.5 w-3.5" />
          <span className="text-xs font-medium">Dive deeper</span>
        </div>

        <div className="w-px h-6 bg-border/50" />

        {/* AI Button */}
        <Button
          variant="ghost"
          size="sm"
          className={cn(
            "h-9 px-4 gap-2",
            "text-violet-600 hover:text-violet-700",
            "hover:bg-violet-50 dark:hover:bg-violet-950/30",
            "transition-all duration-200",
            "btn-hover-lift"
          )}
          onClick={onAI}
        >
          <Sparkles className="h-4 w-4" />
          <span className="font-medium">Ask AI</span>
        </Button>

        <div className="w-px h-6 bg-border/50" />

        {/* Note Button */}
        <Button
          variant="ghost"
          size="sm"
          className={cn(
            "h-9 px-4 gap-2",
            "text-emerald-600 hover:text-emerald-700",
            "hover:bg-emerald-50 dark:hover:bg-emerald-950/30",
            "transition-all duration-200",
            "btn-hover-lift"
          )}
          onClick={onNote}
        >
          <StickyNote className="h-4 w-4" />
          <span className="font-medium">Add Note</span>
        </Button>
      </div>

      {/* Arrow Pointer */}
      <div
        className="absolute left-1/2 -bottom-2 w-0 h-0 -translate-x-1/2"
        style={{
          borderLeft: "8px solid transparent",
          borderRight: "8px solid transparent",
          borderTop: "8px solid rgba(255, 255, 255, 0.95)",
        }}
      />
    </div>
  );
}
