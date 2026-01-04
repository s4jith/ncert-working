import React from "react";
import { Sparkles, StickyNote } from "lucide-react";
import { Button } from "../../components/ui/button";
import { cn } from "../../lib/utils";

export default function SelectionDialog({ position, onAI, onNote }) {
  if (!position) return null;

  return (
    <div
      className="fixed z-40 animate-in fade-in slide-in-from-bottom-2 duration-200"
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        transform: "translate(-50%, -100%) translateY(-8px)",
      }}
    >
      <div className="rounded-lg border bg-card shadow-lg p-2 flex gap-1">
        <Button
          variant="ghost"
          size="sm"
          className="h-8 text-primary hover:text-primary hover:bg-primary/10"
          onClick={onAI}
        >
          <Sparkles className="h-4 w-4 mr-1.5" />
          AI
        </Button>
        <div className="w-px bg-border" />
        <Button
          variant="ghost"
          size="sm"
          className="h-8 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
          onClick={onNote}
        >
          <StickyNote className="h-4 w-4 mr-1.5" />
          Note
        </Button>
      </div>
    </div>
  );
}
