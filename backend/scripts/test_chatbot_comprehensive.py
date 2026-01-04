"""
Automated Chatbot Testing - State Topper Question Bank
Tests chatbot with comprehensive MATHEMATICS questions across Class 5-12
NOTE: Currently only Mathematics data is available (49,421 vectors)
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple

# Backend API URL
API_BASE_URL = "http://localhost:8000"

# Test questions organized by difficulty and class level
# We have Mathematics data for Class 5-12
MATH_TESTS = {
    "basic": [
        # Class 5-6 Level Questions
        {
            "q": "What is a fraction?",
            "keywords": ["fraction", "numerator", "denominator", "part"],
            "class": 5,
            "subject": "Mathematics"
        },
        {
            "q": "What are natural numbers?",
            "keywords": ["natural", "counting", "1, 2, 3", "positive"],
            "class": 5,
            "subject": "Mathematics"
        },
        {
            "q": "Explain what is meant by the perimeter of a rectangle",
            "keywords": ["perimeter", "sum", "length", "breadth", "boundary"],
            "class": 5,
            "subject": "Mathematics"
        },
        # Class 7-8 Level Questions
        {
            "q": "What is a polynomial?",
            "keywords": ["polynomial", "expression", "variable", "degree"],
            "class": 8,
            "subject": "Mathematics"
        },
        {
            "q": "Define integers",
            "keywords": ["integer", "positive", "negative", "zero", "whole"],
            "class": 7,
            "subject": "Mathematics"
        },
        {
            "q": "What are rational numbers?",
            "keywords": ["rational", "p/q", "fraction", "integer"],
            "class": 7,
            "subject": "Mathematics"
        },
        # Class 9-10 Level Questions
        {
            "q": "Define linear equations in two variables",
            "keywords": ["linear", "equation", "two variables", "ax+by"],
            "class": 10,
            "subject": "Mathematics"
        },
        {
            "q": "What is the difference between rational and irrational numbers?",
            "keywords": ["rational", "irrational", "p/q", "decimal"],
            "class": 9,
            "subject": "Mathematics"
        },
        {
            "q": "Explain the term 'degree of a polynomial'",
            "keywords": ["degree", "highest power", "exponent"],
            "class": 9,
            "subject": "Mathematics"
        },
        {
            "q": "What are prime numbers? Give first 10 prime numbers",
            "keywords": ["prime", "divisible", "2, 3, 5, 7", "11, 13"],
            "class": 10,
            "subject": "Mathematics"
        },
        # Class 11-12 Level Questions
        {
            "q": "What is a set in mathematics?",
            "keywords": ["set", "collection", "objects", "elements"],
            "class": 11,
            "subject": "Mathematics"
        },
        {
            "q": "Define a function in mathematics",
            "keywords": ["function", "relation", "domain", "range", "mapping"],
            "class": 11,
            "subject": "Mathematics"
        }
    ],
    "medium": [
        # Class 5-6 Level
        {
            "q": "How do you add two fractions with different denominators?",
            "keywords": ["LCM", "common denominator", "add", "numerator"],
            "class": 5,
            "subject": "Mathematics"
        },
        {
            "q": "What is the formula for area of a triangle?",
            "keywords": ["area", "triangle", "base", "height", "1/2"],
            "class": 6,
            "subject": "Mathematics"
        },
        # Class 7-8 Level
        {
            "q": "How do you solve simple equations?",
            "keywords": ["equation", "variable", "isolate", "transpose"],
            "class": 7,
            "subject": "Mathematics"
        },
        {
            "q": "Explain the concept of percentage",
            "keywords": ["percentage", "per hundred", "fraction", "100"],
            "class": 8,
            "subject": "Mathematics"
        },
        # Class 9-10 Level
        {
            "q": "How do I find the roots of a quadratic equation?",
            "keywords": ["quadratic formula", "factorization", "roots", "discriminant"],
            "class": 10,
            "subject": "Mathematics"
        },
        {
            "q": "How can I prove that √2 is irrational?",
            "keywords": ["contradiction", "proof", "rational", "irrational"],
            "class": 10,
            "subject": "Mathematics"
        },
        {
            "q": "What is the relationship between zeros of a polynomial and its coefficients?",
            "keywords": ["sum", "product", "roots", "coefficients"],
            "class": 10,
            "subject": "Mathematics"
        },
        {
            "q": "How do I find the HCF of two numbers using Euclid's division algorithm?",
            "keywords": ["HCF", "Euclid", "division", "remainder"],
            "class": 10,
            "subject": "Mathematics"
        },
        # Class 11-12 Level
        {
            "q": "What is the binomial theorem?",
            "keywords": ["binomial", "expansion", "coefficient", "power"],
            "class": 11,
            "subject": "Mathematics"
        },
        {
            "q": "Explain the concept of limits in calculus",
            "keywords": ["limit", "approaching", "function", "value"],
            "class": 11,
            "subject": "Mathematics"
        }
    ],
    "hard": [
        # Class 6-8 Advanced
        {
            "q": "A rectangular park is 45m long and 30m wide. A path 2.5m wide is constructed outside the park. Find the area of the path.",
            "keywords": ["area", "path", "rectangle", "difference"],
            "class": 6,
            "subject": "Mathematics"
        },
        {
            "q": "The sum of three consecutive odd numbers is 63. Find the numbers.",
            "keywords": ["consecutive", "odd", "sum", "equation"],
            "class": 8,
            "subject": "Mathematics"
        },
        # Class 9-10 Advanced
        {
            "q": "If α and β are the zeros of the polynomial x² - 5x + 6, find a quadratic polynomial whose zeros are 1/α and 1/β",
            "keywords": ["zeros", "polynomial", "reciprocal", "quadratic"],
            "class": 10,
            "subject": "Mathematics"
        },
        {
            "q": "Prove that in a right triangle, the square of the hypotenuse is equal to the sum of squares of the other two sides",
            "keywords": ["Pythagoras", "theorem", "hypotenuse", "square"],
            "class": 10,
            "subject": "Mathematics"
        },
        {
            "q": "Show that any positive odd integer is of the form 6q + 1, or 6q + 3, or 6q + 5, where q is some integer",
            "keywords": ["odd", "integer", "form", "division"],
            "class": 10,
            "subject": "Mathematics"
        },
        {
            "q": "A two-digit number is such that the product of its digits is 12. When 36 is added to the number, the digits interchange their places. Find the number.",
            "keywords": ["two-digit", "product", "digits", "interchange"],
            "class": 10,
            "subject": "Mathematics"
        },
        # Class 11-12 Advanced
        {
            "q": "Find the derivative of x³ + 2x² - 5x + 7 using first principles",
            "keywords": ["derivative", "first principles", "limit", "differentiation"],
            "class": 11,
            "subject": "Mathematics"
        },
        {
            "q": "Prove that sin²θ + cos²θ = 1 for all values of θ",
            "keywords": ["trigonometry", "identity", "sin", "cos", "proof"],
            "class": 10,
            "subject": "Mathematics"
        },
        {
            "q": "Find the sum of first n terms of the arithmetic progression: 3, 7, 11, 15, ...",
            "keywords": ["arithmetic progression", "sum", "formula", "common difference"],
            "class": 10,
            "subject": "Mathematics"
        }
    ]
}


class ChatbotTester:
    def __init__(self):
        self.results = []
        self.start_time = None
        
    def test_question(self, question: Dict, mode: str = "quick") -> Dict:
        """Test a single question"""
        try:
            # API endpoint - Use annotation API for Q&A testing
            url = f"{API_BASE_URL}/api/annotation"
            
            # Map testing modes to annotation actions
            action_map = {
                "quick": "define",
                "deepdive": "elaborate"
            }
            
            payload = {
                "selected_text": question["q"],
                "action": action_map.get(mode, "define"),
                "class_level": question["class"],
                "subject": question["subject"],
                "chapter": 1  # Default chapter
            }
            
            start_time = time.time()
            response = requests.post(url, json=payload, timeout=60)  # Increased to 60s
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                source_count = data.get("source_count", 0)  # Annotation API returns count, not list
                
                # Check for keywords
                answer_lower = answer.lower()
                keywords_found = sum(1 for kw in question["keywords"] if kw.lower() in answer_lower)
                keyword_score = (keywords_found / len(question["keywords"])) * 100
                
                # Check for hallucination indicators
                hallucination_indicators = [
                    "i don't have",
                    "according to my knowledge",
                    "i cannot",
                    "not found in the book"
                ]
                has_hallucination = any(ind in answer_lower for ind in hallucination_indicators)
                
                result = {
                    "question": question["q"],
                    "subject": question["subject"],
                    "class": question["class"],
                    "status": "success",
                    "answer_length": len(answer),
                    "response_time": round(response_time, 2),
                    "source_count": source_count,
                    "keyword_score": round(keyword_score, 1),
                    "has_answer": len(answer) > 100,
                    "has_hallucination": has_hallucination,
                    "answer_preview": answer[:200] + "..." if len(answer) > 200 else answer,
                    "full_answer": answer  # Store full answer for review
                }
            else:
                result = {
                    "question": question["q"],
                    "status": "error",
                    "error_code": response.status_code,
                    "error_msg": response.text[:200],
                    "full_answer": None
                }
                
        except Exception as e:
            result = {
                "question": question["q"],
                "status": "exception",
                "error": str(e),
                "full_answer": None
            }
        
        return result
    
    def run_test_suite(self, test_suite: Dict, difficulty: str, mode: str = "quick"):
        """Run a complete test suite"""
        print(f"\n{'='*80}")
        print(f"🧪 Testing {difficulty.upper()} Questions ({mode.upper()} mode)")
        print(f"{'='*80}\n")
        
        for i, question in enumerate(test_suite[difficulty], 1):
            print(f"Question {i}/{len(test_suite[difficulty])}: {question['q'][:60]}...")
            
            result = self.test_question(question, mode)
            self.results.append({
                "difficulty": difficulty,
                "mode": mode,
                **result
            })
            
            # Print result
            if result["status"] == "success":
                status_icon = "✅" if result["keyword_score"] >= 50 else "⚠️"
                print(f"  {status_icon} Response: {result['response_time']}s | "
                      f"Sources: {result['source_count']} | "
                      f"Keywords: {result['keyword_score']}% | "
                      f"Length: {result['answer_length']} chars")
                if result["has_hallucination"]:
                    print(f"  ⚠️  WARNING: Possible hallucination detected")
            else:
                error_msg = result.get('error_msg', result.get('error', 'Unknown error'))
                # Shorten rate limit messages
                if "429" in str(error_msg) and "quota" in str(error_msg).lower():
                    print(f"  ❌ FAILED: Rate limit exceeded (429)")
                else:
                    print(f"  ❌ FAILED: {error_msg}")
            
            # CRITICAL FIX: Longer pause to avoid RPM (Requests Per Minute) limits
            # Gemini free tier: ~4 requests/minute per key
            # 15 second delay = 4 requests/minute (safe rate)
            time.sleep(15)  # Increased from 3 to 15 seconds
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print(f"\n{'='*80}")
        print(f"📊 TEST REPORT - State Topper Question Bank")
        print(f"{'='*80}\n")
        
        # Summary statistics
        total = len(self.results)
        successful = sum(1 for r in self.results if r["status"] == "success")
        failed = total - successful
        
        print(f"Total Questions: {total}")
        print(f"Successful: {successful} ({successful/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        print()
        
        # By difficulty
        print("📈 Results by Difficulty:")
        for difficulty in ["basic", "medium", "hard"]:
            diff_results = [r for r in self.results if r.get("difficulty") == difficulty]
            if diff_results:
                avg_score = sum(r.get("keyword_score", 0) for r in diff_results) / len(diff_results)
                avg_time = sum(r.get("response_time", 0) for r in diff_results) / len(diff_results)
                success_rate = sum(1 for r in diff_results if r["status"] == "success") / len(diff_results) * 100
                
                print(f"  {difficulty.capitalize():10} - Success: {success_rate:5.1f}% | "
                      f"Avg Score: {avg_score:5.1f}% | Avg Time: {avg_time:.2f}s")
        
        # Quality metrics
        print(f"\n📊 Quality Metrics:")
        successful_results = [r for r in self.results if r["status"] == "success"]
        if successful_results:
            avg_keyword_score = sum(r["keyword_score"] for r in successful_results) / len(successful_results)
            avg_response_time = sum(r["response_time"] for r in successful_results) / len(successful_results)
            avg_sources = sum(r["source_count"] for r in successful_results) / len(successful_results)
            hallucination_count = sum(1 for r in successful_results if r["has_hallucination"])
            
            print(f"  Average Keyword Match: {avg_keyword_score:.1f}%")
            print(f"  Average Response Time: {avg_response_time:.2f}s")
            print(f"  Average Source Count: {avg_sources:.1f}")
            print(f"  Hallucination Cases: {hallucination_count}")
        
        # Save detailed JSON report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"test_report_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": total,
                    "successful": successful,
                    "failed": failed
                },
                "results": self.results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed JSON report saved: {report_file}")
        
        # Generate human-readable HTML report
        self._generate_html_report(timestamp)
        
    def _generate_html_report(self, timestamp: str):
        """Generate a beautiful HTML report with full answers"""
        html_file = f"test_report_{timestamp}.html"
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chatbot Test Report - {timestamp}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
        }}
        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        .question-card {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .question-card.success {{
            border-left: 4px solid #10b981;
        }}
        .question-card.warning {{
            border-left: 4px solid #f59e0b;
        }}
        .question-card.error {{
            border-left: 4px solid #ef4444;
        }}
        .question-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
        }}
        .question-text {{
            font-size: 18px;
            font-weight: 600;
            color: #333;
            flex: 1;
        }}
        .status-badge {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .status-badge.success {{
            background: #d1fae5;
            color: #065f46;
        }}
        .status-badge.warning {{
            background: #fef3c7;
            color: #92400e;
        }}
        .status-badge.error {{
            background: #fee2e2;
            color: #991b1b;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 15px 0;
            padding: 15px;
            background: #f9fafb;
            border-radius: 6px;
        }}
        .metric {{
            text-align: center;
        }}
        .metric-label {{
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 20px;
            font-weight: bold;
            color: #333;
        }}
        .answer-section {{
            margin-top: 20px;
            padding: 20px;
            background: #f9fafb;
            border-radius: 6px;
        }}
        .answer-section h4 {{
            margin: 0 0 15px 0;
            color: #333;
        }}
        .answer-text {{
            white-space: pre-wrap;
            line-height: 1.8;
            color: #4b5563;
        }}
        .error-message {{
            color: #dc2626;
            padding: 15px;
            background: #fee2e2;
            border-radius: 6px;
            margin-top: 15px;
        }}
        .difficulty-section {{
            margin-bottom: 40px;
        }}
        .difficulty-header {{
            background: #6366f1;
            color: white;
            padding: 15px 25px;
            border-radius: 8px 8px 0 0;
            font-size: 20px;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎓 Chatbot Test Report</h1>
        <p>Mathematics Questions (Class 5-12)</p>
        <p>Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
    </div>
"""
        
        # Summary statistics
        total = len(self.results)
        successful = sum(1 for r in self.results if r["status"] == "success")
        failed = total - successful
        
        if successful > 0:
            success_results = [r for r in self.results if r["status"] == "success"]
            avg_time = sum(r.get("response_time", 0) for r in success_results) / len(success_results)
            avg_keyword = sum(r.get("keyword_score", 0) for r in success_results) / len(success_results)
        else:
            avg_time = 0
            avg_keyword = 0
        
        html_content += f"""
    <div class="summary">
        <div class="summary-card">
            <h3>Total Questions</h3>
            <div class="value">{total}</div>
        </div>
        <div class="summary-card">
            <h3>Successful</h3>
            <div class="value" style="color: #10b981;">{successful}</div>
        </div>
        <div class="summary-card">
            <h3>Failed</h3>
            <div class="value" style="color: #ef4444;">{failed}</div>
        </div>
        <div class="summary-card">
            <h3>Success Rate</h3>
            <div class="value">{(successful/total*100):.1f}%</div>
        </div>
        <div class="summary-card">
            <h3>Avg Response Time</h3>
            <div class="value">{avg_time:.1f}s</div>
        </div>
        <div class="summary-card">
            <h3>Avg Keyword Match</h3>
            <div class="value">{avg_keyword:.1f}%</div>
        </div>
    </div>
"""
        
        # Group results by difficulty
        difficulties = {}
        for result in self.results:
            diff = result.get("difficulty", "unknown")
            if diff not in difficulties:
                difficulties[diff] = []
            difficulties[diff].append(result)
        
        # Render each difficulty section
        for difficulty, results in difficulties.items():
            html_content += f"""
    <div class="difficulty-section">
        <div class="difficulty-header">{difficulty.upper()} Questions</div>
"""
            
            for i, result in enumerate(results, 1):
                status = result["status"]
                card_class = "success" if status == "success" else "error"
                
                if status == "success" and result.get("keyword_score", 0) < 50:
                    card_class = "warning"
                
                badge_class = card_class
                
                html_content += f"""
        <div class="question-card {card_class}">
            <div class="question-header">
                <div class="question-text">Q{i}: {result["question"]}</div>
                <div class="status-badge {badge_class}">
                    {"✓ Success" if status == "success" else "✗ Failed"}
                </div>
            </div>
"""
                
                if status == "success":
                    html_content += f"""
            <div class="metrics">
                <div class="metric">
                    <div class="metric-label">Response Time</div>
                    <div class="metric-value">{result.get("response_time", 0):.1f}s</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Sources Used</div>
                    <div class="metric-value">{result.get("source_count", 0)}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Keyword Match</div>
                    <div class="metric-value">{result.get("keyword_score", 0):.0f}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Answer Length</div>
                    <div class="metric-value">{result.get("answer_length", 0)}</div>
                </div>
            </div>
            
            <div class="answer-section">
                <h4>📝 Full Answer:</h4>
                <div class="answer-text">{result.get("full_answer", "No answer available")}</div>
            </div>
"""
                else:
                    error_msg = result.get("error_msg", result.get("error", "Unknown error"))
                    html_content += f"""
            <div class="error-message">
                <strong>Error:</strong> {error_msg}
            </div>
"""
                
                html_content += """
        </div>
"""
            
            html_content += """
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"📄 Human-readable HTML report saved: {html_file}")
        print(f"   Open this file in your browser to view full answers!")
    
    def _identify_problem_areas(self):
        """Identify and print problem areas from test results"""
        successful_results = [r for r in self.results if r["status"] == "success"]
        
        # Identify problem areas
        print(f"\n🔍 Problem Areas:")
        low_score_questions = [r for r in successful_results if r.get("keyword_score", 0) < 50]
        if low_score_questions:
            print(f"  ⚠️  {len(low_score_questions)} questions with <50% keyword match:")
            for q in low_score_questions[:5]:  # Show first 5
                print(f"     - {q['question'][:60]}... (Score: {q['keyword_score']}%)")
        else:
            print(f"  ✅ All questions have good keyword match!")
        
        print(f"\n{'='*80}\n")


def main():
    """Main test execution"""
    print("\n" + "="*80)
    print("🎓 COMPREHENSIVE CHATBOT TESTING - MATHEMATICS (Class 5-12)")
    print("="*80)
    print(f"\nStart Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Backend: {API_BASE_URL}")
    print(f"Data Available: Mathematics only (49,421 vectors)")
    
    tester = ChatbotTester()
    
    # Test Mathematics ONLY (we have data for Class 5-12)
    print("\n\n📐 MATHEMATICS TESTING (Class 5-12)")
    print("="*80)
    tester.run_test_suite(MATH_TESTS, "basic", mode="quick")
    tester.run_test_suite(MATH_TESTS, "medium", mode="quick")
    tester.run_test_suite(MATH_TESTS, "hard", mode="deepdive")
    
    # Generate final report
    tester.generate_report()
    
    # Identify problem areas
    tester._identify_problem_areas()
    
    print(f"\n✅ Testing completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Next: Open the HTML report in your browser to view full answers!")


if __name__ == "__main__":
    main()
