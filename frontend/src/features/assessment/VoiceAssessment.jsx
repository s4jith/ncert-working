import { useState, useEffect, useRef } from "react";
import { Mic, MicOff, Volume2, CheckCircle, Loader2 } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import { Progress } from "../../components/ui/progress";

/**
 * Voice Assessment Component
 *
 * Appears after completing 4 pages of lesson.
 * Uses voice input/output for questions and answers.
 *
 * TODO: Backend Integration
 * =========================
 * 1. POST /api/assessments - Submit voice assessment
 * 2. POST /api/assessments/evaluate - Send audio for evaluation
 * 3. GET /api/assessments/score - Get evaluation results
 *
 * Web Speech API:
 * - SpeechRecognition: For voice input
 * - SpeechSynthesis: For voice output (questions)
 */

export default function VoiceAssessment({ lessonId, onComplete, onClose }) {
  const [isListening, setIsListening] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [transcript, setTranscript] = useState("");
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [score, setScore] = useState(null);

  const recognitionRef = useRef(null);
  const synthesisRef = useRef(null);

  // Sample questions - TODO: Load from backend based on lesson
  const questions = [
    "What did you learn from this lesson?",
    "Can you explain the main concept?",
    "How would you apply this knowledge?",
  ];

  // Initialize Web Speech API
  useEffect(() => {
    if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
      const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = "en-US";

      recognitionRef.current.onresult = (event) => {
        const text = event.results[0][0].transcript;
        setTranscript(text);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      window.speechSynthesis.cancel();
    };
  }, []);

  // Speak question
  const speakQuestion = (text) => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel(); // Stop any ongoing speech
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      utterance.volume = 1;

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);

      window.speechSynthesis.speak(utterance);
    }
  };

  // Start listening
  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      setTranscript("");
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  // Stop listening
  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  };

  // Submit answer and move to next question
  const submitAnswer = () => {
    const newAnswers = [
      ...answers,
      {
        question: questions[currentQuestion],
        answer: transcript,
        timestamp: new Date().toISOString(),
      },
    ];
    setAnswers(newAnswers);
    setTranscript("");

    if (currentQuestion < questions.length - 1) {
      // Move to next question
      setCurrentQuestion(currentQuestion + 1);
      setTimeout(() => speakQuestion(questions[currentQuestion + 1]), 500);
    } else {
      // All questions answered, evaluate
      evaluateAnswers(newAnswers);
    }
  };

  // Evaluate answers with backend
  const evaluateAnswers = async (allAnswers) => {
    setIsEvaluating(true);

    // TODO: Send to backend for AI evaluation
    // const response = await fetch('/api/assessments/evaluate', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({
    //     lessonId,
    //     answers: allAnswers
    //   })
    // });
    // const result = await response.json();

    // Simulate evaluation
    setTimeout(() => {
      const simulatedScore = Math.floor(Math.random() * 30) + 70; // 70-100
      setScore(simulatedScore);
      setIsEvaluating(false);

      // Speak the score
      speakQuestion(
        `Your score is ${simulatedScore} out of 100. ${
          simulatedScore >= 80 ? "Excellent work!" : "Good effort!"
        }`
      );
    }, 2000);
  };

  // Start assessment
  useEffect(() => {
    if (questions.length > 0) {
      setTimeout(() => {
        speakQuestion(`Let's begin the assessment. ${questions[0]}`);
      }, 500);
    }
  }, []);

  const progress = ((currentQuestion + 1) / questions.length) * 100;

  return (
    <div className="fixed inset-0 z-50 bg-background flex items-stretch">
      {/* Split Screen Layout */}
      <div className="flex w-full h-full">
        {/* Left Side - Virtual Companion (AI) */}
        <div className="w-1/2 bg-card border-r border-primary/20 flex flex-col items-center justify-center p-8">
          <div className="text-center max-w-md">
            {/* AI Avatar */}
            <div className="w-32 h-32 mx-auto mb-6 rounded-full bg-primary/10 border-4 border-primary flex items-center justify-center">
              <Volume2
                className={`h-16 w-16 ${
                  isSpeaking ? "text-primary animate-pulse" : "text-primary/50"
                }`}
              />
            </div>

            <h3 className="text-2xl font-bold text-primary mb-2">
              Virtual Companion
            </h3>
            <p className="text-sm text-muted-foreground mb-8">
              AI Assessment Assistant
            </p>

            {/* Question Display */}
            {!isEvaluating && score === null && (
              <div className="mb-6">
                <div className="bg-primary/5 rounded-lg p-6 border border-primary/20">
                  <p className="text-lg font-medium leading-relaxed">
                    {questions[currentQuestion]}
                  </p>
                </div>

                {/* Progress Indicator */}
                <div className="mt-4">
                  <p className="text-xs text-muted-foreground mb-2">
                    Question {currentQuestion + 1} of {questions.length}
                  </p>
                  <Progress value={progress} className="h-1.5" />
                </div>
              </div>
            )}

            {/* Evaluation State */}
            {isEvaluating && (
              <div className="py-8">
                <Loader2 className="h-12 w-12 mx-auto mb-4 animate-spin text-primary" />
                <p className="text-lg font-medium">Evaluating...</p>
              </div>
            )}

            {/* Score Display */}
            {score !== null && (
              <div className="py-4">
                <CheckCircle className="h-16 w-16 mx-auto mb-4 text-emerald-600" />
                <h3 className="text-5xl font-bold text-primary mb-2">
                  {score}
                </h3>
                <p className="text-sm text-muted-foreground mb-4">out of 100</p>
                <p className="text-lg font-medium">
                  {score >= 80 ? "🎉 Excellent work!" : "👍 Good effort!"}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Right Side - You (User) */}
        <div className="w-1/2 bg-background flex flex-col items-center justify-center p-8">
          <div className="text-center max-w-md w-full">
            {/* User Avatar */}
            <div className="w-32 h-32 mx-auto mb-6 rounded-full bg-muted border-4 border-muted-foreground/20 flex items-center justify-center">
              <div className="w-16 h-16 rounded-full bg-muted-foreground/20" />
            </div>

            <h3 className="text-2xl font-bold mb-2">You</h3>
            <p className="text-sm text-muted-foreground mb-8">Student</p>

            {/* User Interaction Area */}
            {!isEvaluating && score === null && (
              <>
                {/* Voice Input */}
                <div className="mb-6">
                  <Button
                    size="lg"
                    className={`h-28 w-28 rounded-full mx-auto ${
                      isListening
                        ? "bg-red-600 hover:bg-red-700 animate-pulse"
                        : "bg-primary hover:bg-primary/90"
                    }`}
                    onClick={isListening ? stopListening : startListening}
                    disabled={isSpeaking}
                  >
                    {isListening ? (
                      <MicOff className="h-12 w-12" />
                    ) : (
                      <Mic className="h-12 w-12" />
                    )}
                  </Button>

                  <p className="text-center text-sm text-muted-foreground mt-4">
                    {isListening
                      ? "Listening... Speak now"
                      : "Tap to speak your answer"}
                  </p>
                </div>

                {/* Transcript Display */}
                {transcript && (
                  <div className="mb-6 p-4 bg-muted/30 rounded-lg border border-muted-foreground/20 min-h-[120px]">
                    <p className="text-xs font-medium text-muted-foreground mb-2">
                      YOUR ANSWER:
                    </p>
                    <p className="text-sm leading-relaxed">{transcript}</p>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex flex-col gap-3 w-full">
                  <Button
                    size="lg"
                    className="w-full"
                    onClick={submitAnswer}
                    disabled={!transcript || isListening || isSpeaking}
                  >
                    {currentQuestion < questions.length - 1
                      ? "Next Question →"
                      : "Submit Assessment"}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={onClose}
                  >
                    Cancel
                  </Button>
                </div>
              </>
            )}

            {/* Waiting/Evaluating State */}
            {isEvaluating && (
              <div className="py-8">
                <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-muted animate-pulse flex items-center justify-center">
                  <Loader2 className="h-10 w-10 animate-spin" />
                </div>
                <p className="text-sm text-muted-foreground">Processing...</p>
              </div>
            )}

            {/* Result State */}
            {score !== null && (
              <div className="w-full">
                {/* Answers Review */}
                <div className="mb-6 space-y-3 max-h-[400px] overflow-y-auto">
                  <h4 className="text-xs font-semibold text-muted-foreground mb-3">
                    YOUR ANSWERS:
                  </h4>
                  {answers.map((item, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-muted/30 rounded-lg border border-muted-foreground/10"
                    >
                      <p className="text-xs font-medium text-primary mb-1">
                        Q{idx + 1}: {item.question}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {item.answer}
                      </p>
                    </div>
                  ))}
                </div>

                <Button
                  size="lg"
                  className="w-full"
                  onClick={() => onComplete(score)}
                >
                  Continue Learning →
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
