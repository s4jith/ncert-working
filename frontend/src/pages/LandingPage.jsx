import React, { useRef, useState, useCallback, useEffect } from 'react';
import { motion, useScroll, useTransform, AnimatePresence, useMotionValue, useSpring } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
    BookOpen,
    Brain,
    Target,
    BarChart3,
    MessageCircle,
    Sparkles,
    ChevronRight,
    Zap,
    ArrowRight,
    HelpCircle,
    GraduationCap,
    Lightbulb,
    Award,
    Shield
} from 'lucide-react';

// Testimonial data
const testimonials = [
    {
        quote: "Brainwave transformed how I study. The AI-powered book assistant helps me understand complex concepts in seconds!",
        author: "Sahana",
        role: "Class 12 Student",
        avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Sahana&backgroundColor=b6e3f4",
    },
    {
        quote: "The personalized learning path keeps me motivated. I improved my scores by 40% in just two months!",
        author: "Karthiban",
        role: "Class 11 Student",
        avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Karthiban&backgroundColor=c0aede",
    },
    {
        quote: "Love how I can chat with any textbook. It's like having a personal tutor available 24/7!",
        author: "Kavin",
        role: "Class 10 Student",
        avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Kavin&backgroundColor=d1d4f9",
    },
    {
        quote: "The test analytics helped me identify my weak areas. Now I study smarter, not harder!",
        author: "Mithran",
        role: "Class 12 Student",
        avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Mithran&backgroundColor=ffd5dc",
    },
    {
        quote: "Best educational platform I've used. The interface is clean and the AI responses are incredibly helpful.",
        author: "Sajith",
        role: "Class 11 Student",
        avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Sajith&backgroundColor=c9f0db",
    },
];

// Features data with cartoon images
const features = [
    {
        title: "Book to Bot",
        description: "Upload any textbook and chat with it",
        image: "/features/book-to-bot.png",
        category: "AI Learning"
    },
    {
        title: "AI-Powered Learning",
        description: "Personalized explanations tailored to you",
        image: "/features/ai-learning.png",
        category: "Smart Study"
    },
    {
        title: "Smart Tests",
        description: "Adaptive tests based on performance",
        image: "/features/smart-tests.png",
        category: "Assessment"
    },
    {
        title: "Progress Analytics",
        description: "Track your learning journey",
        image: "/features/progress-analytics.png",
        category: "Insights"
    },
];

// FAQ data
const faqs = [
    {
        icon: BookOpen,
        question: "How does Book to Bot work?",
        answer: "Simply upload your textbook PDF and our AI will analyze it. You can then ask questions about any topic in the book and get instant, contextual answers."
    },
    {
        icon: Award,
        question: "Is Brainwave free to use?",
        answer: "We offer a free tier with basic features. Premium plans with unlimited AI chats and advanced analytics will be available soon."
    },
    {
        icon: GraduationCap,
        question: "Which subjects are supported?",
        answer: "Brainwave supports all NCERT subjects including Physics, Chemistry, Biology, Mathematics, and more."
    },
    {
        icon: Lightbulb,
        question: "How accurate are the AI responses?",
        answer: "Our AI is trained on verified educational content and provides highly accurate explanations based on your textbook."
    },
    {
        icon: Shield,
        question: "Is my data secure?",
        answer: "Absolutely. We use enterprise-grade encryption and never share your data with third parties."
    },
];

// Navbar
const Navbar = () => {
    const navigate = useNavigate();
    return (
        <motion.nav
            initial={{ y: -100 }}
            animate={{ y: 0 }}
            transition={{ duration: 0.5 }}
            className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-lg border-b border-neutral-200"
        >
            <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-neutral-900 rounded-lg flex items-center justify-center">
                        <Zap className="w-5 h-5 text-white" />
                    </div>
                    <span className="text-xl font-bold text-neutral-900">Brainwave</span>
                </div>
                <div className="flex items-center gap-3">
                    <button onClick={() => navigate('/login')} className="px-5 py-2 text-sm font-medium text-neutral-700 hover:text-neutral-900">
                        Login
                    </button>
                    <button onClick={() => navigate('/signup')} className="px-5 py-2 text-sm font-medium bg-neutral-900 text-white rounded-full hover:bg-neutral-800">
                        Sign Up
                    </button>
                </div>
            </div>
        </motion.nav>
    );
};

