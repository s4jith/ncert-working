import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import BasicProfile from './BasicProfile';
import PreviousAcademics from './PreviousAcademics';
import AvatarUsername from './AvatarUsername';
import ExamCalendar from './ExamCalendar';
import useUserStore from '../../stores/userStore';

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * OnboardingLayout Component
 * 
 * Wrapper component that handles the 4-step onboarding flow.
 * 
 * Step 1: Basic Profile (MANDATORY) - name, class
 * Step 2: Previous Academics (OPTIONAL) - subjects, marks
 * Step 3: Avatar & Username (OPTIONAL) - DiceBear avatar customization
 * Step 4: Exam Calendar (OPTIONAL) - add exam dates
 */

const STEPS = [
  { id: 1, title: 'Basic Profile', required: true },
  { id: 2, title: 'Previous Academics', required: false },
  { id: 3, title: 'Avatar & Username', required: false },
  { id: 4, title: 'Exam Calendar', required: false }
];

function OnboardingLayout() {
  const navigate = useNavigate();
  const { user, setUser } = useUserStore();
  const [currentStep, setCurrentStep] = useState(1);
  const [onboardingData, setOnboardingData] = useState({
    profile: {
      name: user.name || '',
      classLevel: user.classLevel || 6
    },
    academics: {
      subjects: []
    },
    avatar: {
      seed: user.avatarSeed || Date.now().toString(),
      style: user.avatarStyle || 'avataaars',
      username: ''
    },
    calendar: {
      exams: []
    }
  });

  const handleNext = (stepData) => {
    // Update onboarding data based on current step
    switch (currentStep) {
      case 1:
        setOnboardingData(prev => ({ ...prev, profile: stepData }));
        break;
      case 2:
        setOnboardingData(prev => ({ ...prev, academics: stepData }));
        break;
      case 3:
        setOnboardingData(prev => ({ ...prev, avatar: stepData }));
        break;
      case 4:
        setOnboardingData(prev => ({ ...prev, calendar: stepData }));
        break;
    }

    if (currentStep < STEPS.length) {
      setCurrentStep(currentStep + 1);
    } else {
      // Complete onboarding
      completeOnboarding();
    }
  };

  const handleSkip = () => {
    if (currentStep < STEPS.length) {
      setCurrentStep(currentStep + 1);
    } else {
      completeOnboarding();
    }
  };

  const completeOnboarding = async () => {
    try {
      // Save onboarding data to backend
      const response = await fetch(`${API_BASE}/api/auth/complete-onboarding`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: user.user_id,
          profile: onboardingData.profile,
          academics: onboardingData.academics,
          avatar: onboardingData.avatar,
          calendar: onboardingData.calendar
        })
      });
      
      const data = await response.json();
      
      if (!data.success) {
        console.error("Failed to save onboarding:", data.error);
        // Still update locally and continue even if backend fails
      }
    } catch (error) {
      console.error("Onboarding save error:", error);
      // Continue even if backend fails
    }

    // Update user store with onboarding data
    setUser({
      ...user,
      name: onboardingData.profile.name,
      classLevel: onboardingData.profile.classLevel,
      username: onboardingData.avatar.username || `student_${Date.now()}`,
      avatarSeed: onboardingData.avatar.seed,
      avatarStyle: onboardingData.avatar.style,
      isOnboarded: true
    });

    navigate('/dashboard');
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <BasicProfile
            data={onboardingData.profile}
            onNext={handleNext}
          />
        );
      case 2:
        return (
          <PreviousAcademics
            data={onboardingData.academics}
            classLevel={onboardingData.profile.classLevel}
            onNext={handleNext}
            onSkip={handleSkip}
          />
        );
      case 3:
        return (
          <AvatarUsername
            data={onboardingData.avatar}
            onNext={handleNext}
            onSkip={handleSkip}
          />
        );
      case 4:
        return (
          <ExamCalendar
            data={onboardingData.calendar}
            onNext={handleNext}
            onSkip={handleSkip}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header with Progress */}
      <div className="border-b bg-card">
        <div className="max-w-3xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-xl font-semibold text-foreground">
              Let's get you set up
            </h1>
            <span className="text-sm text-muted-foreground">
              Step {currentStep} of {STEPS.length}
            </span>
          </div>

          {/* Progress Bar */}
          <div className="flex gap-2">
            {STEPS.map((step) => (
              <div
                key={step.id}
                className={`h-1.5 flex-1 rounded-full transition-colors ${
                  step.id <= currentStep
                    ? 'bg-foreground'
                    : 'bg-border'
                }`}
              />
            ))}
          </div>

          {/* Step indicator */}
          <div className="flex justify-between mt-2">
            {STEPS.map((step) => (
              <span
                key={step.id}
                className={`text-xs ${
                  step.id === currentStep
                    ? 'text-foreground font-medium'
                    : 'text-muted-foreground'
                }`}
              >
                {step.title}
                {!step.required && <span className="ml-1 opacity-50">(optional)</span>}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Step Content */}
      <div className="max-w-3xl mx-auto px-6 py-8">
        {renderStep()}
      </div>
    </div>
  );
}

export default OnboardingLayout;
