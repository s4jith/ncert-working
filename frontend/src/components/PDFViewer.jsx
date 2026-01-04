import { useState, useEffect } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import { Button } from "./ui/button";
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  History,
} from "lucide-react";
import { useAnnotations } from "../contexts/AnnotationContext";
import SelectionDialog from "./annotations/SelectionDialog";
import AIPanel from "./annotations/AIPanel";
import NotesPanel from "./annotations/NotesPanel";
import HistoryPanel from "./annotations/HistoryPanel";
import HighlightOverlay from "./annotations/HighlightOverlay";

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

export default function PDFViewer({ pdfUrl, currentLesson }) {
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.2);
  const [dialogPosition, setDialogPosition] = useState(null);
  const [showHistory, setShowHistory] = useState(false);

  const { setSelectedText, activePanel, setActivePanel } = useAnnotations();

  function onDocumentLoadSuccess({ numPages }) {
    setNumPages(numPages);
  }

  const handleTextSelection = (e) => {
    const selection = window.getSelection();
    const text = selection?.toString().trim();

    if (text && text.length > 0) {
      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();

      // Store selected text and position
      setSelectedText({
        text,
        position: {
          x: rect.left + rect.width / 2,
          y: rect.top,
        },
      });

      // Show selection dialog
      setDialogPosition({
        x: rect.left + rect.width / 2,
        y: rect.top,
      });
    } else {
      setDialogPosition(null);
    }
  };

  const goToPrevPage = () => {
    setPageNumber((prev) => Math.max(prev - 1, 1));
  };

  const goToNextPage = () => {
    setPageNumber((prev) => Math.min(prev + 1, numPages));
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
    <div className="flex flex-col h-full relative">
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
      <div className="flex-1 overflow-auto bg-muted/30 p-4">
        <div
          className="flex justify-center relative"
          onMouseUp={handleTextSelection}
        >
          <div className="relative">
            <Document
              file={pdfUrl}
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
                className="shadow-lg"
                renderTextLayer={true}
                renderAnnotationLayer={true}
              />
            </Document>

            {/* Highlight Overlay */}
            <HighlightOverlay
              pageNumber={pageNumber}
              scale={scale}
              currentLesson={currentLesson}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
