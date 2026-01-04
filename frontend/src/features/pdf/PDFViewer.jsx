import { useState, useEffect } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import { Button } from "../../components/ui/button";
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  History,
  Eye,
  EyeOff,
} from "lucide-react";
import useAnnotationStore from "../../stores/annotationStore";
import SelectionDialog from "../annotations/SelectionDialog";
import AIPanel from "../annotations/AIPanel";
import NotesPanel from "../annotations/NotesPanel";
import HistoryPanel from "../annotations/HistoryPanel";
import HighlightOverlay from "../annotations/HighlightOverlay";

import ErrorBoundary from "../../components/ErrorBoundary";

/**
 * PDF Viewer Component
 *
 * Main component for displaying and interacting with PDF documents.
 * Handles text selection, zoom, navigation, and annotation creation.
 */

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

export default function PDFViewer({ pdfUrl, currentLesson }) {
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.2);
  const [dialogPosition, setDialogPosition] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [direction, setDirection] = useState("next"); // 'next' or 'prev'
  const [pagesCompleted, setPagesCompleted] = useState(0);
  const [showAnnotations, setShowAnnotations] = useState(true);

  const setSelectedText = useAnnotationStore((state) => state.setSelectedText);
  const activePanel = useAnnotationStore((state) => state.activePanel);
  const setActivePanel = useAnnotationStore((state) => state.setActivePanel);

  function onDocumentLoadSuccess({ numPages }) {
    setNumPages(numPages);
  }

  // Keyboard navigation for natural book reading
  useEffect(() => {
    const handleKeyPress = (e) => {
      // Prevent navigation when typing in inputs
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") {
        return;
      }

      switch (e.key) {
        case "ArrowRight":
        case " ": // Spacebar
        case "PageDown":
          e.preventDefault();
          goToNextPage();
          break;
        case "ArrowLeft":
        case "PageUp":
          e.preventDefault();
          goToPrevPage();
          break;
        case "Home":
          e.preventDefault();
          setDirection("prev");
          setPageNumber(1);
          break;
        case "End":
          e.preventDefault();
          setDirection("next");
          setPageNumber(numPages);
          break;
      }
    };

    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, [pageNumber, numPages, isTransitioning]);

  const handleTextSelection = (e) => {
    const selection = window.getSelection();
    const text = selection?.toString().trim();

    if (text && text.length > 0) {
      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();

      // Get PDF container position for accurate positioning
      const pdfContainer = e.currentTarget.querySelector(".react-pdf__Page");
      const containerRect = pdfContainer?.getBoundingClientRect() || rect;

      // Calculate position relative to PDF page
      const relativeX = rect.left - containerRect.left + rect.width / 2;
      const relativeY = rect.top - containerRect.top + rect.height / 2;

      // Store selected text and position
      setSelectedText({
        text,
        position: {
          x: relativeX,
          y: relativeY,
        },
      });

      // Show selection dialog at absolute screen position
      setDialogPosition({
        x: rect.left + rect.width / 2,
        y: rect.top,
      });
    } else {
      setDialogPosition(null);
    }
  };

  const goToPrevPage = () => {
    if (pageNumber <= 1 || isTransitioning) return;
    setDirection("prev");
    setIsTransitioning(true);
    setTimeout(() => {
      setPageNumber((prev) => Math.max(prev - 1, 1));
      setTimeout(() => setIsTransitioning(false), 150);
    }, 200);
  };

  const goToNextPage = () => {
    if (pageNumber >= numPages || isTransitioning) return;
    setDirection("next");
    setIsTransitioning(true);
    setTimeout(() => {
      setPageNumber((prev) => {
        const nextPage = Math.min(prev + 1, numPages);
        // Track page completion
        if (nextPage > pagesCompleted) {
          setPagesCompleted(nextPage);
        }
        return nextPage;
      });
      setTimeout(() => setIsTransitioning(false), 150);
    }, 200);
  };

  const zoomIn = () => {
    setScale((prev) => Math.min(prev + 0.2, 3));
  };

  const zoomOut = () => {
    setScale((prev) => Math.max(prev - 0.2, 0.5));
  };

  const handleAIClick = () => {
    setDialogPosition(null);
    setActivePanel("ai");
  };

  const handleNoteClick = () => {
    setDialogPosition(null);
    setActivePanel("note");
  };

  const handleClosePanel = () => {
    setActivePanel(null);
    setSelectedText(null);
  };

  return (
    <div className="flex flex-col h-full relative ">
      {/* Selection Dialog */}
      <SelectionDialog
        position={dialogPosition}
        onAI={handleAIClick}
        onNote={handleNoteClick}
      />

      {/* Panels */}
      <AIPanel
        open={activePanel === "ai"}
        onClose={handleClosePanel}
        currentLesson={currentLesson}
        pageNumber={pageNumber}
      />
      <NotesPanel
        open={activePanel === "note"}
        onClose={handleClosePanel}
        currentLesson={currentLesson}
        pageNumber={pageNumber}
      />
      <HistoryPanel
        open={showHistory || activePanel === "history"}
        onClose={() => {
          setShowHistory(false);
          setActivePanel(null);
        }}
        currentLesson={currentLesson}
      />

      {/* PDF Controls */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-card">
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={goToPrevPage}
            disabled={pageNumber <= 1}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-sm font-medium min-w-[100px] text-center">
            Page {pageNumber} of {numPages || "--"}
          </span>
          <Button
            variant="outline"
            size="icon"
            onClick={goToNextPage}
            disabled={pageNumber >= numPages}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => setShowAnnotations(!showAnnotations)}
            title={showAnnotations ? "Hide annotations" : "Show annotations"}
          >
            {showAnnotations ? (
              <Eye className="h-4 w-4" />
            ) : (
              <EyeOff className="h-4 w-4" />
            )}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowHistory(true)}
            className="mr-4"
          >
            <History className="h-4 w-4 mr-2" />
            History
          </Button>

          <Button variant="outline" size="icon" onClick={zoomOut}>
            <ZoomOut className="h-4 w-4" />
          </Button>
          <span className="text-sm font-medium min-w-[60px] text-center">
            {Math.round(scale * 100)}%
          </span>
          <Button variant="outline" size="icon" onClick={zoomIn}>
            <ZoomIn className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* PDF Content */}
      <div className="flex-1 overflow-auto bg-gradient-to-b from-muted/20 to-muted/40 p-6">
        <div
          className="flex justify-center relative book-container"
          onMouseUp={handleTextSelection}
        >
          <div
            className={`relative transition-all duration-300 ease-out ${isTransitioning
              ? direction === "next"
                ? "page-turn-next"
                : "page-turn-prev"
              : "page-turn-idle"
              }`}
          >
            <Document
              file={pdfUrl}
              className=" page page-turn"
              onLoadSuccess={onDocumentLoadSuccess}
              loading={
                <div className="flex items-center justify-center h-[600px]">
                  <div className="text-muted-foreground">Loading PDF...</div>
                </div>
              }
              error={
                <div className="flex items-center justify-center h-[600px]">
                  <div className="text-destructive">Failed to load PDF</div>
                </div>
              }
            >
              <Page
                pageNumber={pageNumber}
                scale={scale}
                className="pdf-page-shadow rounded-lg overflow-hidden"
                renderTextLayer={true}
                renderAnnotationLayer={true}
              />
            </Document>

            {/* Highlight Overlay */}
            {showAnnotations && (
              <HighlightOverlay
                pageNumber={pageNumber}
                scale={scale}
                currentLesson={currentLesson}
              />
            )}
          </div>
        </div>
      </div>


    </div>
  );
}
