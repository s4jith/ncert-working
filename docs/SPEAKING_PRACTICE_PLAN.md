# 🎙️ AI Speaking Practice - Feature Plan

## 🎯 Feature Overview

**NEW PAGE:** AI Speaking Practice Room (Like Zoom but audio-only)

### What Students Get:
1. **Live Conversation** with AI tutor (voice-to-voice)
2. **Real-time Feedback** during conversation
3. **Detailed Analytics** after session:
   - Grammar score
   - Fluency score
   - Vocabulary usage
   - Pronunciation feedback
   - Confidence level
   - Speaking pace
   - Improvement suggestions

### Use Case:
- Practice English speaking
- Improve communication skills
- Get instant feedback
- Build confidence
- Prepare for presentations/exams

---

## 🎨 UI Design

### Main Interface (Like Zoom Meeting Room):

```
┌─────────────────────────────────────────────────────────┐
│              🎤 AI Speaking Practice Room                │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │                                                    │ │
│  │                  🤖 AI TUTOR                       │ │
│  │                                                    │ │
│  │           [Sound Wave Animation]                   │ │
│  │              ● AI is listening...                  │ │
│  │                                                    │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │  "Tell me about photosynthesis"              │ │ │
│  │  │  (AI's last question/response)               │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  │                                                    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │                                                    │ │
│  │                  👤 YOU                            │ │
│  │                                                    │ │
│  │           [Sound Wave Animation]                   │ │
│  │              🎤 Speaking...                        │ │
│  │                                                    │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │  "Photosynthesis is the process..."         │ │ │
│  │  │  (Your real-time transcription)              │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  │                                                    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌─────────────────────────────────────────────────────┤
│  │  🎤 [MIC ON/OFF]  ⏸️ [PAUSE]  🛑 [END SESSION]     │
│  └─────────────────────────────────────────────────────┘
│                                                          │
│  Session Stats:  ⏱️ 5:30  |  💬 12 exchanges  |  📊 Live│
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Conversation Flow

### Session Types:

#### 1. **Free Conversation** (Default)
```
AI: "Hello! Let's have a conversation. Tell me about your day!"
Student: "Today I went to school and learned math..."
AI: "That sounds interesting! What did you learn in math?"
Student: "We learned about fractions..."
AI: "Great! Can you explain what a fraction is?"
```

#### 2. **Topic-Based Practice**
```
Topics:
- Science concepts (Photosynthesis, Water cycle, etc.)
- Current events discussion
- Story telling
- Explain a concept
- Debate practice
```

#### 3. **Presentation Practice**
```
AI: "Imagine you're presenting about the solar system. Begin!"
Student: [Gives 2-minute presentation]
AI: "Good start! Let me ask you a question about Mars..."
```

#### 4. **Interview Simulation**
```
AI: "I'll interview you for a school project. Ready?"
Student: "Yes!"
AI: "Tell me about yourself..."
```

---

## 📊 Analytics Dashboard (After Session)

### Comprehensive Feedback Report:

```
┌─────────────────────────────────────────────────────────┐
│         📊 Speaking Practice Report                      │
│                                                          │
│  Session Details:                                        │
│  🕐 Duration: 10 minutes 30 seconds                      │
│  💬 Total Exchanges: 24                                  │
│  📝 Words Spoken: 450                                    │
│  🎯 Topic: Science Concepts                              │
│                                                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  OVERALL SCORE: 78/100 ⭐⭐⭐⭐                          │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Grammar & Accuracy        85/100 ████████░░    │   │
│  │  Fluency                   75/100 ███████░░░    │   │
│  │  Vocabulary                72/100 ███████░░░    │   │
│  │  Pronunciation             80/100 ████████░░    │   │
│  │  Coherence                 76/100 ███████░░░    │   │
│  │  Confidence                82/100 ████████░░    │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
├─────────────────────────────────────────────────────────┤
│  📈 STRENGTHS                                            │
│  ✅ Clear pronunciation of technical terms               │
│  ✅ Good use of scientific vocabulary                    │
│  ✅ Confident speaking pace                              │
│  ✅ Logical flow of ideas                                │
│                                                          │
├─────────────────────────────────────────────────────────┤
│  ⚠️  AREAS FOR IMPROVEMENT                               │
│  🔸 Grammar Issues Found: 8                              │
│     • "was went" → "went" (3 times)                     │
│     • "don't knows" → "don't know" (2 times)            │
│     • Missing articles (3 times)                         │
│                                                          │
│  🔸 Filler Words: 15 times                               │
│     • "um" (8 times)                                     │
│     • "like" (7 times)                                   │
│                                                          │
│  🔸 Speaking Pace: Sometimes too fast                    │
│     Average: 180 words/min (ideal: 130-150)             │
│                                                          │
├─────────────────────────────────────────────────────────┤
│  💡 PERSONALIZED SUGGESTIONS                             │
│                                                          │
│  1. Practice Past Tense:                                 │
│     ❌ "I was went to school"                           │
│     ✅ "I went to school"                               │
│                                                          │
│  2. Reduce Filler Words:                                 │
│     • Pause briefly instead of saying "um"              │
│     • Practice with timer to build confidence           │
│                                                          │
│  3. Slow Down:                                           │
│     • Take breaths between sentences                    │
│     • Emphasize key words                               │
│                                                          │
│  4. Vocabulary Enhancement:                              │
│     Try using these words next time:                    │
│     • "Furthermore" instead of "and also"               │
│     • "Consequently" instead of "so"                    │
│     • "Essential" instead of "very important"           │
│                                                          │
├─────────────────────────────────────────────────────────┤
│  📝 CONVERSATION HIGHLIGHTS                              │
│                                                          │
│  Best Exchange:                                          │
│  You: "Photosynthesis is essential for life because    │
│       plants produce oxygen which animals need."        │
│  ✅ Perfect grammar, clear explanation!                 │
│                                                          │
│  Needs Work:                                             │
│  You: "The plants was making the food from sunlight."  │
│  ❌ Should be: "The plants were making..."             │
│                                                          │
├─────────────────────────────────────────────────────────┤
│  🎯 PRACTICE GOALS FOR NEXT SESSION                      │
│                                                          │
│  [ ] Use correct past tense 10 times                    │
│  [ ] Reduce filler words by 50%                         │
│  [ ] Speak at 130-150 words per minute                  │
│  [ ] Use 3 advanced vocabulary words                    │
│                                                          │
├─────────────────────────────────────────────────────────┤
│  📊 PROGRESS TRACKING                                    │
│                                                          │
│      Session 1    Session 2    Session 3 (Today)        │
│  Overall: 65/100 → 72/100 → 78/100 ↗️ +13 points!     │
│                                                          │
│  [View Detailed Analytics]  [Share Report]  [Practice]  │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technical Implementation

