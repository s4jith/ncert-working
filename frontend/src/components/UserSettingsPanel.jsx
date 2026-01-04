/**
 * User Settings Panel
 * Allows users to set their preferred subject
 * Class level is fixed from user profile (students only study their own class)
 */

import React, { useState, useEffect } from "react";
import { Settings, BookOpen, Loader2, CheckCircle } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "./ui/sheet";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import useUserStore from "../stores/userStore";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function UserSettingsPanel({ open, onClose }) {
  const { user, setPreferredSubject } = useUserStore();
  const [availableSubjects, setAvailableSubjects] = useState([]);
  const [loading, setLoading] = useState(true);

  const languageDescriptions = {
    5: "Very simple language (Like talking to a 10-year-old)",
    6: "Simple, clear language (Like talking to a 11-year-old)",
    7: "Clear language with some details (Like talking to a 12-year-old)",
    8: "Standard language with technical terms explained (Like talking to a 13-year-old)",
    9: "Academic language with technical terms (Like talking to a 14-year-old)",
    10: "Full academic language (Board exam preparation level)",
    11: "Advanced academic language (Higher secondary level)",
    12: "Full academic language with exam focus (Board exam preparation)",
  };

  // Fetch available subjects for student's class level
  useEffect(() => {
    if (open) {
      fetchAvailableSubjects();
    }
  }, [open, user.classLevel]);

  const fetchAvailableSubjects = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/books/student/subjects?class_level=${user.classLevel}`);
      
      if (response.ok) {
        const data = await response.json();
        setAvailableSubjects(data.subjects || []);
      }
    } catch (err) {
      console.error("Failed to fetch subjects:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Sheet open={open} onOpenChange={onClose}>
      <SheetContent side="right" className="w-[400px] max-w-[90vw]">
        <SheetHeader className="mb-6">
          <SheetTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            User Settings
          </SheetTitle>
          <SheetDescription>
            Customize your learning experience
          </SheetDescription>
        </SheetHeader>

        <div className="space-y-6">
          {/* Class Level Display (Read-only) */}
          <div className="p-4 rounded-lg bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium text-gray-700">Your Class</p>
              <Badge className="bg-purple-600 text-white text-lg px-4 py-1">
                Class {user.classLevel}
              </Badge>
            </div>
            <p className="text-xs text-gray-500">
              Class level is set from your profile. Contact admin to update.
            </p>
          </div>

          {/* AI Language Level Info */}
          <div className="p-3 rounded-lg bg-muted/30">
            <p className="text-xs text-muted-foreground">
              <strong>AI Language Level:</strong>
            </p>
            <p className="text-sm mt-1">
              {languageDescriptions[user.classLevel] || languageDescriptions[10]}
            </p>
          </div>

          {/* Subject Selection - Real data from Pinecone */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <BookOpen className="h-4 w-4 text-muted-foreground" />
              <p className="text-sm font-medium">Preferred Subject</p>
            </div>
            
            {loading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                <span className="ml-2 text-sm text-muted-foreground">Loading subjects...</span>
              </div>
            ) : availableSubjects.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {availableSubjects.map((subject) => (
                  <Button
                    key={subject.name}
                    variant={user.preferredSubject === subject.name ? "default" : "outline"}
                    size="sm"
                    onClick={() => setPreferredSubject(subject.name)}
                    className="gap-1"
                  >
                    {subject.name}
                    {subject.has_ai_support && (
                      <CheckCircle className="h-3 w-3 text-green-500" />
                    )}
                  </Button>
                ))}
              </div>
            ) : (
              <div className="text-center py-4 text-sm text-muted-foreground">
                No subjects available for Class {user.classLevel} yet.
                <br />
                Please contact your admin to upload books.
              </div>
            )}
          </div>

          {/* Current Settings Summary */}
          <div className="mt-6 p-4 rounded-lg border bg-card">
            <p className="text-sm font-medium mb-3">Current Settings</p>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Class:</span>
                <Badge>Class {user.classLevel}</Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Subject:</span>
                <Badge variant="secondary">{user.preferredSubject}</Badge>
              </div>
            </div>
          </div>

          {/* Info Box */}
          <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800">
            <p className="text-xs text-blue-900 dark:text-blue-100">
              <strong>Tip:</strong> The AI will adjust its language complexity based on your class level. 
              Only subjects with uploaded books for your class are shown here.
            </p>
          </div>

          <Button className="w-full" onClick={onClose}>
            Save Settings
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
