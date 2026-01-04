import { useState, useEffect } from "react";
import { RefreshCw, Quote } from "lucide-react";
import quotesData from "../../data/quotes.json";

/**
 * QuoteCard Component
 * 
 * Displays random motivational quotes from the quotes.json file.
 */

export default function QuoteCard() {
  const [currentQuote, setCurrentQuote] = useState(null);

  const getRandomQuote = () => {
    const randomIndex = Math.floor(Math.random() * quotesData.quotes.length);
    setCurrentQuote(quotesData.quotes[randomIndex]);
  };

  useEffect(() => {
    getRandomQuote();
  }, []);

  if (!currentQuote) return null;

  return (
    <div 
      className="rounded-2xl p-6 shadow-sm border border-gray-100 relative overflow-hidden"
      style={{ 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}
    >
      {/* Decorative Quote Icon */}
      <Quote className="absolute top-4 right-4 w-12 h-12 text-white/20" />
      
      <div className="relative z-10">
        <p className="text-white text-lg font-medium leading-relaxed mb-4">
          "{currentQuote.text}"
        </p>
        <p className="text-white/80 text-sm">
          — {currentQuote.author}
        </p>
      </div>

      {/* Refresh Button */}
      <button
        onClick={getRandomQuote}
        className="absolute bottom-4 right-4 p-2 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
      >
        <RefreshCw className="w-4 h-4 text-white" />
      </button>
    </div>
  );
}