### Backend: New Endpoint for Analysis

```python
# students/views.py

@login_required
def speaking_practice_room(request):
    """Speaking practice page - like Zoom meeting room"""
    return render(request, 'students/speaking_practice.html')

@login_required
@require_POST
def analyze_speaking_session(request):
    """
    Analyze complete speaking session
    Returns grammar, fluency, vocabulary scores
    """
    data = json.loads(request.body)
    conversation_history = data.get('conversation', [])
    duration = data.get('duration', 0)
    
    # Combine all student utterances
    student_text = "\n".join([
        turn['text'] for turn in conversation_history 
        if turn['speaker'] == 'student'
    ])
    
    # Analyze with OpenAI/Gemini
    analysis = analyze_with_ai(student_text, duration, conversation_history)
    
    # Save to database
    SpeakingSession.objects.create(
        student=request.user,
        conversation_data=conversation_history,
        duration=duration,
        grammar_score=analysis['grammar_score'],
        fluency_score=analysis['fluency_score'],
        # ... more scores
    )
    
    return JsonResponse(analysis)

def analyze_with_ai(text, duration, conversation):
    """Use AI to analyze speaking quality"""
    
    prompt = f"""
    Analyze this student's speaking practice:
    
    Duration: {duration} seconds
    Total words: {len(text.split())}
    
    Student's Speech:
    {text}
    
    Full Conversation:
    {json.dumps(conversation, indent=2)}
    
    Provide detailed analysis in JSON format:
    {{
        "overall_score": 0-100,
        "grammar_score": 0-100,
        "fluency_score": 0-100,
        "vocabulary_score": 0-100,
        "pronunciation_score": 0-100,
        "coherence_score": 0-100,
        "confidence_score": 0-100,
        
        "grammar_errors": [
            {{"error": "was went", "correction": "went", "count": 3}},
            ...
        ],
        
        "filler_words": [
            {{"word": "um", "count": 8}},
            {{"word": "like", "count": 7}}
        ],
        
        "speaking_pace": {{
            "words_per_minute": 180,
            "ideal_range": "130-150",
            "feedback": "Too fast - try to slow down"
        }},
        
        "strengths": [
            "Clear pronunciation",
            "Good vocabulary",
            ...
        ],
        
        "improvements": [
            "Practice past tense",
            "Reduce filler words",
            ...
        ],
        
        "suggestions": [
            {{
                "issue": "Past tense errors",
                "examples": [
                    {{"wrong": "was went", "correct": "went"}}
                ],
                "tip": "Remember: use simple past, not 'was + past'"
            }},
            ...
        ],
        
        "vocabulary_enhancement": [
            {{"basic": "very important", "advanced": "essential"}},
            {{"basic": "and also", "advanced": "furthermore"}},
            ...
        ],
        
        "best_exchanges": [
            {{
                "text": "...",
                "reason": "Perfect grammar and clarity"
            }}
        ],
        
        "needs_work": [
            {{
                "text": "...",
                "issue": "Subject-verb agreement"
            }}
        ]
    }}
    """
    
    # Call OpenAI/Gemini
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert English language tutor."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)
```