// Features Panel - Image cards with hover effect
const FeaturesPanel = ({ navigate }) => {
    const [stopScroll, setStopScroll] = useState(false);

    return (
        <div className="w-full h-full flex-shrink-0 bg-gradient-to-br from-white to-neutral-50 p-3 flex flex-col">
            <div className="text-center mb-3">
                <h2 className="text-2xl font-bold text-neutral-900">Explore Features</h2>
                <p className="text-sm text-neutral-500 mt-1">Hover to discover, click to explore</p>
            </div>

            {/* Marquee container */}
            <div
                className="flex-1 overflow-hidden relative"
                onMouseEnter={() => setStopScroll(true)}
                onMouseLeave={() => setStopScroll(false)}
            >
                {/* Left fade */}
                <div className="absolute left-0 top-0 h-full w-16 z-10 pointer-events-none bg-gradient-to-r from-white to-transparent" />

                {/* Scrolling cards */}
                <motion.div
                    className="flex h-full items-center"
                    animate={{ x: stopScroll ? 0 : [0, -features.length * 240] }}
                    transition={{
                        x: { duration: features.length * 5, repeat: Infinity, ease: "linear" },
                    }}
                >
                    {[...features, ...features, ...features].map((feature, index) => (
                        <div
                            key={index}
                            onClick={() => navigate('/login')}
                            className="w-56 mx-3 h-72 relative group cursor-pointer flex-shrink-0 rounded-xl overflow-hidden hover:scale-95 transition-all duration-300"
                        >
                            <img
                                src={feature.image}
                                alt={feature.title}
                                className="w-full h-full object-cover"
                            />
                            {/* Hover overlay */}
                            <div className="flex flex-col items-center justify-center px-4 opacity-0 group-hover:opacity-100 transition-all duration-300 absolute inset-0 backdrop-blur-sm bg-black/40">
                                <p className="text-white text-lg font-semibold text-center mb-2">
                                    {feature.title}
                                </p>
                                <p className="text-white/80 text-sm text-center">
                                    {feature.description}
                                </p>
                                <div className="mt-4 px-4 py-2 bg-white/20 rounded-full text-white text-xs font-medium">
                                    Explore →
                                </div>
                            </div>
                            {/* Category badge */}
                            <div className="absolute top-3 left-3 px-2 py-1 bg-white/90 rounded-full text-xs font-medium text-neutral-700">
                                {feature.category}
                            </div>
                        </div>
                    ))}
                </motion.div>

                {/* Right fade */}
                <div className="absolute right-0 top-0 h-full w-16 z-10 pointer-events-none bg-gradient-to-l from-white to-transparent" />
            </div>
        </div>
    );
};

