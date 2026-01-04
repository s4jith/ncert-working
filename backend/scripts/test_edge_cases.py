"""
Test Edge Case Handling

Tests the new edge case handling features:
1. Progressive search (searches earlier classes if no content found)
2. Gemini fallback (uses general knowledge with disclaimer)
3. Class availability handling (Class 11-12 limited content)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

def test_annotation_request(question: str, class_level: int, subject: str = "Mathematics"):
    """Test annotation endpoint with edge case"""
    try:
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing: {question}")
        logger.info(f"Class: {class_level}, Subject: {subject}")
        logger.info(f"{'='*80}")
        
        response = requests.post(
            f"{BASE_URL}/api/annotation",
            json={
                "selected_text": question,
                "action": "define",
                "class_level": class_level,
                "subject": subject,
                "chapter": None
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            source_count = data.get("source_count", 0)
            
            logger.info(f"\n✅ SUCCESS")
            logger.info(f"Sources used: {source_count}")
            logger.info(f"\nAnswer:\n{answer[:500]}...")
            
            # Check for fallback indicators
            if source_count == 0:
                logger.info(f"\n⚠️  FALLBACK USED: No sources found, used Gemini general knowledge")
            elif "Class" in answer and any(str(c) in answer for c in range(5, 10)):
                logger.info(f"\n🔄 PROGRESSIVE SEARCH: Found content from earlier class")
            
            return True
        else:
            logger.error(f"\n❌ FAILED: {response.status_code}")
            logger.error(f"Error: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"\n❌ EXCEPTION: {e}")
        return False

def main():
    """Run edge case tests"""
    print(f"\n{'='*80}")
    print(f"🔧 EDGE CASE TESTING")
    print(f"{'='*80}")
    print(f"\nTesting new features:")
    print(f"✓ Progressive search (earlier classes)")
    print(f"✓ Gemini fallback (general knowledge)")
    print(f"✓ Class 11-12 handling")
    print(f"\n{'='*80}\n")
    
    # Test 1: Basic question that should work
    logger.info(f"\n📝 Test 1: Basic content (should find in current/previous class)")
    test_annotation_request(
        question="What is the perimeter of a rectangle?",
        class_level=6,
        subject="Mathematics"
    )
    time.sleep(15)
    
    # Test 2: Advanced topic (might need progressive search)
    logger.info(f"\n📝 Test 2: Advanced topic (might need earlier class foundation)")
    test_annotation_request(
        question="Explain the concept of HCF",
        class_level=10,
        subject="Mathematics"
    )
    time.sleep(15)
    
    # Test 3: Class 11 question (limited content)
    logger.info(f"\n📝 Test 3: Class 11 content (limited availability)")
    test_annotation_request(
        question="What is the binomial theorem?",
        class_level=11,
        subject="Mathematics"
    )
    time.sleep(15)
    
    # Test 4: Topic likely not in textbook (should use fallback)
    logger.info(f"\n📝 Test 4: Topic not in textbook (should use Gemini fallback)")
    test_annotation_request(
        question="Explain what machine learning is",
        class_level=10,
        subject="Mathematics"
    )
    time.sleep(15)
    
    print(f"\n{'='*80}")
    print(f"✅ EDGE CASE TESTING COMPLETE")
    print(f"{'='*80}")
    print(f"\nCheck the logs above to verify:")
    print(f"1. Progressive search found content from earlier classes")
    print(f"2. Fallback was used when no content found")
    print(f"3. Class 11 questions handled gracefully")

if __name__ == "__main__":
    main()