### Frontend: Speaking Practice Room

```javascript
// templates/students/speaking_practice.html

function speakingPractice() {
    return {
        // Session state
        sessionActive: false,
        isPaused: false,
        micOn: false,
        
        // Conversation tracking
        conversation: [],
        currentTurn: 'ai', // 'ai' or 'student'
        
        // Real-time transcription
        studentTranscript: '',
        aiTranscript: '',
        
        // Session stats
        startTime: null,
        duration: 0,
        exchangeCount: 0,
        wordCount: 0,
        
        // Voice APIs
        recognition: null,
        synthesis: window.speechSynthesis,
        
        // UI state
        isListening: false,
        isSpeaking: false,
        showAnalytics: false,
        analysisData: null,
        
        // Session settings
        practiceType: 'free', // 'free', 'topic', 'presentation', 'interview'
        selectedTopic: null,
        
        // Start session
        startSession() {
            this.sessionActive = true;
            this.startTime = Date.now();
            this.conversation = [];
            this.exchangeCount = 0;
            this.wordCount = 0;
            
            // AI starts conversation
            this.aiSpeak("Hello! I'm your speaking practice tutor. What would you like to talk about today?");
            
            // Start timer
            this.startTimer();
        },
        
        // Student speaks
        studentSpeak() {
            if (!this.micOn) return;
            
            this.currentTurn = 'student';
            this.isListening = true;
            
            // Start speech recognition
            this.recognition.start();
        },
        
        // Handle student's speech result
        onStudentSpeechEnd(transcript) {
            this.isListening = false;
            
            // Save to conversation
            this.conversation.push({
                speaker: 'student',
                text: transcript,
                timestamp: Date.now() - this.startTime
            });
            
            this.studentTranscript = transcript;
            this.wordCount += transcript.split(' ').length;
            this.exchangeCount++;
            
            // AI responds
            this.getAIResponse(transcript);
        },
        
        // AI responds
        async getAIResponse(studentText) {
            this.currentTurn = 'ai';
            
            // Call backend for AI response
            const response = await fetch('/students/speaking-practice/respond/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    student_message: studentText,
                    conversation_history: this.conversation,
                    practice_type: this.practiceType
                })
            });
            
            const data = await response.json();
            const aiResponse = data.response;
            
            // Save AI response
            this.conversation.push({
                speaker: 'ai',
                text: aiResponse,
                timestamp: Date.now() - this.startTime
            });
            
            // Speak AI response
            this.aiSpeak(aiResponse);
        },
        
        // AI speaks
        aiSpeak(text) {
            this.isSpeaking = true;
            this.aiTranscript = text;
            
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'en-IN';
            utterance.rate = 0.9;
            
            utterance.onend = () => {
                this.isSpeaking = false;
                this.currentTurn = 'student';
                // Prompt student to speak
            };
            
            this.synthesis.speak(utterance);
        },
        
        // End session and get analytics
        async endSession() {
            this.sessionActive = false;
            this.duration = Math.floor((Date.now() - this.startTime) / 1000);
            
            // Stop any ongoing speech
            this.synthesis.cancel();
            if (this.recognition) this.recognition.stop();
            
            // Get analysis
            this.showAnalytics = true;
            await this.getAnalytics();
        },
        
        // Get detailed analytics
        async getAnalytics() {
            const response = await fetch('/students/speaking-practice/analyze/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    conversation: this.conversation,
                    duration: this.duration,
                    practice_type: this.practiceType
                })
            });
            
            this.analysisData = await response.json();
        }
    };
}
```

