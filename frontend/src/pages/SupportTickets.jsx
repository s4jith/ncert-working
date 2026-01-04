import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import useUserStore from "../stores/userStore";
import DashboardLayout from "../components/dashboard/DashboardLayout";
import { Button } from "../components/ui/button";
import { 
  MessageSquare, 
  Plus, 
  Clock, 
  CheckCircle, 
  CheckCircle2,
  AlertCircle,
  Send,
  Eye,
  ChevronDown,
  ChevronUp,
  X,
  Loader2,
  Bell,
  ArrowLeft,
  Ticket
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const CATEGORIES = [
  { value: "general", label: "General Question" },
  { value: "technical", label: "Technical Issue" },
  { value: "content", label: "Content/Syllabus" },
  { value: "account", label: "Account Issue" },
  { value: "other", label: "Other" }
];

const PRIORITIES = [
  { value: "low", label: "Low", color: "text-gray-600 bg-gray-100" },
  { value: "medium", label: "Medium", color: "text-yellow-600 bg-yellow-100" },
  { value: "high", label: "High", color: "text-orange-600 bg-orange-100" },
  { value: "urgent", label: "Urgent", color: "text-red-600 bg-red-100" }
];

export default function SupportTickets() {
  const navigate = useNavigate();
  const { user, logout } = useUserStore();
  const isAdmin = user?.role === "admin" || user?.role === "teacher";
  
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState({ total: 0, open: 0, in_progress: 0, resolved: 0 });
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [expandedTicket, setExpandedTicket] = useState(null);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [replyText, setReplyText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [statusFilter, setStatusFilter] = useState("all");
  const [activeFilter, setActiveFilter] = useState("all");
  
  // New ticket form
  const [newTicket, setNewTicket] = useState({
    subject: "",
    description: "",
    category: "general",
    priority: "medium"
  });

  useEffect(() => {
    fetchTickets();
    fetchNotifications();
    if (isAdmin) {
      fetchStats();
    }
  }, [user.id, statusFilter]);

  const fetchTickets = async () => {
    try {
      const params = new URLSearchParams();
      if (!isAdmin) {
        params.append("user_id", user.id);
      }
      params.append("is_admin", isAdmin.toString());
      if (statusFilter !== "all") {
        params.append("status", statusFilter);
      }
      
      const res = await fetch(`${API_BASE}/api/support-tickets/?${params.toString()}`);
      const data = await res.json();
      setTickets(data.tickets || []);
    } catch (error) {
      console.error("Failed to fetch tickets:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/support-tickets/stats/summary`);
      const data = await res.json();
      setStats(data);
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  };

  const fetchNotifications = async () => {
    try {
      let url;
      if (isAdmin) {
        url = `${API_BASE}/api/support-tickets/notifications/admin`;
      } else {
        url = `${API_BASE}/api/support-tickets/notifications/user/${user.id}`;
      }
      const res = await fetch(url);
      const data = await res.json();
      setNotifications(data.notifications || []);
      setUnreadCount(data.unread_count || 0);
    } catch (error) {
      console.error("Failed to fetch notifications:", error);
    }
  };

  const handleCreateTicket = async (e) => {
    e.preventDefault();
    if (!newTicket.subject.trim() || !newTicket.description.trim()) return;
    
    setSubmitting(true);
    try {
      const params = new URLSearchParams();
      params.append("user_id", user.id);
      params.append("user_name", user.name || "Student");
      
      const res = await fetch(`${API_BASE}/api/support-tickets/?${params.toString()}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newTicket)
      });
      
      if (res.ok) {
        setShowCreateModal(false);
        setNewTicket({ subject: "", description: "", category: "general", priority: "medium" });
        fetchTickets();
      }
    } catch (error) {
      console.error("Failed to create ticket:", error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleReply = async (ticketId) => {
    if (!replyText.trim()) return;
    
    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/support-tickets/${ticketId}/reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: replyText,
          is_admin: isAdmin,
          author_name: isAdmin ? "Admin" : (user.name || "Student")
        })
      });
      
      if (res.ok) {
        setReplyText("");
        fetchTickets();
        fetchNotifications();
      }
    } catch (error) {
      console.error("Failed to add reply:", error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleMarkRead = async (ticketId) => {
    try {
      await fetch(`${API_BASE}/api/support-tickets/${ticketId}/mark-read?by_admin=${isAdmin}`, {
        method: "POST"
      });
      fetchTickets();
      fetchNotifications();
    } catch (error) {
      console.error("Failed to mark as read:", error);
    }
  };

  const handleResolve = async (ticketId) => {
    try {
      await fetch(`${API_BASE}/api/support-tickets/${ticketId}/resolve`, {
        method: "POST"
      });
      fetchTickets();
      fetchNotifications();
    } catch (error) {
      console.error("Failed to resolve ticket:", error);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      open: "bg-yellow-100 text-yellow-700",
      in_progress: "bg-blue-100 text-blue-700",
      resolved: "bg-green-100 text-green-700",
      closed: "bg-gray-100 text-gray-700"
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || styles.open}`}>
        {status.replace("_", " ").toUpperCase()}
      </span>
    );
  };

  const getPriorityBadge = (priority) => {
    const p = PRIORITIES.find(pr => pr.value === priority) || PRIORITIES[1];
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${p.color}`}>
        {p.label}
      </span>
    );
  };

  // Filter tickets for student view
  const filteredTickets = activeFilter === 'all' 
    ? tickets 
    : tickets.filter(ticket => ticket.status === activeFilter);

  return isAdmin ? (
    // Admin Layout
    <div className="min-h-screen bg-gray-50">
      {/* Admin Header */}
      <header className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <button 
                onClick={() => navigate("/admin-dashboard")} 
                className="text-white/80 hover:text-white flex items-center gap-2"
              >
                <ArrowLeft className="w-5 h-5" />
                Back to Dashboard
              </button>
              <div>
                <h1 className="text-2xl font-bold">Support Tickets 🎫</h1>
                <p className="text-purple-100 text-sm">Manage all support tickets</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              {unreadCount > 0 && (
                <div className="flex items-center gap-2 px-3 py-2 bg-white/20 rounded-lg">
                  <Bell className="w-4 h-4" />
                  <span className="text-sm font-medium">{unreadCount} new</span>
                </div>
              )}
              <span className="text-sm bg-white/20 px-3 py-1 rounded-full">{user?.email || "Admin"}</span>
              <button 
                onClick={() => { logout(); navigate("/"); }} 
                className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-md transition"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="space-y-6">
          {/* Admin Stats */}
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-xl border border-gray-100 shadow-sm">
              <p className="text-sm text-gray-500">Total</p>
              <p className="text-2xl font-bold text-gray-800">{stats.total}</p>
            </div>
            <div className="bg-white p-4 rounded-xl border border-yellow-200 shadow-sm">
              <p className="text-sm text-yellow-600">Open</p>
              <p className="text-2xl font-bold text-yellow-600">{stats.open}</p>
            </div>
            <div className="bg-white p-4 rounded-xl border border-blue-200 shadow-sm">
              <p className="text-sm text-blue-600">In Progress</p>
              <p className="text-2xl font-bold text-blue-600">{stats.in_progress}</p>
            </div>
            <div className="bg-white p-4 rounded-xl border border-green-200 shadow-sm">
              <p className="text-sm text-green-600">Resolved</p>
              <p className="text-2xl font-bold text-green-600">{stats.resolved}</p>
            </div>
          </div>

        {/* Filter */}
        <div className="flex gap-2">
          {["all", "open", "in_progress", "resolved", "closed"].map(status => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                statusFilter === status
                  ? "bg-gray-900 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {status === "all" ? "All" : status.replace("_", " ").charAt(0).toUpperCase() + status.replace("_", " ").slice(1)}
            </button>
          ))}
        </div>

        {/* Tickets List */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
          </div>
        ) : tickets.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center border border-gray-100">
            <MessageSquare className="w-12 h-12 mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-medium text-gray-800 mb-2">No tickets yet</h3>
            <p className="text-gray-500 mb-4">
              {isAdmin ? "No support tickets have been submitted" : "Need help? Create a support ticket"}
            </p>
            {!isAdmin && (
              <Button onClick={() => setShowCreateModal(true)} className="gap-2">
                <Plus className="w-4 h-4" />
                Create First Ticket
              </Button>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {tickets.map(ticket => (
              <div key={ticket.id} className="bg-white rounded-xl border border-gray-100 overflow-hidden">
                {/* Ticket Header */}
                <div 
                  className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                  onClick={() => {
                    setExpandedTicket(expandedTicket === ticket.id ? null : ticket.id);
                    if (isAdmin && !ticket.is_read_by_admin) {
                      handleMarkRead(ticket.id);
                    }
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        ticket.status === "open" ? "bg-yellow-100" :
                        ticket.status === "resolved" ? "bg-green-100" : "bg-blue-100"
                      }`}>
                        <MessageSquare className={`w-5 h-5 ${
                          ticket.status === "open" ? "text-yellow-600" :
                          ticket.status === "resolved" ? "text-green-600" : "text-blue-600"
                        }`} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-400">{ticket.ticket_number}</span>
                          {!ticket.is_read_by_admin && isAdmin && (
                            <span className="px-1.5 py-0.5 bg-red-500 text-white text-xs rounded">NEW</span>
                          )}
                        </div>
                        <h3 className="font-medium text-gray-800">{ticket.title}</h3>
                        <p className="text-sm text-gray-500">
                          by {ticket.created_by_name} • {new Date(ticket.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {getPriorityBadge(ticket.priority)}
                      {getStatusBadge(ticket.status)}
                      {expandedTicket === ticket.id ? (
                        <ChevronUp className="w-5 h-5 text-gray-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-gray-400" />
                      )}
                    </div>
                  </div>
                </div>

                {/* Expanded Content */}
                {expandedTicket === ticket.id && (
                  <div className="border-t border-gray-100 p-4 space-y-4">
                    {/* Description */}
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-sm text-gray-600 whitespace-pre-wrap">{ticket.description}</p>
                    </div>

                    {/* Read Status */}
                    {!isAdmin && ticket.is_read_by_admin && (
                      <div className="flex items-center gap-2 text-sm text-blue-600">
                        <Eye className="w-4 h-4" />
                        <span>Admin has viewed your ticket</span>
                        {ticket.read_at && (
                          <span className="text-gray-400">• {new Date(ticket.read_at).toLocaleString()}</span>
                        )}
                      </div>
                    )}

                    {/* Replies */}
                    {ticket.replies && ticket.replies.length > 0 && (
                      <div className="space-y-3">
                        <h4 className="text-sm font-medium text-gray-700">Conversation</h4>
                        {ticket.replies.map((reply, idx) => (
                          <div 
                            key={idx} 
                            className={`p-3 rounded-lg ${
                              reply.is_admin ? "bg-blue-50 ml-4" : "bg-gray-50 mr-4"
                            }`}
                          >
                            <div className="flex justify-between items-center mb-1">
                              <span className={`text-xs font-medium ${
                                reply.is_admin ? "text-blue-600" : "text-gray-600"
                              }`}>
                                {reply.author_name}
                              </span>
                              <span className="text-xs text-gray-400">
                                {new Date(reply.created_at).toLocaleString()}
                              </span>
                            </div>
                            <p className="text-sm text-gray-700">{reply.message}</p>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Reply Input */}
                    {ticket.status !== "closed" && ticket.status !== "resolved" && (
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={replyText}
                          onChange={(e) => setReplyText(e.target.value)}
                          placeholder="Type your reply..."
                          className="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          onKeyPress={(e) => e.key === "Enter" && handleReply(ticket.id)}
                        />
                        <Button 
                          onClick={() => handleReply(ticket.id)} 
                          disabled={submitting || !replyText.trim()}
                          className="gap-2"
                        >
                          {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                          Send
                        </Button>
                      </div>
                    )}

                    {/* Admin Actions */}
                    {isAdmin && ticket.status !== "resolved" && ticket.status !== "closed" && (
                      <div className="flex gap-2 pt-2 border-t border-gray-100">
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleResolve(ticket.id)}
                          className="gap-1"
                        >
                          <CheckCircle className="w-4 h-4" />
                          Mark Resolved
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        </div>
      </main>

      {/* Create Ticket Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-lg p-6 relative">
            <button 
              onClick={() => setShowCreateModal(false)}
              className="absolute top-4 right-4 p-1 hover:bg-gray-100 rounded-lg"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
            
            <h2 className="text-xl font-bold text-gray-800 mb-6">Create Support Ticket</h2>
            
            <form onSubmit={handleCreateTicket} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                <input
                  type="text"
                  value={newTicket.title}
                  onChange={(e) => setNewTicket({ ...newTicket, title: e.target.value })}
                  placeholder="Brief description of your issue"
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                  minLength={5}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={newTicket.description}
                  onChange={(e) => setNewTicket({ ...newTicket, description: e.target.value })}
                  placeholder="Describe your issue in detail..."
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 h-32 resize-none"
                  required
                  minLength={10}
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                  <select
                    value={newTicket.category}
                    onChange={(e) => setNewTicket({ ...newTicket, category: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    {CATEGORIES.map(cat => (
                      <option key={cat.value} value={cat.value}>{cat.label}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                  <select
                    value={newTicket.priority}
                    onChange={(e) => setNewTicket({ ...newTicket, priority: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    {PRIORITIES.map(p => (
                      <option key={p.value} value={p.value}>{p.label}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div className="flex justify-end gap-3 pt-4">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting} className="gap-2">
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  Submit Ticket
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  ) : (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Stats */}
        <div className="grid md:grid-cols-3 gap-4">
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-blue-50 rounded-lg">
                <Ticket className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Tickets</p>
                <p className="text-2xl font-bold text-gray-800">{tickets.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-amber-50 rounded-lg">
                <Clock className="w-6 h-6 text-amber-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Pending</p>
                <p className="text-2xl font-bold text-gray-800">
                  {tickets.filter(t => t.status === 'pending').length}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-green-50 rounded-lg">
                <CheckCircle2 className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Resolved</p>
                <p className="text-2xl font-bold text-gray-800">
                  {tickets.filter(t => t.status === 'resolved').length}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex gap-2 flex-wrap">
          {['all', 'pending', 'in_progress', 'resolved'].map((status) => (
            <button
              key={status}
              onClick={() => setActiveFilter(status)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeFilter === status
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
            >
              {status === 'all' ? 'All' : status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </button>
          ))}
        </div>

        {/* Tickets List */}
        <div className="space-y-4">
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
            </div>
          ) : filteredTickets.length === 0 ? (
            <div className="bg-white rounded-xl p-8 text-center">
              <Ticket className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600">No tickets found</p>
            </div>
          ) : (
            filteredTickets.map((ticket) => (
              <div
                key={ticket._id}
                onClick={() => setSelectedTicket(ticket)}
                className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-800 mb-1">{ticket.subject}</h3>
                    <p className="text-sm text-gray-600 line-clamp-2">{ticket.description}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    ticket.status === 'pending' ? 'bg-amber-100 text-amber-700' :
                    ticket.status === 'in_progress' ? 'bg-blue-100 text-blue-700' :
                    'bg-green-100 text-green-700'
                  }`}>
                    {ticket.status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                </div>
                
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    {new Date(ticket.created_at).toLocaleDateString()}
                  </span>
                  {ticket.priority && (
                    <span className={`flex items-center gap-1 ${
                      ticket.priority === 'high' ? 'text-red-600' :
                      ticket.priority === 'medium' ? 'text-amber-600' :
                      'text-green-600'
                    }`}>
                      <AlertCircle className="w-4 h-4" />
                      {ticket.priority}
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Create Button */}
        <button
          onClick={() => setShowCreateModal(true)}
          className="fixed bottom-6 right-6 p-4 bg-indigo-600 text-white rounded-full shadow-lg hover:bg-indigo-700 transition-colors"
        >
          <Plus className="w-6 h-6" />
        </button>
      </div>

      {/* Create Ticket Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-lg p-6 relative">
            <button 
              onClick={() => setShowCreateModal(false)}
              className="absolute top-4 right-4 p-1 hover:bg-gray-100 rounded-lg"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
            
            <h2 className="text-xl font-bold text-gray-800 mb-6">Create Support Ticket</h2>
            
            <form onSubmit={handleCreateTicket} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Subject *
                </label>
                <input
                  type="text"
                  value={newTicket.subject}
                  onChange={(e) => setNewTicket({ ...newTicket, subject: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description *
                </label>
                <textarea
                  value={newTicket.description}
                  onChange={(e) => setNewTicket({ ...newTicket, description: e.target.value })}
                  rows={4}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Priority
                </label>
                <select
                  value={newTicket.priority}
                  onChange={(e) => setNewTicket({ ...newTicket, priority: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>

              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  variant="outline"
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={submitting}
                  className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white"
                >
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  Submit Ticket
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}

