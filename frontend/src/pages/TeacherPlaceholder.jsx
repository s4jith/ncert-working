import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Construction } from 'lucide-react';
import { Button } from '../components/ui/button';

/**
 * TeacherPlaceholder Page
 * 
 * Placeholder page for teacher role - "Yet to be designed"
 */

function TeacherPlaceholder() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      <div className="text-center max-w-md">
        <div className="w-24 h-24 mx-auto mb-8 rounded-full bg-secondary flex items-center justify-center">
          <Construction className="w-12 h-12 text-muted-foreground" />
        </div>
        
        <h1 className="text-3xl font-bold text-foreground mb-4">
          Yet to be designed
        </h1>
        
        <p className="text-muted-foreground mb-8">
          The teacher portal is currently under development. 
          Please check back soon for updates.
        </p>
        
        <Button
          onClick={() => navigate('/')}
          variant="outline"
          className="gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Go Back
        </Button>
      </div>
    </div>
  );
}

export default TeacherPlaceholder;