// Testimonials Panel
const TestimonialsPanel = () => {
    const [activeIndex, setActiveIndex] = useState(0);
    const [isHovered, setIsHovered] = useState(false);
    const containerRef = useRef(null);
    const mouseX = useMotionValue(0);
    const mouseY = useMotionValue(0);
    const cursorX = useSpring(mouseX, { damping: 25, stiffness: 150 });
    const cursorY = useSpring(mouseY, { damping: 25, stiffness: 150 });

    const handleMouseMove = useCallback((e) => {
        if (!containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        mouseX.set(e.clientX - rect.left);
        mouseY.set(e.clientY - rect.top);
    }, [mouseX, mouseY]);

    const t = testimonials[activeIndex];

    return (
        <div className="w-full h-full flex-shrink-0 bg-white p-4 flex flex-col">
            <div className="text-center mb-4">
                <span className="px-3 py-1 bg-neutral-100 text-neutral-700 text-xs font-semibold rounded-full uppercase">Testimonials</span>
            </div>
            <div
                ref={containerRef}
                className="flex-1 relative flex items-center justify-center cursor-none"
                onMouseMove={handleMouseMove}
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
                onClick={() => setActiveIndex((activeIndex + 1) % testimonials.length)}
            >
                <motion.div
                    className="pointer-events-none absolute z-50 mix-blend-difference"
                    style={{ x: cursorX, y: cursorY, translateX: "-50%", translateY: "-50%" }}
                >
                    <motion.div
                        className="rounded-full bg-neutral-900 flex items-center justify-center"
                        animate={{ width: isHovered ? 60 : 0, height: isHovered ? 60 : 0, opacity: isHovered ? 1 : 0 }}
                    >
                        <span className="text-white text-[10px] font-medium uppercase">Next</span>
                    </motion.div>
                </motion.div>

                <div className="absolute top-0 right-0 font-mono text-sm">
                    <span className="text-2xl font-light text-neutral-900">{String(activeIndex + 1).padStart(2, "0")}</span>
                    <span className="text-neutral-400">/{String(testimonials.length).padStart(2, "0")}</span>
                </div>

                <div className="max-w-lg text-center">
                    <AnimatePresence mode="wait">
                        <motion.p
                            key={activeIndex}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="text-xl font-light text-neutral-800 leading-relaxed"
                        >
                            "{t.quote}"
                        </motion.p>
                    </AnimatePresence>
                    <motion.div className="mt-8 flex items-center justify-center gap-3" layout>
                        <img src={t.avatar} alt={t.author} className="w-12 h-12 rounded-full" />
                        <div className="text-left">
                            <p className="font-medium text-neutral-900">{t.author}</p>
                            <p className="text-sm text-neutral-500">{t.role}</p>
                        </div>
                    </motion.div>
                </div>

                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-neutral-100">
                    <motion.div className="h-full bg-neutral-900" animate={{ width: `${((activeIndex + 1) / testimonials.length) * 100}%` }} />
                </div>
                <p className="absolute bottom-4 text-[10px] text-neutral-400 uppercase tracking-widest">Click anywhere</p>
            </div>
        </div>
    );
};

// FAQ Panel
const FAQPanel = () => {
    const [activeIndex, setActiveIndex] = useState(0);

    return (
        <div className="w-full h-full flex-shrink-0 bg-neutral-50 p-6 flex flex-col">
            <div className="text-center mb-4">
                <span className="inline-flex items-center gap-1 px-3 py-1 bg-neutral-200 text-neutral-700 text-xs font-semibold rounded-full uppercase">
                    <HelpCircle className="w-3 h-3" /> FAQs
                </span>
            </div>

            <div className="flex-1 grid grid-cols-2 gap-4 min-h-0">
                {/* Left - Questions */}
                <div className="flex flex-col gap-2 overflow-hidden">
                    {faqs.map((faq, index) => {
                        const Icon = faq.icon;
                        return (
                            <motion.div
                                key={index}
                                onClick={() => setActiveIndex(index)}
                                whileHover={{ x: 4 }}
                                className={`flex-1 p-3 rounded-xl cursor-pointer flex items-center gap-3 ${activeIndex === index
                                    ? 'bg-neutral-900 text-white'
                                    : 'bg-white border border-neutral-200 hover:border-neutral-300'
                                    }`}
                            >
                                <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${activeIndex === index ? 'bg-white/20' : 'bg-neutral-100'
                                    }`}>
                                    <Icon className={`w-5 h-5 ${activeIndex === index ? 'text-white' : 'text-neutral-600'}`} />
                                </div>
                                <p className={`text-sm font-medium line-clamp-2 ${activeIndex === index ? 'text-white' : 'text-neutral-700'}`}>
                                    {faq.question}
                                </p>
                            </motion.div>
                        );
                    })}
                </div>

                {/* Right - Answer */}
                <div className="bg-white rounded-2xl border border-neutral-200 p-6 flex flex-col">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={activeIndex}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="flex-1 flex flex-col"
                        >
                            <div className="w-14 h-14 bg-neutral-100 rounded-xl flex items-center justify-center mb-4">
                                {React.createElement(faqs[activeIndex].icon, { className: "w-7 h-7 text-neutral-900" })}
                            </div>
                            <h3 className="text-lg font-semibold text-neutral-900 mb-3">
                                {faqs[activeIndex].question}
                            </h3>
                            <p className="text-base text-neutral-600 leading-relaxed flex-1">
                                {faqs[activeIndex].answer}
                            </p>
                        </motion.div>
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
};

// CTA Panel
const CTAPanel = ({ navigate }) => (
    <div className="w-full h-full flex-shrink-0 bg-neutral-900 flex items-center justify-center text-center p-8">
        <div>
            <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Zap className="w-8 h-8 text-neutral-900" />
            </div>
            <h2 className="text-3xl font-bold text-white mb-4">Ready to start?</h2>
            <p className="text-neutral-400 mb-8 max-w-sm mx-auto">Join thousands of students learning smarter with Brainwave.</p>
            <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => navigate('/login')}
                className="inline-flex items-center gap-2 px-8 py-4 bg-white text-neutral-900 rounded-full font-semibold hover:bg-neutral-100"
            >
                Get Started <ArrowRight className="w-5 h-5" />
            </motion.button>
        </div>
    </div>
);

// Progress Indicator
const ScrollProgress = ({ progress, panels }) => (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 flex items-center gap-2 px-4 py-2 bg-white/80 backdrop-blur-lg rounded-full border border-neutral-200 shadow-lg">
        {panels.map((name, i) => {
            const start = i / panels.length;
            const end = (i + 1) / panels.length;
            const isActive = progress >= start && progress < end;
            const isPast = progress >= end;
            return (
                <div key={i} className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${isActive ? 'bg-neutral-900 scale-125' : isPast ? 'bg-neutral-900' : 'bg-neutral-300'}`} />
                    <span className={`text-xs font-medium ${isActive ? 'text-neutral-900' : 'text-neutral-400'}`}>{name}</span>
                    {i < panels.length - 1 && <div className="w-6 h-0.5 bg-neutral-200" />}
                </div>
            );
        })}
    </div>
);

// Footer
const Footer = () => {
    const navigate = useNavigate();
    return (
        <footer className="bg-neutral-950 text-white py-12 px-6">
            <div className="max-w-6xl mx-auto">
                <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-8">
                    <div className="col-span-2 md:col-span-1">
                        <div className="flex items-center gap-2 mb-4">
                            <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
                                <Zap className="w-5 h-5 text-neutral-900" />
                            </div>
                            <span className="text-lg font-bold">Brainwave</span>
                        </div>
                        <p className="text-sm text-neutral-400">AI-powered learning for everyone.</p>
                    </div>
                    {['Product', 'Resources', 'Company', 'Legal'].map((title) => (
                        <div key={title}>
                            <h4 className="font-semibold text-sm mb-3">{title}</h4>
                            <ul className="space-y-2">
                                {['Link 1', 'Link 2', 'Link 3'].map((link, i) => (
                                    <li key={i}>
                                        <span onClick={() => navigate('/login')} className="text-sm text-neutral-400 hover:text-white cursor-pointer">{link}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </div>
                <div className="border-t border-neutral-800 pt-6 flex flex-col md:flex-row items-center justify-between gap-4">
                    <p className="text-sm text-neutral-500">© 2025 Brainwave. All rights reserved.</p>
                    <p className="text-sm text-neutral-500">Built with ❤ by <span className="text-white font-medium">4%</span></p>
                </div>
            </div>
        </footer>
    );
};

const panelNames = ['Features', 'Reviews', 'FAQ', 'Start'];

// Main Landing Page
export default function LandingPage() {
    const navigate = useNavigate();
    const containerRef = useRef(null);
    const { scrollYProgress } = useScroll({ target: containerRef });
    const [progress, setProgress] = useState(0);

    useEffect(() => {
        const unsubscribe = scrollYProgress.on('change', setProgress);
        return () => unsubscribe();
    }, [scrollYProgress]);

    // Title animation - fades out and moves up
    const titleOpacity = useTransform(scrollYProgress, [0, 0.1], [1, 0]);
    const titleY = useTransform(scrollYProgress, [0, 0.15], [0, -150]);

    // Screen animation - stays at 85-90% of viewport, just tilts
    const screenRotateX = useTransform(scrollYProgress, [0, 0.15], [15, 0]);
    const screenScale = useTransform(scrollYProgress, [0, 0.15], [0.9, 1]);
    const screenY = useTransform(scrollYProgress, [0, 0.15], [60, 0]);

    // Horizontal scroll inside screen
    const innerX = useTransform(scrollYProgress, [0.2, 1], ['0%', '-300%']);

    return (
        <div className="bg-gradient-to-br from-white via-neutral-50 to-sky-50/30 min-h-screen">
            <Navbar />
            <ScrollProgress progress={progress} panels={panelNames} />

            <div ref={containerRef} className="h-[500vh] relative">
                <div className="sticky top-0 h-screen flex flex-col items-center justify-center overflow-hidden">

                    {/* Hero Title - Fades out and goes behind screen on scroll */}
                    <motion.div
                        style={{ opacity: titleOpacity, y: titleY }}
                        className="absolute top-20 left-0 right-0 text-center z-10 pointer-events-none"
                    >
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex items-center justify-center gap-2 mb-4"
                        >
                            <div className="flex -space-x-2">
                                {testimonials.slice(0, 4).map((t, i) => (
                                    <img key={i} src={t.avatar} alt="" className="w-8 h-8 rounded-full border-2 border-white" />
                                ))}
                            </div>
                            <span className="text-sm text-neutral-600 font-medium px-3 py-1 bg-white rounded-full border border-neutral-200">
                                1k+ students
                            </span>
                        </motion.div>
                        <motion.h1
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                            className="text-4xl md:text-5xl font-bold text-neutral-900 mb-2"
                        >
                            Learn Smarter with
                        </motion.h1>
                        <motion.span
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                            className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-neutral-900 via-neutral-600 to-neutral-400 bg-clip-text text-transparent"
                        >
                            AI-Powered Education
                        </motion.span>
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.3 }}
                            className="mt-6 pointer-events-auto"
                        >
                            <button
                                onClick={() => navigate('/login')}
                                className="px-6 py-3 bg-neutral-900 text-white rounded-full font-medium hover:bg-neutral-800"
                            >
                                Get Started
                            </button>
                        </motion.div>
                    </motion.div>

                    {/* The Screen - Stays at 85-90% of viewport, centered */}
                    <motion.div
                        style={{
                            rotateX: screenRotateX,
                            scale: screenScale,
                            y: screenY,
                            transformPerspective: 1200,
                            boxShadow: "0 30px 80px -20px rgba(0, 0, 0, 0.25)",
                        }}
                        className="w-[90%] max-w-6xl h-[70vh] bg-white border-4 border-neutral-200 rounded-3xl overflow-hidden z-20"
                    >
                        <div className="h-full overflow-hidden">
                            <motion.div style={{ x: innerX }} className="flex h-full">
                                <FeaturesPanel navigate={navigate} />
                                <TestimonialsPanel />
                                <FAQPanel />
                                <CTAPanel navigate={navigate} />
                            </motion.div>
                        </div>
                    </motion.div>

                    {/* Scroll hint */}
                    <motion.div
                        style={{ opacity: titleOpacity }}
                        className="absolute bottom-6 text-center"
                    >
                        <p className="text-sm text-neutral-400 flex items-center gap-2">
                            Scroll to explore <ChevronRight className="w-4 h-4 animate-pulse" />
                        </p>
                    </motion.div>
                </div>
            </div>

            <Footer />
        </div>
    );
}