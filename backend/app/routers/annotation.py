"""
Annotation Router - Text annotation with AI assistance (Define, Elaborate, Flow)

Supports multilingual input/output - responds in the same language as the selected text.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Literal
from app.services.enhanced_rag_service import enhanced_rag_service
from app.services.gemini_service import gemini_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/annotation",
    tags=["Annotation"]
)


def detect_text_language(text: str) -> str:
    """Detect language of the selected text and return language instruction."""
    try:
        from app.services.openvino_multilingual_service import multilingual_service
        lang, confidence = multilingual_service.detect_language_with_confidence(text)
        
        lang_names = {
            "hi": "Hindi",
            "ur": "Urdu",
            "ta": "Tamil",
            "te": "Telugu",
            "bn": "Bengali",
            "mr": "Marathi",
            "gu": "Gujarati",
            "kn": "Kannada",
            "ml": "Malayalam",
            "pa": "Punjabi",
            "ar": "Arabic",
            "en": "English"
        }
        
        if lang != "en" and confidence > 0.5:
            lang_name = lang_names.get(lang, lang.upper())
            return f"\n\n**IMPORTANT: The input text is in {lang_name}. You MUST respond entirely in {lang_name} using the same script.**"
        return ""
    except:
        return ""


class AnnotationRequest(BaseModel):
    """Request schema for annotation AI actions."""
    selected_text: str = Field(..., description="Text selected by user for annotation")
    action: Literal["define", "elaborate", "stick_flow"] = Field(..., description="AI action to perform")
    class_level: int = Field(..., ge=5, le=12, description="Student's class level")
    subject: str = Field(..., description="Subject name (Mathematics, Physics, etc.)")
    chapter: int | None = Field(None, ge=1, description="Optional chapter number")


class AnnotationResponse(BaseModel):
    """Response schema for annotation."""
    answer: str = Field(..., description="AI-generated response")
    action_type: str = Field(..., description="Type of action performed")
    source_count: int = Field(..., description="Number of sources used")


@router.post("/", response_model=AnnotationResponse)
async def process_annotation(request: AnnotationRequest):
    """
    🎯 Process annotation request with AI assistance.
    
    **Actions:**
    - `define`: Quick, accurate definition from textbook
    - `elaborate`: Detailed explanation with examples  
    - `stick_flow`: Text-based flow diagram showing concept breakdown
    
    **Cost-Efficient Design:**
    - Uses RAG for context (reduces Gemini tokens)
    - Targeted prompts for specific actions
    - No image generation (text-based flows)
    
    **Edge Case Handling:**
    - Class 11-12: Limited content available (graceful fallback)
    - Missing content: Searches earlier classes for foundation
    - No matches: Uses Gemini general knowledge with disclaimer
    """
    try:
        logger.info(f"📝 Annotation request: {request.action.upper()} for '{request.selected_text[:50]}...'")
        logger.info(f"   Class {request.class_level}, {request.subject}")
        
        # Detect input language for multilingual response
        lang_instruction = detect_text_language(request.selected_text)
        if lang_instruction:
            logger.info(f"   🌐 Detected non-English input, will respond in same language")
        
        # EDGE CASE: Check class availability
        # Currently we have comprehensive data for Classes 5-10
        # Classes 11-12 have limited content
        if request.class_level > 10:
            logger.warning(f"⚠️ Class {request.class_level} requested (limited content available)")
            # Don't block the request - let the RAG system try to find content
            # If not found, it will fall back to general knowledge
        
        # Get relevant context from textbook using RAG
        if request.action == "define":
            # Quick mode: Current + 2 previous classes WITH lower LLM reuse threshold
            answer, source_chunks = enhanced_rag_service.answer_annotation_basic(
                question=f"Define: {request.selected_text}",
                subject=request.subject,
                student_class=request.class_level,
                chapter=request.chapter
            )
            
            # Extract concise definition
            if source_chunks:
                context = "\n\n".join([chunk.get('text', '')[:500] for chunk in source_chunks[:3]])
                
                prompt = f"""Based on the textbook content below, provide a clear, concise definition of "{request.selected_text}" for a Class {request.class_level} student.

**Textbook Content:**
{context}

**Instructions:**
1. Start with a one-line definition
2. Add 2-3 bullet points explaining key aspects
3. Use simple language appropriate for Class {request.class_level}
4. Keep it under 150 words
5. Use ONLY the textbook content provided

**Format:**
**Definition:** [One clear sentence]

