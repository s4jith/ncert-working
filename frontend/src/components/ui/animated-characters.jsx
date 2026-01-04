import { useState, useEffect, useRef } from "react";
import { Slack } from "lucide-react";
export const Pupil = ({ 
  size = 12, 
  maxDistance = 5,
  pupilColor = "black",
  forceLookX,
  forceLookY
}) => {
  const [mouseX, setMouseX] = useState(0);
  const [mouseY, setMouseY] = useState(0);
  const pupilRef = useRef(null);

  useEffect(() => {
    const handleMouseMove = (e) => {
      setMouseX(e.clientX);
      setMouseY(e.clientY);
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  const calculatePupilPosition = () => {
    if (!pupilRef.current) return { x: 0, y: 0 };

    if (forceLookX !== undefined && forceLookY !== undefined) {
      return { x: forceLookX, y: forceLookY };
    }

    const pupil = pupilRef.current.getBoundingClientRect();
    const pupilCenterX = pupil.left + pupil.width / 2;
    const pupilCenterY = pupil.top + pupil.height / 2;

    const deltaX = mouseX - pupilCenterX;
    const deltaY = mouseY - pupilCenterY;
    const distance = Math.min(Math.sqrt(deltaX ** 2 + deltaY ** 2), maxDistance);

    const angle = Math.atan2(deltaY, deltaX);
    const x = Math.cos(angle) * distance;
    const y = Math.sin(angle) * distance;

    return { x, y };
  };

  const pupilPosition = calculatePupilPosition();

  return (
    <div
      ref={pupilRef}
      className="rounded-full"
      style={{
        width: `${size}px`,
        height: `${size}px`,
        backgroundColor: pupilColor,
        transform: `translate(${pupilPosition.x}px, ${pupilPosition.y}px)`,
        transition: 'transform 0.1s ease-out',
      }}
    />
  );
};

/**
 * EyeBall Component - Eye with pupil that tracks mouse position
 */
export const EyeBall = ({ 
  size = 58, 
  pupilSize = 16, 
  maxDistance = 10,
  eyeColor = "white",
  pupilColor = "black",
  isBlinking = false,
  forceLookX,
  forceLookY
}) => {
  const [mouseX, setMouseX] = useState(0);
  const [mouseY, setMouseY] = useState(0);
  const eyeRef = useRef(null);

  useEffect(() => {
    const handleMouseMove = (e) => {
      setMouseX(e.clientX);
      setMouseY(e.clientY);
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  const calculatePupilPosition = () => {
    if (!eyeRef.current) return { x: 0, y: 0 };

    if (forceLookX !== undefined && forceLookY !== undefined) {
      return { x: forceLookX, y: forceLookY };
    }

    const eye = eyeRef.current.getBoundingClientRect();
    const eyeCenterX = eye.left + eye.width / 2;
    const eyeCenterY = eye.top + eye.height / 2;

    const deltaX = mouseX - eyeCenterX;
    const deltaY = mouseY - eyeCenterY;
    const distance = Math.min(Math.sqrt(deltaX ** 2 + deltaY ** 2), maxDistance);

    const angle = Math.atan2(deltaY, deltaX);
    const x = Math.cos(angle) * distance;
    const y = Math.sin(angle) * distance;

    return { x, y };
  };

  const pupilPosition = calculatePupilPosition();

  return (
    <div
      ref={eyeRef}
      className="rounded-full flex items-center justify-center transition-all duration-150"
      style={{
        width: `${size}px`,
        height: isBlinking ? '2px' : `${size}px`,
        backgroundColor: eyeColor,
        overflow: 'hidden',
      }}
    >
      {!isBlinking && (
        <div
          className="rounded-full"
          style={{
            width: `${pupilSize}px`,
            height: `${pupilSize}px`,
            backgroundColor: pupilColor,
            transform: `translate(${pupilPosition.x}px, ${pupilPosition.y}px)`,
            transition: 'transform 0.1s ease-out',
          }}
        />
      )}
    </div>
  );
};

/**
 * AnimatedCharacters Component
 * 
 * Displays 6 animated characters that follow mouse movement
 * and react to password visibility state.
 */
export function AnimatedCharacters({ password = "", showPassword = false, isTyping = false }) {
  const [mouseX, setMouseX] = useState(0);
  const [mouseY, setMouseY] = useState(0);
  const [isPurpleBlinking, setIsPurpleBlinking] = useState(false);
  const [isBlackBlinking, setIsBlackBlinking] = useState(false);
  const [isLookingAtEachOther, setIsLookingAtEachOther] = useState(false);
  const [isPurplePeeking, setIsPurplePeeking] = useState(false);
  
  const pinkRef= useRef(null)
  const purpleRef = useRef(null);
  const blackRef = useRef(null);
  const yellowRef = useRef(null);
  const orangeRef = useRef(null);
  const redRef = useRef(null);
  const blueRef = useRef(null);

  useEffect(() => {
    const handleMouseMove = (e) => {
      setMouseX(e.clientX);
      setMouseY(e.clientY);
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  // Purple character blinking
  useEffect(() => {
    const getRandomBlinkInterval = () => Math.random() * 4000 + 3000;

    const scheduleBlink = () => {
      const blinkTimeout = setTimeout(() => {
        setIsPurpleBlinking(true);
        setTimeout(() => {
          setIsPurpleBlinking(false);
          scheduleBlink();
        }, 150);
      }, getRandomBlinkInterval());

      return blinkTimeout;
    };

    const timeout = scheduleBlink();
    return () => clearTimeout(timeout);
  }, []);

  // Black character blinking
  useEffect(() => {
    const getRandomBlinkInterval = () => Math.random() * 4000 + 3000;

    const scheduleBlink = () => {
      const blinkTimeout = setTimeout(() => {
        setIsBlackBlinking(true);
        setTimeout(() => {
          setIsBlackBlinking(false);
          scheduleBlink();
        }, 150);
      }, getRandomBlinkInterval());

      return blinkTimeout;
    };

    const timeout = scheduleBlink();
    return () => clearTimeout(timeout);
  }, []);

  // Look at each other when typing starts
  useEffect(() => {
    if (isTyping) {
      setIsLookingAtEachOther(true);
      const timer = setTimeout(() => {
        setIsLookingAtEachOther(false);
      }, 800);
      return () => clearTimeout(timer);
    } else {
      setIsLookingAtEachOther(false);
    }
  }, [isTyping]);

  // Purple sneaky peeking when password visible
  useEffect(() => {
    if (password.length > 0 && showPassword) {
      const schedulePeek = () => {
        const peekInterval = setTimeout(() => {
          setIsPurplePeeking(true);
          setTimeout(() => {
            setIsPurplePeeking(false);
          }, 800);
        }, Math.random() * 3000 + 2000);
        return peekInterval;
      };

      const firstPeek = schedulePeek();
      return () => clearTimeout(firstPeek);
    } else {
      setIsPurplePeeking(false);
    }
  }, [password, showPassword, isPurplePeeking]);

  const calculatePosition = (ref) => {
    if (!ref.current) return { faceX: 0, faceY: 0, bodySkew: 0 };

    const rect = ref.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 3;

    const deltaX = mouseX - centerX;
    const deltaY = mouseY - centerY;

    const faceX = Math.max(-15, Math.min(15, deltaX / 20));
    const faceY = Math.max(-10, Math.min(10, deltaY / 30));
    const bodySkew = Math.max(-6, Math.min(6, -deltaX / 120));

    return { faceX, faceY, bodySkew };
  };
  const pinkPos=calculatePosition(pinkRef)
  const purplePos = calculatePosition(purpleRef);
  const blackPos = calculatePosition(blackRef);
  const yellowPos = calculatePosition(yellowRef);
  const orangePos = calculatePosition(orangeRef);
  const redPos = calculatePosition(redRef);
  const bluePos = calculatePosition(blueRef);

  const hideEyes = password.length > 0 && !showPassword;

  return (
    <div className="relative flex items-end justify-center" style={{ width: '600px', height: '450px' }}>
      {/* Pink tall character - Back layer */}
      <div 
        ref={purpleRef}
        className="absolute bottom-0 transition-all duration-700 ease-in-out"
        style={{
          left: '30px',
          width: '160px',
          height: (isTyping || hideEyes) ? '380px' : '420px',
          backgroundColor: '#f928a9ff',
          borderRadius: '10px 10px 0 0',
          zIndex: 1,
          transform: (password.length > 0 && showPassword)
            ? `skewX(0deg)`
            : (isTyping || hideEyes)
              ? `skewX(${(purplePos.bodySkew || 0) - 12}deg) translateX(40px)` 
              : `skewX(${purplePos.bodySkew || 0}deg)`,
          transformOrigin: 'bottom center',
        }}
      >
        <div 
          className="absolute flex gap-6 transition-all duration-700 ease-in-out"
          style={{
            left: (password.length > 0 && showPassword) ? `${15}px` : isLookingAtEachOther ? `${45}px` : `${38 + purplePos.faceX}px`,
            top: (password.length > 0 && showPassword) ? `${30}px` : isLookingAtEachOther ? `${55}px` : `${35 + purplePos.faceY}px`,
          }}
        >
          <EyeBall 
            size={16} 
            pupilSize={6} 
            maxDistance={4} 
            eyeColor="white" 
            pupilColor="#000000ff" 
            isBlinking={isPurpleBlinking}
            forceLookX={(password.length > 0 && showPassword) ? (isPurplePeeking ? 4 : -4) : isLookingAtEachOther ? 3 : undefined}
            forceLookY={(password.length > 0 && showPassword) ? (isPurplePeeking ? 5 : -4) : isLookingAtEachOther ? 4 : undefined}
          />
          <EyeBall 
            size={16} 
            pupilSize={6} 
            maxDistance={4} 
            eyeColor="white" 
            pupilColor="#4C1D95" 
            isBlinking={isPurpleBlinking}
            forceLookX={(password.length > 0 && showPassword) ? (isPurplePeeking ? 4 : -4) : isLookingAtEachOther ? 3 : undefined}
            forceLookY={(password.length > 0 && showPassword) ? (isPurplePeeking ? 5 : -4) : isLookingAtEachOther ? 4 : undefined}
          />
        </div>
      </div>
      <div 
        ref={pinkRef}
        className="absolute bottom-0 transition-all duration-700 ease-in-out"
        style={{
          left: '350px',
          width: '160px',
          height: (isTyping || hideEyes) ? '500px' : '520px',
          backgroundColor: '#ff8400ff',
          borderRadius: '10px 10px 0 0',
          zIndex: 1,
          transform: (password.length > 0 && showPassword)
            ? `skewX(0deg)`
            : (isTyping || hideEyes)
              ? `skewX(${(pinkPos.bodySkew || 0) +12}deg) translateX(-180px)` 
              : `skewX(${pinkPos.bodySkew || 0}deg)`,
          transformOrigin: 'bottom center',
        }}
      >
        <div 
          className="absolute flex gap-6 transition-all duration-700 ease-in-out"
          style={{
            left: (password.length > 0 && showPassword) ? `${15}px` : isLookingAtEachOther ? `${45}px` : `${38 + pinkPos.faceX}px`,
            top: (password.length > 0 && showPassword) ? `${30}px` : isLookingAtEachOther ? `${55}px` : `${35 + pinkPos.faceY}px`,
          }}
        >
          <EyeBall 
            size={16} 
            pupilSize={6} 
            maxDistance={4} 
            eyeColor="white" 
            pupilColor="#000000ff" 
            isBlinking={isPurpleBlinking}
            forceLookX={(password.length > 0 && showPassword) ? (isPurplePeeking ? 4 : -4) : isLookingAtEachOther ? 3 : undefined}
            forceLookY={(password.length > 0 && showPassword) ? (isPurplePeeking ? 5 : -4) : isLookingAtEachOther ? 4 : undefined}
          />
          <EyeBall 
            size={16} 
            pupilSize={6} 
            maxDistance={4} 
            eyeColor="white" 
            pupilColor="#4C1D95" 
            isBlinking={isPurpleBlinking}
            forceLookX={(password.length > 0 && showPassword) ? (isPurplePeeking ? 4 : -4) : isLookingAtEachOther ? 3 : undefined}
            forceLookY={(password.length > 0 && showPassword) ? (isPurplePeeking ? 5 : -4) : isLookingAtEachOther ? 4 : undefined}
          />
        </div>
      </div>
      {/* Yellow tall character - Middle layer */}
      <div 
        ref={blackRef}
        className="absolute bottom-0 transition-all duration-700 ease-in-out"
        style={{
          left: '170px',
          width: '160px',
          height: '380px',
          backgroundColor: '#ffc801ff',
          borderRadius: '16px 16px 0 0',
          zIndex: 2,
          transform: (password.length > 0 && showPassword)
            ? `skewX(0deg)`
            : isLookingAtEachOther
              ? `skewX(${(blackPos.bodySkew || 0) * 1.5 + 10}deg) translateX(20px)`
              : (isTyping || hideEyes)
                ? `skewX(${(blackPos.bodySkew || 0) * 1.5}deg)` 
                : `skewX(${blackPos.bodySkew || 0}deg)`,
          transformOrigin: 'bottom center',
        }}
      >
        <div 
          className="absolute flex gap-7 transition-all duration-700 ease-in-out"
          style={{
            left: (password.length > 0 && showPassword) ? `${10}px` : isLookingAtEachOther ? `${26}px` : `${22 + blackPos.faceX}px`,
            top: (password.length > 0 && showPassword) ? `${24}px` : isLookingAtEachOther ? `${10}px` : `${28 + blackPos.faceY}px`,
          }}
        >
          <EyeBall 
            size={14} 
            pupilSize={5} 
            maxDistance={5} 
            eyeColor="white" 
            pupilColor="#0F766E" 
            isBlinking={isBlackBlinking}
            forceLookX={(password.length > 0 && showPassword) ? -4 : isLookingAtEachOther ? 0 : undefined}
            forceLookY={(password.length > 0 && showPassword) ? -4 : isLookingAtEachOther ? -4 : undefined}
          />
          <EyeBall 
            size={14} 
            pupilSize={5} 
            maxDistance={5} 
            eyeColor="white" 
            pupilColor="#0F766E" 
            isBlinking={isBlackBlinking}
            forceLookX={(password.length > 0 && showPassword) ? -4 : isLookingAtEachOther ? 0 : undefined}
            forceLookY={(password.length > 0 && showPassword) ? -4 : isLookingAtEachOther ? -4 : undefined}
          />
        </div>
      </div>

      {/* Lime green semi-circle character - Front left */}
      <div 
        ref={orangeRef}
        className="absolute bottom-0 transition-all duration-700 ease-in-out"
        style={{
          left: '0px',
          width: '320px',
          height: '240px',
          zIndex: 3,
          backgroundColor: '#b4ff06ff',
          borderRadius: '300px 300px 0 0',
          transform: (password.length > 0 && showPassword) ? `skewX(0deg)` : `skewX(${orangePos.bodySkew || 0}deg)`,
          transformOrigin: 'bottom center',
        }}
      >
        <div 
          className="absolute flex gap-7 transition-all duration-200 ease-out"
          style={{
            left: (password.length > 0 && showPassword) ? `${45}px` : `${70 + (orangePos.faceX || 0)}px`,
            top: (password.length > 0 && showPassword) ? `${70}px` : `${75 + (orangePos.faceY || 0)}px`,
          }}
        >
          <Pupil size={10} maxDistance={4} pupilColor="#991B1B" forceLookX={(password.length > 0 && showPassword) ? -5 : undefined} forceLookY={(password.length > 0 && showPassword) ? -4 : undefined} />
          <Pupil size={10} maxDistance={4} pupilColor="#991B1B" forceLookX={(password.length > 0 && showPassword) ? -5 : undefined} forceLookY={(password.length > 0 && showPassword) ? -4 : undefined} />
        </div>
      </div>

      {/* Cyan tall rounded character - Front right */}
      <div 
        ref={yellowRef}
        className="absolute bottom-0 transition-all duration-700 ease-in-out"
        style={{
          left: '380px',
          width: '140px',
          height: '220px',
          backgroundColor: '#00d9ffff',
          borderRadius: '60px 60px 0 0',
          zIndex: 4,
          border: '2px solid #0bd2f5ff',
          transform: (password.length > 0 && showPassword) ? `skewX(0deg)` : `skewX(${yellowPos.bodySkew || 0}deg)`,
          transformOrigin: 'bottom center',
        }}
      >
        <div 
          className="absolute flex gap-5 transition-all duration-200 ease-out"
          style={{
            left: (password.length > 0 && showPassword) ? `${18}px` : `${44 + (yellowPos.faceX || 0)}px`,
            top: (password.length > 0 && showPassword) ? `${30}px` : `${35 + (yellowPos.faceY || 0)}px`,
          }}
        >
          <Pupil size={10} maxDistance={4} pupilColor="#78350F" forceLookX={(password.length > 0 && showPassword) ? -5 : undefined} forceLookY={(password.length > 0 && showPassword) ? -4 : undefined} />
          <Pupil size={10} maxDistance={4} pupilColor="#78350F" forceLookX={(password.length > 0 && showPassword) ? -5 : undefined} forceLookY={(password.length > 0 && showPassword) ? -4 : undefined} />
        </div>
        {/* Mouth line */}
        <div 
          className="absolute w-16 h-[3px] bg-[#78350F] rounded-full transition-all duration-200 ease-out"
          style={{
            left: (password.length > 0 && showPassword) ? `${10}px` : `${36 + (yellowPos.faceX || 0)}px`,
            top: (password.length > 0 && showPassword) ? `${75}px` : `${75 + (yellowPos.faceY || 0)}px`,
          }}
        />
      </div>

      {/* Red square character - New character 1 */}
      <div 
        ref={redRef}
        className="absolute bottom-0 transition-all duration-700 ease-in-out"
        style={{
          left: '280px',
          width: '130px',
          height: '240px',
          backgroundColor: '#ef4444',
          borderRadius: '12px 12px 0 0',
          zIndex: 3,
          transform: (password.length > 0 && showPassword) ? `skewX(0deg)` : `skewX(${redPos.bodySkew || 0}deg)`,
          transformOrigin: 'bottom center',
        }}
      >
        <div 
          className="absolute flex gap-4 transition-all duration-200 ease-out"
          style={{
            left: (password.length > 0 && showPassword) ? `${25}px` : `${30 + (redPos.faceX || 0)}px`,
            top: (password.length > 0 && showPassword) ? `${40}px` : `${45 + (redPos.faceY || 0)}px`,
          }}
        >
         <Pupil size={12} maxDistance={5} pupilColor="#fef3c7" forceLookX={(password.length > 0 && showPassword) ? -5 : undefined} forceLookY={(password.length > 0 && showPassword) ? -4 : undefined} />
          <Pupil size={12} maxDistance={5} pupilColor="#fef3c7" forceLookX={(password.length > 0 && showPassword) ? -5 : undefined} forceLookY={(password.length > 0 && showPassword) ? -4 : undefined} />
        </div>
      </div>

      {/* Blue wavy character - New character 2 */}
      
    </div>
  );
}

export default AnimatedCharacters;