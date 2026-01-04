import React, { useState, useRef, useEffect } from "react";
import { MessageCircle, Send, X, Sparkles, Minimize2, Zap, Brain } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { ScrollArea } from "../../components/ui/scroll-area";
import useUserStore from "../../stores/userStore";
import { chatService } from "../../services/api";

/**
 * Student Chatbot - Floating chatbot for open-ended questions
 * Two modes: Quick (exam-style) and DeepDive (comprehensive with web content)
 */
export default function StudentChatbot({ currentLesson }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [chatMode, setChatMode] = useState("quick"); // "quick" or "deepdive"
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "👋 Hi! I'm your study assistant.\n\n**Quick Mode**: Direct, exam-style answers from your textbook.\n**DeepDive Mode**: Comprehensive explanations with additional context and related topics.\n\nChoose a mode and ask me anything!",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const { user } = useUserStore();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleModeChange = (mode) => {
    setChatMode(mode);
    const modeMessage = {
      role: "assistant",
      content: mode === "quick" 
        ? "✅ **Quick Mode activated!** I'll give you direct, exam-style answers from your textbook."
        : "✅ **DeepDive Mode activated!** I'll provide comprehensive explanations covering all aspects of the topic, including background context and related information.",
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, modeMessage]);
  };

  // Use lesson's subject if available, otherwise use user's preferred subject
  const effectiveSubject = currentLesson?.subject || user.preferredSubject || "Mathematics";

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isTyping) return;

    const userMessage = {
      role: "user",
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsTyping(true);

    try {
      console.log("🚀 Sending chat request:", {
        question: userMessage.content,
        classLevel: user.classLevel || 6,
        subject: effectiveSubject,
        chapter: currentLesson?.number || 1,
        mode: chatMode
      });
      
      const result = await chatService.studentChat(
        userMessage.content,
        user.classLevel || 6,
        effectiveSubject,
        currentLesson?.number || 1,
        chatMode // Pass the mode to backend
      );

      const assistantMessage = {
        role: "assistant",
        content: result.answer,
        timestamp: new Date(),
        sources: result.sources,
        mode: chatMode,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Student chat error:", error);
      const errorMessage = {
        role: "assistant",
        content: "Sorry, I couldn't process that. Please try again.",
        timestamp: new Date(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 group"
        aria-label="Open student chatbot"
      >
        <div className="relative">
          {/* Pulsing ring effect */}
          <span className="absolute inset-0 rounded-full bg-violet-500 opacity-75 animate-ping"></span>
          
          {/* Main button */}
          <div className="relative flex items-center justify-center w-16 h-16 bg-gradient-to-br from-violet-600 to-purple-700 rounded-full shadow-lg transition-all duration-300 group-hover:scale-110 group-hover:shadow-xl">
            <MessageCircle className="w-8 h-8 text-white" />
            
            {/* Sparkle indicator */}
            <div className="absolute -top-1 -right-1 w-4 h-4 bg-yellow-400 rounded-full flex items-center justify-center animate-bounce">
              <Sparkles className="w-3 h-3 text-white" />
            </div>
          </div>
        </div>
      </button>
    );
  }

  return (
    <div
      className={`fixed bottom-6 right-6 z-50 bg-white rounded-2xl shadow-2xl border border-gray-200 transition-all duration-300 ${
        isMinimized ? "w-80 h-16" : "w-96 h-[600px]"
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-gradient-to-r from-violet-600 to-purple-700 rounded-t-2xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
            <MessageCircle className="w-6 h-6 text-white" />
          </div>
          <div className="text-white">
            <h3 className="font-semibold text-sm">Study Assistant</h3>
            <p className="text-xs text-white/80">
              {chatMode === "quick" ? "Quick Mode" : "DeepDive Mode"}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsMinimized(!isMinimized)}
            className="h-8 w-8 text-white hover:bg-white/20"
          >
            <Minimize2 className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsOpen(false)}
            className="h-8 w-8 text-white hover:bg-white/20"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Mode Selector */}
          <div className="p-3 bg-gray-50 border-b flex gap-2">
            <button
              onClick={() => handleModeChange("quick")}
              className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                chatMode === "quick"
                  ? "bg-violet-600 text-white shadow-md"
                  : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-200"
              }`}
            >
              <Zap className="w-4 h-4" />
              Quick
            </button>
            <button
              onClick={() => handleModeChange("deepdive")}
              className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                chatMode === "deepdive"
                  ? "bg-violet-600 text-white shadow-md"
                  : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-200"
              }`}
            >
              <Brain className="w-4 h-4" />
              DeepDive
            </button>
          </div>

          {/* Messages */}
          <ScrollArea className="h-[calc(100%-12rem)] p-4">
            <div className="space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${
                    message.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                      message.role === "user"
                        ? "bg-violet-600 text-white"
                        : message.isError
                        ? "bg-red-50 text-red-800 border border-red-200"
                        : "bg-gray-100 text-gray-900"
                    }`}
                  >
                    <div className="text-sm leading-relaxed">
                      {message.role === "assistant" ? (
                        <div className="prose prose-sm max-w-none
                          [&_strong]:font-bold [&_strong]:text-gray-900
                          [&_em]:italic
                          [&_p]:my-2
                          [&_ul]:list-disc [&_ul]:ml-5 [&_ul]:my-2
                          [&_ol]:list-decimal [&_ol]:ml-5 [&_ol]:my-2
                          [&_li]:my-1
                          [&_h3]:font-bold [&_h3]:text-base [&_h3]:my-2
                          [&_h2]:font-bold [&_h2]:text-lg [&_h2]:my-2
                          [&_h1]:font-bold [&_h1]:text-xl [&_h1]:my-2
                        ">
                          <ReactMarkdown>{message.content}</ReactMarkdown>
                        </div>
                      ) : (
                        message.content
                      )}
                    </div>
                    <div
                      className={`text-xs mt-1 ${
                        message.role === "user"
                          ? "text-violet-200"
                          : "text-gray-500"
                      }`}
                    >
                      {new Date(message.timestamp).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </div>
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-2xl px-4 py-3">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.1s]"></span>
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Input */}
          <div className="absolute bottom-0 left-0 right-0 p-4 bg-white border-t rounded-b-2xl">
            <div className="flex gap-2">
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={
                  chatMode === "quick"
                    ? "Ask a direct question..."
                    : "Ask anything for deep explanation..."
                }
                className="flex-1 rounded-xl border-gray-300 focus:border-violet-500 focus:ring-violet-500"
                disabled={isTyping}
              />
              <Button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isTyping}
                className="rounded-xl bg-gradient-to-r from-violet-600 to-purple-700 hover:from-violet-700 hover:to-purple-800 text-white px-4"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
