import { useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';

/**
 * AvatarUsername Step (Step 3)
 * 
 * OPTIONAL step - customize DiceBear avatar and username.
 * If skipped, system assigns default avatar + username.
 * 
 * TODO: Backend Integration
 * - POST /api/onboarding/avatar
 * - Check username availability
 * - Store avatar configuration
 */

const AVATAR_STYLES = [
  { id: 'avataaars', name: 'Avatars' },
  { id: 'bottts', name: 'Robots' },
  { id: 'lorelei', name: 'Lorelei' },
  { id: 'micah', name: 'Micah' },
  { id: 'notionists', name: 'Notion' }
];

function AvatarUsername({ data, onNext, onSkip }) {
  const [avatarSeed, setAvatarSeed] = useState(data.seed || Date.now().toString());
  const [avatarStyle, setAvatarStyle] = useState(data.style || 'avataaars');
  const [username, setUsername] = useState(data.username || '');
  const [error, setError] = useState('');

  const getAvatarUrl = (style, seed) => {
    return `https://api.dicebear.com/7.x/${style}/svg?seed=${seed}`;
  };

  const regenerateAvatar = () => {
    setAvatarSeed(Date.now().toString());
  };

  const handleNext = () => {
    // Username validation (optional)
    if (username && username.length < 3) {
      setError('Username must be at least 3 characters');
      return;
    }

    if (username && !/^[a-zA-Z0-9_]+$/.test(username)) {
      setError('Username can only contain letters, numbers, and underscores');
      return;
    }

    /**
     * TODO: Backend Integration
     * - Check username availability
     * await fetch('/api/onboarding/avatar', {
     *   method: 'POST',
     *   body: JSON.stringify({ avatarSeed, avatarStyle, username })
     * });
     */

    onNext({ seed: avatarSeed, style: avatarStyle, username });
  };

  return (
    <div className="max-w-md mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-foreground mb-2">
          Customize your avatar
        </h2>
        <p className="text-muted-foreground">
          Create your unique identity in the app
        </p>
      </div>

      {/* Avatar Preview */}
      <div className="flex justify-center mb-8">
        <div className="relative">
          <img
            src={getAvatarUrl(avatarStyle, avatarSeed)}
            alt="Avatar"
            className="w-32 h-32 rounded-full bg-secondary"
          />
          <button
            type="button"
            onClick={regenerateAvatar}
            className="absolute -bottom-2 -right-2 w-10 h-10 bg-foreground text-background rounded-full flex items-center justify-center hover:bg-foreground/80 transition-colors"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Style Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-foreground mb-3">
          Choose a style
        </label>
        <div className="grid grid-cols-5 gap-2">
          {AVATAR_STYLES.map((style) => (
            <button
              key={style.id}
              type="button"
              onClick={() => setAvatarStyle(style.id)}
              className={`flex flex-col items-center p-2 rounded-lg border-2 transition-colors ${
                avatarStyle === style.id
                  ? 'border-foreground bg-secondary'
                  : 'border-border hover:border-foreground/50'
              }`}
            >
              <img
                src={getAvatarUrl(style.id, avatarSeed)}
                alt={style.name}
                className="w-10 h-10 mb-1"
              />
              <span className="text-xs text-muted-foreground">{style.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Username Input */}
      <div className="mb-8">
        <label className="block text-sm font-medium text-foreground mb-2">
          Choose a username (optional)
        </label>
        <Input
          type="text"
          value={username}
          onChange={(e) => {
            setUsername(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ''));
            setError('');
          }}
          placeholder="your_username"
          className="h-12"
        />
        <p className="text-xs text-muted-foreground mt-2">
          Letters, numbers, and underscores only
        </p>
      </div>

      {error && (
        <p className="text-destructive text-sm mb-4">{error}</p>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3">
        <Button
          variant="outline"
          onClick={onSkip}
          className="flex-1 h-12"
        >
          Skip
        </Button>
        <Button
          onClick={handleNext}
          className="flex-1 h-12"
        >
          Save & Continue
        </Button>
      </div>
    </div>
  );
}

export default AvatarUsername;
