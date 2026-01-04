"""
Create sample questions directly in MongoDB for testing
This bypasses Pinecone and creates test data directly
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.mongo import mongodb
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_sample_questions():
    """Create sample questions for Mathematics Class 10."""
    
    logger.info("Creating sample question bank...")
    
    await mongodb.connect()
    collection = mongodb.db.topic_question_bank
    
    # Sample questions for Class 10 Mathematics Chapter 1
    questions_data = [
        {
            "class_level": 10,
            "subject": "Mathematics",
            "chapter_number": 1,
            "chapter_name": "Real Numbers",
            "topic_id": "euclids_division_lemma",
            "topic_name": "Euclid's Division Lemma",
            "topic_description": "Understanding Euclid's division algorithm and its applications",
            "page_range": "1-5",
            "questions": [
                {
                    "topic_id": "euclids_division_lemma",
                    "topic_name": "Euclid's Division Lemma",
                    "chapter": 1,
                    "chapter_name": "Real Numbers",
                    "question_text": "State Euclid's Division Lemma.",
                    "correct_answer": "Euclid's Division Lemma states that for any two positive integers a and b, there exist unique integers q and r such that a = bq + r, where 0 ≤ r < b. Here, a is the dividend, b is the divisor, q is the quotient, and r is the remainder.",
                    "difficulty": "easy",
                    "marks": 2
                },
                {
                    "topic_id": "euclids_division_lemma",
                    "topic_name": "Euclid's Division Lemma",
                    "chapter": 1,
                    "chapter_name": "Real Numbers",
                    "question_text": "Use Euclid's division algorithm to find the HCF of 135 and 225.",
                    "correct_answer": "Step 1: 225 = 135 × 1 + 90. Step 2: 135 = 90 × 1 + 45. Step 3: 90 = 45 × 2 + 0. Since the remainder is 0, HCF(135, 225) = 45.",
                    "difficulty": "medium",
                    "marks": 3
                },
                {
                    "topic_id": "euclids_division_lemma",
                    "topic_name": "Euclid's Division Lemma",
                    "chapter": 1,
                    "chapter_name": "Real Numbers",
                    "question_text": "Show that any positive odd integer is of the form 6q + 1, or 6q + 3, or 6q + 5, where q is some integer.",
                    "correct_answer": "By Euclid's division lemma, any positive integer n can be written as n = 6q + r where 0 ≤ r < 6. So r can be 0, 1, 2, 3, 4, or 5. If n is odd, it cannot be 6q (r=0), 6q+2 (r=2), or 6q+4 (r=4) as these are even. Therefore, n must be of the form 6q+1, 6q+3, or 6q+5.",
                    "difficulty": "hard",
                    "marks": 5
                }
            ],
            "total_questions": 3,
            "difficulty_distribution": {"easy": 1, "medium": 1, "hard": 1},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "class_level": 10,
            "subject": "Mathematics",
            "chapter_number": 1,
            "chapter_name": "Real Numbers",
            "topic_id": "fundamental_theorem_arithmetic",
            "topic_name": "Fundamental Theorem of Arithmetic",
            "topic_description": "Prime factorization and uniqueness of representation",
            "page_range": "5-10",
            "questions": [
                {
                    "topic_id": "fundamental_theorem_arithmetic",
                    "topic_name": "Fundamental Theorem of Arithmetic",
                    "chapter": 1,
                    "chapter_name": "Real Numbers",
                    "question_text": "What is the Fundamental Theorem of Arithmetic?",
                    "correct_answer": "The Fundamental Theorem of Arithmetic states that every composite number can be expressed as a product of primes, and this factorization is unique, apart from the order in which the prime factors occur.",
                    "difficulty": "easy",
                    "marks": 2
                },
                {
                    "topic_id": "fundamental_theorem_arithmetic",
                    "topic_name": "Fundamental Theorem of Arithmetic",
                    "chapter": 1,
                    "chapter_name": "Real Numbers",
                    "question_text": "Find the LCM and HCF of 12 and 18 using prime factorization method.",
                    "correct_answer": "12 = 2² × 3 and 18 = 2 × 3². HCF = product of smallest powers = 2 × 3 = 6. LCM = product of greatest powers = 2² × 3² = 36.",
                    "difficulty": "medium",
                    "marks": 3
                },
                {
                    "topic_id": "fundamental_theorem_arithmetic",
                    "topic_name": "Fundamental Theorem of Arithmetic",
                    "chapter": 1,
                    "chapter_name": "Real Numbers",
                    "question_text": "Prove that √2 is irrational using the Fundamental Theorem of Arithmetic.",
                    "difficulty": "hard",
                    "correct_answer": "Assume √2 is rational, so √2 = p/q where p and q are co-prime integers. Then 2 = p²/q², so p² = 2q². This means p² is even, so p is even. Let p = 2m. Then 4m² = 2q², so q² = 2m². This means q² is even, so q is even. But this contradicts our assumption that p and q are co-prime. Therefore, √2 is irrational.",
                    "marks": 5
                }
            ],
            "total_questions": 3,
            "difficulty_distribution": {"easy": 1, "medium": 1, "hard": 1},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "class_level": 10,
            "subject": "Mathematics",
            "chapter_number": 2,
            "chapter_name": "Polynomials",
            "topic_id": "polynomial_basics",
            "topic_name": "Polynomial Basics",
            "topic_description": "Understanding polynomials, degrees, and types",
            "page_range": "1-5",
            "questions": [
                {
                    "topic_id": "polynomial_basics",
                    "topic_name": "Polynomial Basics",
                    "chapter": 2,
                    "chapter_name": "Polynomials",
                    "question_text": "What is a polynomial? Give an example.",
                    "correct_answer": "A polynomial is an algebraic expression consisting of variables and coefficients, involving only addition, subtraction, multiplication, and non-negative integer exponents. Example: 3x² + 2x - 5.",
                    "difficulty": "easy",
                    "marks": 2
                },
                {
                    "topic_id": "polynomial_basics",
                    "topic_name": "Polynomial Basics",
                    "chapter": 2,
                    "chapter_name": "Polynomials",
                    "question_text": "Find the degree of the polynomial 5x³ + 2x² - 3x + 7.",
                    "correct_answer": "The degree of a polynomial is the highest power of the variable. In 5x³ + 2x² - 3x + 7, the highest power is 3, so the degree is 3.",
                    "difficulty": "easy",
                    "marks": 2
                },
                {
                    "topic_id": "polynomial_basics",
                    "topic_name": "Polynomial Basics",
                    "chapter": 2,
                    "chapter_name": "Polynomials",
                    "question_text": "If α and β are the zeros of the polynomial x² - 5x + 6, find the value of α + β and αβ.",
                    "correct_answer": "For a quadratic polynomial ax² + bx + c, sum of zeros = -b/a and product of zeros = c/a. Here, a=1, b=-5, c=6. Therefore, α + β = -(-5)/1 = 5 and αβ = 6/1 = 6.",
                    "difficulty": "medium",
                    "marks": 3
                }
            ],
            "total_questions": 3,
            "difficulty_distribution": {"easy": 2, "medium": 1, "hard": 0},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    # Insert all questions
    for doc in questions_data:
        await collection.update_one(
            {
                "class_level": doc["class_level"],
                "subject": doc["subject"],
                "chapter_number": doc["chapter_number"],
                "topic_id": doc["topic_id"]
            },
            {"$set": doc},
            upsert=True
        )
    
    logger.info(f"✅ Created {len(questions_data)} topics with sample questions")
    logger.info(f"   - Class 10 Mathematics")
    logger.info(f"   - Chapter 1: Real Numbers (2 topics)")
    logger.info(f"   - Chapter 2: Polynomials (1 topic)")
    
    await mongodb.close()


if __name__ == "__main__":
    asyncio.run(create_sample_questions())
