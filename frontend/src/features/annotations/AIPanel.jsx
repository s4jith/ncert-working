import React, { useState } from "react";
import { Sparkles, FileText, BookOpen, Download } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "../../components/ui/sheet";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { ScrollArea } from "../../components/ui/scroll-area";
import useAnnotationStore from "../../stores/annotationStore";
import useUserStore from "../../stores/userStore";
import { chatService } from "../../services/api";
import ReactMarkdown from "react-markdown";
import { exportChatAsDoc } from "../../utils/chatExport";

/**
 * AI Panel Component - Backend Connected
 * Uses chatService.processAnnotation() for RAG-based AI responses
 */

const AI_ACTIONS = [
  {
    id: "define",
    label: "Define",
    icon: FileText,
    description: "Get clear definitions and meanings",
    color: "text-blue-600",
  },
  {
    id: "stick_flow",
    label: "Stick Flow",
    icon: Sparkles,
    description: "Visual flow diagram of the concept",
    color: "text-purple-600",
  },
  {
    id: "elaborate",
    label: "Elaborate",
    icon: BookOpen,
    description: "Detailed explanation with examples",
    color: "text-green-600",
  },
];

export default function AIPanel({ open, onClose, currentLesson, pageNumber }) {
  const selectedText = useAnnotationStore((state) => state.selectedText);
  const addAIAnnotation = useAnnotationStore((state) => state.addAIAnnotation);
  const { user } = useUserStore();
  const [selectedAction, setSelectedAction] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [response, setResponse] = useState("");
  const [imageUrl, setImageUrl] = useState(null);
  const [error, setError] = useState(null);

  // Use lesson's subject if available, otherwise use user's preferred subject
  const effectiveSubject = currentLesson?.subject || user.preferredSubject || "Mathematics";

  const handleActionSelect = async (action) => {
    setSelectedAction(action.id);
    setIsProcessing(true);
    setError(null);
    setImageUrl(null);

    try {
      console.log("🚀 Calling backend API...", {
        chapter: currentLesson?.number || 1,
        text: selectedText?.text,
        action: action.id,
        subject: effectiveSubject,
        classLevel: user.classLevel
      });

      // Use unified annotation endpoint for all actions
      const result = await chatService.processAnnotation(
        selectedText?.text || "",
        action.id,
        user.classLevel,
        effectiveSubject,
        currentLesson?.number || 1
      );

      console.log("✅ Backend response received:", result);
      setResponse(result.answer);
      setIsProcessing(false);
    } catch (err) {
      console.error("❌ AI API Error:", err);
      setError(err.message || "Failed to get AI response");
      setIsProcessing(false);
    }
  };

  const handleSave = () => {
    if (selectedText && selectedAction) {
      addAIAnnotation({
        text: selectedText.text,
        action: selectedAction,
        response: response,
        pageNumber: pageNumber,
        position: selectedText.position,
        lessonId: currentLesson?.id,
      });

      setSelectedAction(null);
      setResponse("");
      onClose();
    }
  };

  const handleClose = () => {
    setSelectedAction(null);
    setResponse("");
    setImageUrl(null);
    onClose();
  };

  // Download AI response as document
  const handleDownload = () => {
    if (!response && !imageUrl) return;

    const actionLabel = AI_ACTIONS.find((a) => a.id === selectedAction)?.label || "AI Response";
    const messages = [
      {
        role: "user",
        content: `Selected text: "${selectedText?.text || ""}"

Action: ${actionLabel}`,
        timestamp: new Date().toISOString(),
      },
      {
        role: "assistant",
        content: response || "[Visual diagram generated]",
        timestamp: new Date().toISOString(),
      },
    ];

    exportChatAsDoc(messages, {
      filename: `AI-${actionLabel}-${Date.now()}.doc`,
      title: `AI ${actionLabel} - ${currentLesson?.title || "PDF Annotation"}`,
      userName: "Your Question",
      aiName: "AI Response",
    });
  };

  return (
    <Sheet open={open} onOpenChange={handleClose}>
      <SheetContent
        side="right"
        onClose={handleClose}
        className="w-[500px] max-w-[90vw]"
      >
        <SheetHeader className="mb-6">
          <SheetTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            AI Assistant
          </SheetTitle>
        </SheetHeader>

        <div className="space-y-6">
          {/* Selected Text */}
          <div className="rounded-lg border bg-muted/30 p-4">
            <p className="text-xs font-medium text-muted-foreground mb-2">
              Selected Text
            </p>
            <p className="text-sm leading-relaxed">{selectedText?.text}</p>
          </div>

          {/* AI Actions */}
          {!selectedAction && (
            <div className="space-y-3">
              <p className="text-sm font-medium">What would you like to do?</p>
              <div className="grid gap-2">
                {AI_ACTIONS.map((action) => {
                  const Icon = action.icon;
                  return (
                    <Button
                      key={action.id}
                      variant="outline"
                      className="h-auto justify-start p-4"
                      onClick={() => handleActionSelect(action)}
                    >
                      <Icon className={`h-5 w-5 mr-3 ${action.color}`} />
                      <div className="text-left">
                        <div className="font-medium">{action.label}</div>
                        <div className="text-xs text-muted-foreground">
                          {action.description}
                        </div>
                      </div>
                    </Button>
                  );
                })}
              </div>
            </div>
          )}

          {/* AI Response */}
          {selectedAction && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Badge variant="ai">
                  {AI_ACTIONS.find((a) => a.id === selectedAction)?.label}
                </Badge>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setSelectedAction(null);
                    setResponse("");
                  }}
                >
                  Change Action
                </Button>
              </div>

              <div className="min-h-[300px] max-h-[500px] overflow-y-auto rounded-lg border bg-background p-4">
                {isProcessing ? (
                  <div className="flex items-center justify-center h-full py-8">
                    <div className="text-center space-y-2">
                      <Sparkles className="h-8 w-8 animate-pulse text-violet-600 mx-auto" />
                      <p className="text-sm text-muted-foreground">
                        AI is {selectedAction === 'stick_flow' ? 'creating flow diagram' : 'thinking'}...
                      </p>
                    </div>
                  </div>
                ) : error ? (
                  <div className="text-center space-y-2 py-8">
                    <p className="text-sm text-red-600">Error: {error}</p>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        handleActionSelect(
                          AI_ACTIONS.find((a) => a.id === selectedAction)
                        )
                      }
                    >
                      Try Again
                    </Button>
                  </div>
                ) : imageUrl ? (
                  <div className="space-y-3">
                    <img
                      src={imageUrl}
                      alt="Concept Flow Diagram"
                      className="w-full rounded-lg border shadow-sm"
                    />
                    {response && (
                      <p className="text-sm text-muted-foreground">{response}</p>
                    )}
                  </div>
                ) : (
                  <ScrollArea className="h-full">
                    <div className="pr-4">
                      <div
                        className="max-w-none text-base leading-relaxed 
     text-black
     [&_strong]:font-bold 
     [&_em]:italic 
     [&_li]:list-disc [&_li]:ml-4"
                      >
                        <ReactMarkdown>{response}</ReactMarkdown>
                      </div>
                    </div>
                  </ScrollArea>
                )}
              </div>

              {!isProcessing && (response || imageUrl) && (
                <div className="flex gap-2">
                  <Button
                    variant="default"
                    className="flex-1"
                    onClick={handleSave}
                  >
                    Save Annotation
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={handleDownload}
                    title="Download as document"
                    className="shrink-0"
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() =>
                      handleActionSelect(
                        AI_ACTIONS.find((a) => a.id === selectedAction)
                      )
                    }
                  >
                    Regenerate
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
