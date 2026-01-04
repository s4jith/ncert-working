import { useState } from "react";
import { Send, HelpCircle, CheckCircle } from "lucide-react";

/**
 * SupportCard Component
 * 
 * Allows users to raise support tickets/complaints.
 * 
 * TODO: Backend Integration
 * - POST support ticket to API
 * - Get ticket status updates
 * - Show ticket history
 */

export default function SupportCard() {
  const [message, setMessage] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    setLoading(true);
    
    // TODO: Replace with actual API call
    // await api.post('/support/tickets', { message });
    
    setTimeout(() => {
      setLoading(false);
      setSubmitted(true);
      setMessage("");
      
      // Reset after 3 seconds
      setTimeout(() => setSubmitted(false), 3000);
    }, 800);
  };

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center gap-2 mb-4">
        <HelpCircle className="w-5 h-5 text-cyan-500" />
        <h3 className="text-lg font-semibold text-gray-800">Support</h3>
      </div>

      {submitted ? (
        <div className="flex flex-col items-center py-6 text-center">
          <CheckCircle className="w-12 h-12 text-green-500 mb-3" />
          <p className="text-green-600 font-medium">Ticket Submitted!</p>
          <p className="text-sm text-gray-500">We'll get back to you soon.</p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-3">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Describe your issue or question..."
            rows={3}
            className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-800 placeholder:text-gray-400 outline-none focus:ring-2 focus:ring-cyan-200 focus:border-cyan-400 resize-none transition-all"
          />
          <button
            type="submit"
            disabled={loading || !message.trim()}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-cyan-500 hover:bg-cyan-600 disabled:bg-gray-300 text-white font-medium rounded-xl transition-colors"
          >
            {loading ? (
              "Sending..."
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span>Submit Ticket</span>
              </>
            )}
          </button>
        </form>
      )}
    </div>
  );
}
