import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  BookOpen,
  MessageSquare,
  FileText,
  BarChart3,
  Settings,
  LogOut,
  Menu,
  X,
  Sparkles,
  HelpCircle,
  LayoutGrid,
  GraduationCap,
  StickyNote
} from "lucide-react";
import useUserStore from "../../stores/userStore";
import ChatbotPanel from "./ChatbotPanel";

/**
 * DashboardLayout Component
 * 
 * Light themed sidebar with orange Pro card.
 */

const navItems = [
  {
    id: "ai-chat",
    label: "AI Chat Helper",
    icon: MessageSquare,
    path: null,
    isChat: true,
    highlight: true
  },
  {
    id: "book-to-bot",
    label: "Book to Bot",
    icon: BookOpen,
    path: "/book-to-bot",
    badge: "PRO"
  },
  {
    id: "test",
    label: "My Tests",
    icon: LayoutGrid,
    path: "/test",
    badge: "PRO"
  },
  {
    id: "notes",
    label: "Your Notes",
    icon: StickyNote,
    path: "/notes"
  },
  {
    id: "report-card",
    label: "Statistics",
    icon: BarChart3,
    path: "/report-card",
    badge: "PRO"
  },
  {
    id: "about-you",
    label: "Settings",
    icon: Settings,
    path: "/about-you"
  },
  {
    id: "help",
    label: "Updates & FAQ",
    icon: HelpCircle,
    path: "/help"
  },
];

export default function DashboardLayout({ children }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useUserStore();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [chatbotOpen, setChatbotOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleNavClick = (item) => {
    if (item.isChat) {
      setChatbotOpen(true);
    } else if (item.path) {
      navigate(item.path);
    }
  };

  const isActive = (path) => location.pathname === path;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-gray-50">
      {/* Sidebar - Light Theme */}
      <aside
        className={`flex-shrink-0 transition-all duration-300 bg-white border-r border-gray-100 flex flex-col ${sidebarOpen ? "w-64" : "w-20"
          }`}
      >
        {/* Logo */}
        <div className="p-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            {sidebarOpen && (
              <span className="font-bold text-gray-900 text-lg">The brainwave</span>
            )}
          </div>
          {sidebarOpen && (
            <div className="w-6 h-6 rounded border border-gray-300 flex items-center justify-center">
              <div className="w-2 h-3 border border-gray-400 rounded-sm" />
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-2 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = item.path && isActive(item.path);

            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item)}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-xl transition-all duration-200 ${item.highlight
                  ? "bg-gray-100 border border-gray-200 text-gray-900"
                  : active
                    ? "bg-gray-100 text-gray-900"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                  }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-5 h-5 ${item.highlight || active ? 'text-gray-900' : 'text-gray-400'}`} />
                  {sidebarOpen && (
                    <span className="font-medium text-sm">{item.label}</span>
                  )}
                </div>
                {sidebarOpen && item.badge && (
                  <span className="px-2 py-0.5 rounded text-xs font-semibold bg-orange-100 text-orange-600 border border-orange-200">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Pro Plan Card - Orange Gradient */}
        {sidebarOpen && (
          <div className="px-3 pb-3">
            <div
              className="rounded-2xl p-5 relative overflow-hidden"
              style={{
                background: 'linear-gradient(135deg, #f97316 0%, #ea580c 50%, #dc2626 100%)'
              }}
            >
              {/* Decorative circles */}
              <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-white/30" />
              <div className="absolute top-8 right-6 w-3 h-3 rounded-full bg-white/20" />
              <div className="absolute bottom-12 right-4 w-16 h-16 rounded-full bg-white/10 blur-sm" />

              <div className="relative z-10">
                <div className="w-10 h-10 rounded-lg bg-white/20 backdrop-blur-sm flex items-center justify-center mb-3">
                  <GraduationCap className="w-5 h-5 text-white" />
                </div>
                <h3 className="text-white font-bold text-lg mb-1">Pro Plan</h3>
                <p className="text-white/80 text-xs mb-4">
                  Unlock all features and strengthen your learning!
                </p>
                <div className="flex items-center justify-between">
                  <span className="text-white font-semibold">1000 / mo</span>
                  <button className="px-4 py-1.5 rounded-sm bg-white text-gray-900 text-sm font-semibold hover:bg-gray-100 transition-colors">
                    Live soon
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Logout */}
        <div className="p-3 border-t border-gray-100">
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-between px-4 py-3 rounded-xl text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors"
          >
            <span className="font-medium text-sm">Log out</span>
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-6">
        {children}
      </main>

      {/* Mobile Menu Toggle */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="fixed bottom-4 left-4 z-40 lg:hidden p-3 rounded-full bg-white text-gray-900 shadow-lg border border-gray-200"
      >
        {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Chatbot Panel */}
      <ChatbotPanel isOpen={chatbotOpen} onClose={() => setChatbotOpen(false)} />
    </div>
  );
}
