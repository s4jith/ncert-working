import React, { useState } from "react";
import { Sparkles, FileText, BookOpen } from "lucide-react";
import ReactMarkdown from "react-markdown";
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
  const { user } = useUserStore(); // Get user data including class level
  const [selectedAction, setSelectedAction] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [response, setResponse] = useState("");
  const [imageUrl, setImageUrl] = useState(null); // For Stick Flow images
  const [error, setError] = useState(null);

  const handleActionSelect = async (action) => {
    setSelectedAction(action.id);
    setIsProcessing(true);
    setError(null);
    setImageUrl(null); // Reset image

    try {
      console.log("🚀 Calling backend API...", {
        chapter: currentLesson?.number || 1,
        text: selectedText?.text,
        action: action.id
      });

      // Use unified annotation endpoint for all actions
      const result = await chatService.processAnnotation(
        selectedText?.text || "",
        action.id, // "define", "elaborate", or "stick_flow"
        user.classLevel,
        user.preferredSubject || "Social Science",
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

      // Reset and close
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
                  /* Stick Flow Image Display */
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
                      <div className="prose prose-sm max-w-none
                        [&_strong]:font-bold [&_strong]:text-gray-900 dark:[&_strong]:text-white
                        [&_em]:italic
                        [&_p]:my-2 [&_p]:text-gray-900 dark:[&_p]:text-gray-100
                        [&_ul]:list-disc [&_ul]:ml-5 [&_ul]:my-2
                        [&_ol]:list-decimal [&_ol]:ml-5 [&_ol]:my-2
                        [&_li]:my-1 [&_li]:text-gray-900 dark:[&_li]:text-gray-100
                        [&_h3]:font-bold [&_h3]:text-base [&_h3]:my-2 [&_h3]:text-gray-900 dark:[&_h3]:text-white
                        [&_h2]:font-bold [&_h2]:text-lg [&_h2]:my-2 [&_h2]:text-gray-900 dark:[&_h2]:text-white
                        [&_h1]:font-bold [&_h1]:text-xl [&_h1]:my-2 [&_h1]:text-gray-900 dark:[&_h1]:text-white
                      ">
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
