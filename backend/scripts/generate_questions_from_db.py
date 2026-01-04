"""
Generate Questions from Existing PDF Embeddings
This script generates questions for topics from already embedded PDFs in Pinecone.
Run this once to populate the question bank for testing.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.mongo import mongodb
from app.services.topic_question_bank_service import topic_question_bank_service
import google.generativeai as genai
from pinecone import Pinecone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index("ncert-all-subjects")


async def generate_questions_for_chapter(class_level: int, subject: str, chapter_num: int, chapter_name: str):
    """Generate questions for a chapter by querying Pinecone for content."""
    
    logger.info(f"Generating questions for Class {class_level} - {subject} - Chapter {chapter_num}: {chapter_name}")
    
    try:
        # Query Pinecone for chapter content
        namespace = subject.lower().replace(" ", "_")
        
        # Get sample content from this chapter
        query_results = index.query(
            namespace=namespace,
            vector=[0.1] * 768,  # Dummy vector to get results
            filter={
                "class": class_level,
                "subject": subject,
                "chapter": chapter_num
            },
            top_k=20,
            include_metadata=True
        )
        
        if not query_results.matches:
            logger.warning(f"No content found for Chapter {chapter_num}")
            return None
        
        # Extract text content
        content_texts = []
        topics_found = set()
        
        for match in query_results.matches:
            metadata = match.metadata
            if metadata.get("text"):
                content_texts.append(metadata["text"])
            if metadata.get("topic"):
                topics_found.add(metadata["topic"])
        
        if not content_texts:
            logger.warning(f"No text content found for Chapter {chapter_num}")
            return None
        
        # Combine content
        combined_content = "\n\n".join(content_texts[:10])  # Use first 10 chunks
        
        logger.info(f"Found {len(content_texts)} content chunks and {len(topics_found)} topics")
        
        # Identify topics using AI
        topics = await identify_topics(combined_content, chapter_name, list(topics_found))
        
        if not topics:
            logger.warning(f"No topics identified for Chapter {chapter_num}")
            return None
        
        logger.info(f"Identified {len(topics)} topics: {[t['topic_name'] for t in topics]}")
        
        # Generate questions for each topic
        all_questions = []
        for topic in topics:
            questions = await generate_topic_questions(
                class_level, subject, chapter_num, chapter_name,
                topic, combined_content
            )
            all_questions.extend(questions)
        
        # Store in database
        if all_questions:
            await store_questions(class_level, subject, chapter_num, chapter_name, topics, all_questions)
            logger.info(f"✅ Generated and stored {len(all_questions)} questions for Chapter {chapter_num}")
            return len(all_questions)
        
    except Exception as e:
        logger.error(f"Error generating questions for Chapter {chapter_num}: {e}")
        return None


async def identify_topics(content: str, chapter_name: str, existing_topics: list):
    """Use AI to identify topics from chapter content."""
    
    prompt = f"""You are analyzing a chapter from an NCERT textbook.

Chapter: {chapter_name}
Content (sample):
{content[:3000]}

Existing topics mentioned: {', '.join(existing_topics) if existing_topics else 'None'}

Identify 3-5 main topics covered in this chapter. For each topic:
1. Topic name (concise)
2. Brief description (1 sentence)
3. Estimated page range (e.g., "1-5")

Format as JSON array:
[
  {{
    "topic_name": "...",
    "description": "...",
    "page_range": "..."
  }}
]

Only output the JSON array, nothing else."""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        # Parse JSON response
        import json
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        
        topics = json.loads(text.strip())
        return topics
        
    except Exception as e:
        logger.error(f"Error identifying topics: {e}")
        return []


async def generate_topic_questions(class_level, subject, chapter_num, chapter_name, topic, content):
    """Generate questions for a specific topic."""
    
    prompt = f"""You are creating practice questions for students.

Class: {class_level}
Subject: {subject}
Chapter {chapter_num}: {chapter_name}
Topic: {topic['topic_name']}
Description: {topic.get('description', '')}

