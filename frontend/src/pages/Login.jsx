import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Eye, EyeOff, Lock, KeyRound } from "lucide-react";
import useUserStore from "../stores/userStore";
import { AnimatedCharacters } from "../components/ui/animated-characters";
import { Slack } from "lucide-react";

const API_BASE = "http://localhost:8000";
const ADMIN_EMAIL = "admin1@gmail.com";
const ADMIN_PASSWORD = "admin1234";

export default function Login() {
  const navigate = useNavigate();
  const { setUser } = useUserStore();
  
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [selectedRole, setSelectedRole] = useState("student");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [isTypingPassword, setIsTypingPassword] = useState(false);
  const [showPasswordChange, setShowPasswordChange] = useState(false);
  const [tempUserId, setTempUserId] = useState(null);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!userId || !password) {
      setError("Please fill in all fields");
      return;
    }
    setIsLoading(true);
    setError("");

    // Check for hardcoded admin credentials (admin can use email or user_id)
    if ((userId === ADMIN_EMAIL || userId === "admin1") && password === ADMIN_PASSWORD) {
      setUser({
        id: "admin-root",
        user_id: "ADMIN_ROOT",
        name: "Administrator",
        email: ADMIN_EMAIL,
        role: "admin",
        classLevel: null,
        isOnboarded: true
      });
      navigate("/admin-dashboard");
      setIsLoading(false);
      return;
    }

    // For teacher role, try backend
    if (selectedRole === "teacher") {
      try {
        const res = await fetch(`${API_BASE}/api/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId, password: password, role: "teacher" })
        });
        const data = await res.json();
        if (data.success) {
          if (data.first_login) {
            setTempUserId(data.user_id);
            setShowPasswordChange(true);
            setIsLoading(false);
            return;
          }
          setUser({
            id: data.user.id,
            user_id: data.user.user_id,
            name: data.user.name,
            email: data.user.email,
            role: "teacher",
            classLevel: null,
            isOnboarded: true,
            session_id: data.session_id
          });
          navigate("/staff-tests");
        } else {
          setError(data.error || "Invalid teacher credentials");
        }
      } catch (err) {
        console.error("Teacher login error:", err);
        setError("Login failed. Please check your credentials.");
      }
      setIsLoading(false);
      return;
    }

    // For student, try backend with user_id
    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, password: password, role: "student" })
      });
      const data = await res.json();
      if (data.success) {
        if (data.first_login) {
          setTempUserId(data.user_id);
          setShowPasswordChange(true);
          setIsLoading(false);
          return;
        }
        setUser({
          id: data.user.id,
          user_id: data.user.user_id,
          name: data.user.name,
          email: data.user.email,
          role: "student",
          classLevel: data.user.class_level || 10,
          isOnboarded: data.user.is_onboarded || false,
          session_id: data.session_id
        });
        // Navigate based on onboarding status
        if (data.user.is_onboarded) {
          navigate("/dashboard");
        } else {
          navigate("/onboarding");
        }
      } else {
        setError(data.error || "Invalid student credentials");
      }
    } catch (err) {
      console.error("Student login error:", err);
      setError("Login failed. Please check your credentials and ensure the server is running.");
    }
    setIsLoading(false);
  };

  const handlePasswordChange = async () => {
    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    setIsLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/api/auth/change-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: tempUserId, old_password: password, new_password: newPassword })
      });
      const data = await res.json();
      if (data.success) {
        setPassword(newPassword);
        setShowPasswordChange(false);
        alert("Password changed successfully!");
        setNewPassword("");
        setConfirmPassword("");
      } else {
        setError(data.error || "Failed to change password");
      }
    } catch (err) {
      setError("Failed to change password");
    }
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen w-full flex bg-white page-animate">
      <div className="hidden lg:flex lg:w-1/2 flex-col items-center justify-between bg-slate-50 py-12">
        <div className="mb-2 flex items-center gap-2 relative right-[150px]">
          <Slack />
          <h1 className="text-3xl font-bold tracking-wide" style={{ fontFamily: "Space Grotesk, sans-serif", color: "#ef4444" }}>
            THE BRAINWAVE
          </h1>
          <p className="absolute -bottom-[60px] left-12 text-[10px] font-bold text-slate-400 uppercase tracking-[0.2em]">
            Synchronizing minds with smarter learning. Built for focus, clarity, and growth.
          </p>
        </div>
        <div>
          <AnimatedCharacters password={password} showPassword={showPassword} isTyping={isTypingPassword} />
        </div>
      </div>
      <div className="w-full lg:w-1/2 flex items-center justify-center px-8">
        <div className="w-full max-w-md">
          <div className="text-center mb-10">
            <h1 className="text-4xl font-bold text-gray-900 mb-3">Welcome back!</h1>
            <p className="text-gray-500">Sign in with your User ID and password to continue.</p>
          </div>
          <div className="flex justify-center gap-6 mb-8">
            <button type="button" onClick={() => setSelectedRole("student")} className={`text-sm font-medium transition-colors ${selectedRole === "student" ? "text-green-500" : "text-gray-400 hover:text-gray-600"}`}>Student</button>
            <span className="text-gray-300">|</span>
            <button type="button" onClick={() => setSelectedRole("teacher")} className={`text-sm font-medium transition-colors ${selectedRole === "teacher" ? "text-green-500" : "text-gray-400 hover:text-gray-600"}`}>Teacher</button>
          </div>
          <form onSubmit={handleLogin} className="space-y-4">
            <input type="text" placeholder="Your User ID (e.g., varun141)" value={userId} onChange={(e) => setUserId(e.target.value)} className="w-full h-14 px-5 bg-gray-100 rounded-2xl text-gray-900 placeholder:text-gray-400 outline-none focus:ring-2 focus:ring-gray-200 transition-all" />
            <div className="relative">
              <input type={showPassword ? "text" : "password"} placeholder="Your password" value={password} onChange={(e) => setPassword(e.target.value)} onFocus={() => setIsTypingPassword(true)} onBlur={() => setIsTypingPassword(false)} className="w-full h-14 px-5 pr-12 bg-gray-100 rounded-2xl text-gray-900 placeholder:text-gray-400 outline-none focus:ring-2 focus:ring-gray-200 transition-all" />
              <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
            <div className="text-left">
              <button type="button" className="text-sm text-green-500 hover:text-green-600">Forgot password?</button>
            </div>
            {error && <p className="text-red-500 text-sm text-center">{error}</p>}
            <button type="submit" disabled={isLoading} className="w-full h-14 mt-4 font-semibold rounded-2xl bg-gray-900 hover:bg-gray-800 text-white transition-colors">
              {isLoading ? "Signing in..." : "Sign In"}
            </button>
          </form>
          <div className="text-center mt-10 text-gray-400 text-sm">
            <p>Please contact your administrator if you need an account.</p>
          </div>
        </div>
      </div>
      {showPasswordChange && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-8 w-full max-w-md shadow-xl">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <KeyRound className="w-8 h-8 text-green-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900">Change Your Password</h2>
              <p className="text-gray-500 mt-2">This is your first login. Please set a new password.</p>
            </div>
            <div className="space-y-4">
              <div className="relative">
                <input type="password" placeholder="New password (min 8 characters)" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="w-full h-14 px-5 pr-12 bg-gray-100 rounded-2xl text-gray-900 placeholder:text-gray-400 outline-none focus:ring-2 focus:ring-green-200" />
                <Lock className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              </div>
              <div className="relative">
                <input type="password" placeholder="Confirm new password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="w-full h-14 px-5 pr-12 bg-gray-100 rounded-2xl text-gray-900 placeholder:text-gray-400 outline-none focus:ring-2 focus:ring-green-200" />
                <Lock className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              </div>
              {error && <p className="text-red-500 text-sm text-center">{error}</p>}
              <button onClick={handlePasswordChange} disabled={isLoading} className="w-full h-14 mt-4 font-semibold rounded-2xl bg-green-600 hover:bg-green-700 text-white transition-colors disabled:opacity-50">
                {isLoading ? "Changing..." : "Set New Password"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
