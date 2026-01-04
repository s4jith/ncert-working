import { useRef, useState, useEffect } from 'react';

/**
 * AnimatedGridBackground Component
 * 
 * Pure CSS animated scrolling grid with mouse-reveal effect.
 * No external animation library dependencies.
 */

export default function InfiniteGridBackground({ children, className = "" }) {
    const containerRef = useRef(null);
    const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

    const handleMouseMove = (e) => {
        if (!containerRef.current) return;
        const { left, top } = containerRef.current.getBoundingClientRect();
        setMousePosition({
            x: e.clientX - left,
            y: e.clientY - top
        });
    };

    return (
        <div
            ref={containerRef}
            onMouseMove={handleMouseMove}
            className={`relative overflow-hidden ${className}`}
            style={{ background: '#fafafa' }}
        >
            {/* Animated Grid Layer 1 - Subtle always visible */}
            <div
                className="absolute inset-0 z-0 opacity-[0.04] animate-grid-scroll"
                style={{
                    backgroundImage: `
            linear-gradient(to right, #9ca3af 1px, transparent 1px),
            linear-gradient(to bottom, #9ca3af 1px, transparent 1px)
          `,
                    backgroundSize: '50px 50px'
                }}
            />

            {/* Animated Grid Layer 2 - Mouse reveal */}
            <div
                className="absolute inset-0 z-0 opacity-30 animate-grid-scroll"
                style={{
                    backgroundImage: `
            linear-gradient(to right, #d1d5db 1px, transparent 1px),
            linear-gradient(to bottom, #d1d5db 1px, transparent 1px)
          `,
                    backgroundSize: '50px 50px',
                    maskImage: `radial-gradient(400px circle at ${mousePosition.x}px ${mousePosition.y}px, black 0%, transparent 70%)`,
                    WebkitMaskImage: `radial-gradient(400px circle at ${mousePosition.x}px ${mousePosition.y}px, black 0%, transparent 70%)`
                }}
            />

            {/* Decorative gradient orbs */}
            <div className="absolute inset-0 pointer-events-none z-0">
                <div
                    className="absolute rounded-full blur-[100px] animate-pulse-slow"
                    style={{
                        right: '-10%',
                        top: '-15%',
                        width: '35%',
                        height: '35%',
                        background: 'rgba(255, 166, 128, 0.15)'
                    }}
                />
                <div
                    className="absolute rounded-full blur-[80px] animate-pulse-slow"
                    style={{
                        left: '-10%',
                        bottom: '-10%',
                        width: '30%',
                        height: '30%',
                        background: 'rgba(147, 197, 253, 0.15)',
                        animationDelay: '1s'
                    }}
                />
                <div
                    className="absolute rounded-full blur-[60px] animate-pulse-slow"
                    style={{
                        right: '20%',
                        bottom: '10%',
                        width: '20%',
                        height: '20%',
                        background: 'rgba(252, 211, 77, 0.1)',
                        animationDelay: '2s'
                    }}
                />
            </div>

            {/* Content */}
            <div className="relative z-10 h-full">
                {children}
            </div>

            {/* CSS Animations */}
            <style>{`
        @keyframes grid-scroll {
          0% {
            background-position: 0 0;
          }
          100% {
            background-position: 50px 50px;
          }
        }
        
        @keyframes pulse-slow {
          0%, 100% {
            opacity: 0.5;
            transform: scale(1);
          }
          50% {
            opacity: 0.8;
            transform: scale(1.05);
          }
        }
        
        .animate-grid-scroll {
          animation: grid-scroll 8s linear infinite;
        }
        
        .animate-pulse-slow {
          animation: pulse-slow 6s ease-in-out infinite;
        }
      `}</style>
        </div>
    );
}