**Key Points:**
• [Point 1]
• [Point 2]  
• [Point 3]{lang_instruction}"""
                
                answer = gemini_service.generate_response(prompt)
            # Note: If no sources, answer_annotation_basic already provided fallback answer
        
        elif request.action == "elaborate":
            # Deep dive mode: Comprehensive explanation
            answer, source_chunks = enhanced_rag_service.answer_question_deepdive(
                question=f"Explain in detail: {request.selected_text}",
                subject=request.subject,
                student_class=request.class_level,
                chapter=request.chapter
            )
            
            # Generate detailed explanation
            if source_chunks:
                context = "\n\n".join([chunk.get('text', '')[:800] for chunk in source_chunks[:5]])
                
                prompt = f"""Based on the textbook content below, provide a detailed explanation of "{request.selected_text}" for a Class {request.class_level} student.

**Textbook Content:**
{context}

**Instructions:**
1. Start with a brief introduction
2. Explain the concept step-by-step
3. Include at least 2 examples
4. Mention real-world applications if relevant
5. Use simple, engaging language
6. Keep it under 400 words
7. Use ONLY the textbook content provided

**Structure:**
**Introduction:** [What is it?]

**Explanation:** [Detailed breakdown]

**Examples:**
1. [Example 1]
2. [Example 2]

**Application:** [Why it matters]{lang_instruction}"""
                
                answer = gemini_service.generate_response(prompt)
            else:
                answer = f"No detailed information found in the book. '{request.selected_text}' might require additional resources beyond your Class {request.class_level} {request.subject} textbook."
        
        elif request.action == "stick_flow":
            # Generate text-based flow diagram WITH lower LLM reuse threshold
            answer, source_chunks = enhanced_rag_service.answer_annotation_basic(
                question=f"Explain the flow/process of: {request.selected_text}",
                subject=request.subject,
                student_class=request.class_level,
                chapter=request.chapter
            )
            
            if source_chunks:
                context = "\n\n".join([chunk.get('text', '')[:600] for chunk in source_chunks[:4]])
                
                prompt = f"""Based on the textbook content below, create a clear TEXT-BASED flow diagram for "{request.selected_text}" suitable for a Class {request.class_level} student.

**Textbook Content:**
{context}

**Instructions:**
1. Create a step-by-step flow using text and arrows
2. Use these symbols: ↓ → ← ↑ ⟶ ⟵ 
3. Keep each step brief (5-8 words max)
4. Show relationships and progression clearly
5. Use boxes made with text characters
6. Make it easy to copy-paste and study from
7. Limit to 5-8 major steps
8. Use ONLY information from the textbook content

**Format Example:**
```
┌─────────────────────┐
│   Starting Point    │
└─────────────────────┘
          ↓
┌─────────────────────┐
│   Key Process       │
└─────────────────────┘
          ↓
    ┌─────┴─────┐
    ↓           ↓
┌───────┐   ┌───────┐
│ Path A│   │ Path B│
└───────┘   └───────┘
```

Generate a similar flow diagram for "{request.selected_text}":{lang_instruction}"""
                
                answer = gemini_service.generate_response(prompt)
            else:
                answer = f"""No flow information found in the book.

Try asking about:
• Specific processes or procedures
• Step-by-step concepts
• Sequential topics

Current search: "{request.selected_text}" in Class {request.class_level} {request.subject}"""
        
        logger.info(f"✅ Annotation processed: {len(answer)} chars, {len(source_chunks)} sources")
        
        return AnnotationResponse(
            answer=answer,
            action_type=request.action,
            source_count=len(source_chunks)
        )
    
    except Exception as e:
        logger.error(f"❌ Annotation error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-define")
async def quick_define(
    text: str = Query(..., description="Text to define"),
    class_level: int = Query(..., ge=5, le=12),
    subject: str = Query(..., description="Subject name")
):
    """
    ⚡ Ultra-fast definition endpoint (optimized for speed).
    
    Returns just the definition without extra processing.
    Perfect for quick lookups while reading.
    """
    try:
        # Use basic RAG with minimal chunks
        answer, source_chunks = enhanced_rag_service.answer_question_basic(
            question=f"What is {text}?",
            subject=subject,
            student_class=class_level,
            chapter=None
        )
        
        if source_chunks:
            # Quick definition extraction
            context = source_chunks[0].get('text', '')[:300]
            
            prompt = f"""Give a one-sentence definition of "{text}" based on this textbook excerpt:

{context}

Definition:"""
            
            definition = gemini_service.generate_response(prompt)
            
            return {"definition": definition.strip()}
        else:
            return {"definition": f"Term '{text}' not found in textbook."}
    
    except Exception as e:
        logger.error(f"Quick define error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