Reference Content:
{content[:2000]}

Generate 8 questions for this topic:
- 3 Easy questions (basic recall, definitions)
- 3 Medium questions (application, examples)
- 2 Hard questions (analysis, problem-solving)

For EACH question, provide:
1. Question text
2. Correct answer (detailed, 2-3 sentences)
3. Difficulty level (easy/medium/hard)
4. Marks (easy=2, medium=3, hard=5)

Format as JSON array:
[
  {{
    "question_text": "...",
    "correct_answer": "...",
    "difficulty": "easy",
    "marks": 2
  }}
]

Only output the JSON array."""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        # Parse JSON
        import json
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        
        questions = json.loads(text.strip())
        
        # Add topic info to each question
        for q in questions:
            q["topic_id"] = topic["topic_name"].lower().replace(" ", "_")
            q["topic_name"] = topic["topic_name"]
            q["chapter"] = chapter_num
            q["chapter_name"] = chapter_name
        
        return questions
        
    except Exception as e:
        logger.error(f"Error generating questions for topic {topic['topic_name']}: {e}")
        return []


async def store_questions(class_level, subject, chapter_num, chapter_name, topics, questions):
    """Store questions in MongoDB."""
    
    collection = mongodb.db.topic_question_bank
    
    # Group questions by topic
    topic_questions = {}
    for q in questions:
        topic_id = q["topic_id"]
        if topic_id not in topic_questions:
            topic_questions[topic_id] = []
        topic_questions[topic_id].append(q)
    
    # Create document for each topic
    for topic in topics:
        topic_id = topic["topic_name"].lower().replace(" ", "_")
        topic_qs = topic_questions.get(topic_id, [])
        
        if not topic_qs:
            continue
        
        # Count by difficulty
        difficulty_dist = {
            "easy": len([q for q in topic_qs if q["difficulty"] == "easy"]),
            "medium": len([q for q in topic_qs if q["difficulty"] == "medium"]),
            "hard": len([q for q in topic_qs if q["difficulty"] == "hard"])
        }
        
        doc = {
            "class_level": class_level,
            "subject": subject,
            "chapter_number": chapter_num,
            "chapter_name": chapter_name,
            "topic_id": topic_id,
            "topic_name": topic["topic_name"],
            "topic_description": topic.get("description", ""),
            "page_range": topic.get("page_range", ""),
            "questions": topic_qs,
            "total_questions": len(topic_qs),
            "difficulty_distribution": difficulty_dist,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Upsert
        await collection.update_one(
            {
                "class_level": class_level,
                "subject": subject,
                "chapter_number": chapter_num,
                "topic_id": topic_id
            },
            {"$set": doc},
            upsert=True
        )
    
    logger.info(f"Stored questions for {len(topics)} topics in database")


async def main():
    """Main function to generate questions."""
    
    logger.info("🚀 Starting question generation from existing PDFs...")
    
    # Connect to MongoDB
    await mongodb.connect()
    
    # Define chapters to process (Mathematics Class 6)
    chapters = [
        (6, "Mathematics", 1, "Knowing Our Numbers"),
        (6, "Mathematics", 2, "Whole Numbers"),
        (6, "Mathematics", 3, "Playing with Numbers"),
        (6, "Mathematics", 4, "Basic Geometrical Ideas"),
        (6, "Mathematics", 5, "Understanding Elementary Shapes"),
    ]
    
    total_questions = 0
    
    for class_level, subject, chapter_num, chapter_name in chapters:
        count = await generate_questions_for_chapter(class_level, subject, chapter_num, chapter_name)
        if count:
            total_questions += count
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(2)
    
    logger.info(f"\n✅ COMPLETE! Generated {total_questions} total questions")
    logger.info(f"Question bank is ready for testing!")
    
    # Close MongoDB  
    await mongodb.close()


if __name__ == "__main__":
    asyncio.run(main())