---

## 📊 Database Models

```python
# students/models.py

class SpeakingSession(models.Model):
    """Track speaking practice sessions"""
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    
    # Session details
    practice_type = models.CharField(max_length=50)  # free, topic, presentation
    topic = models.CharField(max_length=200, null=True, blank=True)
    duration = models.IntegerField()  # seconds
    exchange_count = models.IntegerField()
    word_count = models.IntegerField()
    
    # Conversation data
    conversation_data = models.JSONField()  # Full conversation history
    
    # Scores
    overall_score = models.IntegerField()  # 0-100
    grammar_score = models.IntegerField()
    fluency_score = models.IntegerField()
    vocabulary_score = models.IntegerField()
    pronunciation_score = models.IntegerField()
    coherence_score = models.IntegerField()
    confidence_score = models.IntegerField()
    
    # Analysis
    grammar_errors = models.JSONField()  # List of errors
    filler_words = models.JSONField()  # Counts
    speaking_pace = models.JSONField()  # Words per minute
    strengths = models.JSONField()  # List
    improvements = models.JSONField()  # List
    suggestions = models.JSONField()  # Detailed tips
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.email} - {self.practice_type} - {self.overall_score}/100"
```

---

## 🎯 Features Summary

### Real-Time During Session:
✅ Live voice conversation with AI  
✅ Real-time transcription display  
✅ Turn-taking (student → AI → student)  
✅ Session timer  
✅ Exchange counter  
✅ Pause/Resume capability  

### Analytics After Session:
✅ Overall score (0-100)  
✅ 6 detailed scores (grammar, fluency, vocabulary, etc.)  
✅ Grammar error detection with corrections  
✅ Filler word counting  
✅ Speaking pace analysis  
✅ Strengths identification  
✅ Improvement suggestions  
✅ Vocabulary enhancement tips  
✅ Best/worst exchange highlights  
✅ Progress tracking across sessions  

---

## 🚀 Implementation Plan

### Phase 1: Basic Speaking Room (Week 1)
- [ ] Create speaking_practice.html page
- [ ] Implement voice turn-taking
- [ ] Add session timer
- [ ] Basic AI conversation

### Phase 2: Advanced Features (Week 2)
- [ ] Add practice type selection
- [ ] Topic-based conversations
- [ ] Real-time transcription display
- [ ] Sound wave animations

### Phase 3: Analytics (Week 3)
- [ ] Implement AI analysis endpoint
- [ ] Create analytics dashboard
- [ ] Grammar error detection
- [ ] Progress tracking

### Phase 4: Polish (Week 4)
- [ ] Visual improvements
- [ ] Charts and graphs
- [ ] Export report feature
- [ ] Mobile optimization

---

**Ready to implement this feature!** 🎤📊
