import { useState } from 'react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import classesData from '../../data/classes.json';

/**
 * BasicProfile Step (Step 1)
 * 
 * MANDATORY step - collects student name and class level.
 * 
 * TODO: Backend Integration
 * - Validate name against profanity filter
 * - Check if class exists in system
 * - POST /api/onboarding/profile
 */

function BasicProfile({ data, onNext }) {
  const [formData, setFormData] = useState({
    name: data.name || '',
    classLevel: data.classLevel || 6
  });
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      setError('Please enter your name');
      return;
    }

    if (formData.name.trim().length < 2) {
      setError('Name must be at least 2 characters');
      return;
    }

    /**
     * TODO: Backend Integration
     * await fetch('/api/onboarding/profile', {
     *   method: 'POST',
     *   body: JSON.stringify(formData)
     * });
     */

    onNext(formData);
  };

  return (
    <div className="max-w-md mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-foreground mb-2">
          Tell us about yourself
        </h2>
        <p className="text-muted-foreground">
          This helps us personalize your learning experience
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            What's your name?
          </label>
          <Input
            type="text"
            value={formData.name}
            onChange={(e) => {
              setFormData({ ...formData, name: e.target.value });
              setError('');
            }}
            placeholder="Enter your name"
            className="h-12"
            autoFocus
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Which class are you in?
          </label>
          <div className="grid grid-cols-4 gap-2">
            {classesData.classes.map((cls) => (
              <button
                key={cls.level}
                type="button"
                onClick={() => setFormData({ ...formData, classLevel: cls.level })}
                className={`p-3 rounded-lg border-2 text-center transition-colors ${
                  formData.classLevel === cls.level
                    ? 'border-foreground bg-foreground text-background'
                    : 'border-border hover:border-foreground/50'
                }`}
              >
                <span className="font-medium">{cls.level}</span>
              </button>
            ))}
          </div>
        </div>

        {error && (
          <p className="text-destructive text-sm">{error}</p>
        )}

        <Button
          type="submit"
          className="w-full h-12 text-base font-medium"
        >
          Next
        </Button>
      </form>
    </div>
  );
}

export default BasicProfile;
