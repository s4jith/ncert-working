"""
Chat Router - RAG-based chat endpoints with multi-index support.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Literal, List, Optional
from app.models.schemas import ChatRequest, ChatResponse, ErrorResponse
from app.services.rag_service import rag_service
from app.services.enhanced_rag_service import enhanced_rag_service
from app.services.gemini_service import gemini_service
from app.services.openvino_vision_service import get_openvino_vision_service
import logging
import numpy as np
import cv2
from PIL import Image
import io

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chat / RAG"]
)


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    RAG-based chat endpoint with progressive learning.
    
    Retrieves relevant context from Pinecone based on class, subject, and chapter.
    Uses progressive learning to access foundational content from previous classes.
    
    **Modes:**
    - `define`: Clear definitions (quick mode - current + previous class)
    - `elaborate`: Detailed explanation with examples (quick mode)
    """
    try:
        logger.info(f"Chat request: Class {request.class_level}, {request.subject}, Ch. {request.chapter}, Mode: {request.mode}")
        
        # Query RAG system with progressive learning
        answer, source_chunks = rag_service.query_with_rag_progressive(
            query_text=request.highlight_text,
            class_level=request.class_level,
            subject=request.subject,
            chapter=request.chapter,
            mode="quick"  # Use quick mode (current + previous class)
        )
        
        return ChatResponse(
            answer=answer,
            used_mode=request.mode,
            source_chunks=source_chunks
        )
    
    except Exception as e:
        logger.error(f"❌ Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STICK FLOW ENDPOINT ====================

class StickFlowRequest(BaseModel):
    """Request schema for Stick Flow visual diagram generation."""
    highlight_text: str = Field(..., description="Text to create flow diagram for")
    class_level: int = Field(..., ge=5, le=12, description="Class level (5-12)")
    subject: str = Field(..., description="Subject name")
    chapter: int = Field(..., ge=1, description="Chapter number")


class StickFlowResponse(BaseModel):
    """Response schema for Stick Flow."""
    imageUrl: str = Field(..., description="Generated flow diagram image URL")
    description: str = Field(None, description="Optional description of the flow")


@router.post("/stick-flow", response_model=StickFlowResponse)
async def generate_stick_flow(request: StickFlowRequest):
    """
    Generate visual flow diagram using Gemini image generation.
    
    Creates a step-by-step flow diagram of the concept using ONLY textbook content.
    The image will be a clean, attractive visual representation focusing solely on
    the content without extraneous elements.
    """
    try:
        logger.info(f"Stick Flow request: Class {request.class_level}, {request.subject}, Ch. {request.chapter}")
        
        # Get context from RAG
        context = rag_service.retrieve_chapter_context(
            class_level=request.class_level,
            subject=request.subject,
            chapter=request.chapter,
            max_chunks=15
        )
        
        # Build flow diagram generation prompt with strict constraints
        flow_prompt = f"""Create a visual flow diagram for Class {request.class_level} students.

**TEXTBOOK CONTENT:**
{context[:2000]}

**CONCEPT TO VISUALIZE:**
{request.highlight_text}

**STRICT REQUIREMENTS:**
1. Create a clear, step-by-step flow diagram
2. Use ONLY information from the textbook content above
3. Make it visually attractive with:
   - Clear boxes/shapes for each step
   - Arrows showing flow/sequence
   - Simple icons or symbols where appropriate
   - Color coding for different types of steps
4. Keep text minimal - use keywords and short phrases
5. Focus ONLY on the concept - no decorative elements, backgrounds, or unrelated content
6. Make it suitable for Class {request.class_level} students
7. Layout should be vertical or horizontal flowchart style

**OUTPUT:**
A clean, professional flow diagram that a student can use for quick revision.
"""
        
        # Generate image using Gemini (using text-to-image capability)
        # For now, we'll generate a text description and return a placeholder
        # In production, you'd integrate with an actual image generation service
        
        description_prompt = f"""Based on this textbook content:

{context[:1500]}

Create a brief description (2-3 sentences) of how to visualize "{request.highlight_text}" as a flow diagram.
Focus on the steps and connections."""

        description = gemini_service.generate_response(description_prompt)
        
        # TODO: Integrate actual image generation
        # For now, return a placeholder
        image_url = f"https://via.placeholder.com/800x600/6366f1/ffffff?text=Flow+Diagram:+{request.highlight_text[:30]}"
        
        logger.info(f"✅ Stick Flow generated successfully")
        
        return StickFlowResponse(
            imageUrl=image_url,
            description=description
        )
    
    except Exception as e:
        logger.error(f"❌ Stick Flow error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STUDENT CHATBOT ENDPOINT ====================

class StudentChatRequest(BaseModel):
    """Request schema for student chatbot with Quick/DeepDive modes."""
    question: str = Field(..., description="Student's question")
    class_level: int = Field(..., ge=5, le=12, description="Class level (5-12)")
    subject: str = Field(..., description="Subject name")
    chapter: int = Field(..., ge=1, description="Chapter number")
    mode: Literal["quick", "deepdive"] = Field("quick", description="Chat mode: quick (exam-style) or deepdive (comprehensive)")


@router.post("/student", response_model=ChatResponse)
async def student_chatbot(request: StudentChatRequest):
    """
    🎓 Enhanced Student Chatbot with Multi-Index Progressive Learning
    
    **BASIC MODE (Quick)**:
    - Searches current class + 2 recent lower classes
    - Example: Class 10 student → searches Classes 8, 9, 10
    - Fast, focused answers from textbook
    - Perfect for homework help and quick concept clarification
    
    **DEEP DIVE MODE**:
    - Searches ALL classes from fundamentals (Class 5 or earliest) to current
    - Example: Class 10 asking about "line" → builds from Class 5 basics to Class 10
    - Includes web content for comprehensive background
    - Starts with "What is a line?", "Why do we need it?", builds progressively
    - Perfect for thorough understanding and exam preparation
    
    **Progressive Learning Architecture**:
    - Automatically accesses foundational content from earlier classes
    - Builds understanding layer by layer
    - Example: Class 11 Physics on "Force" → uses Class 9-10 Newton's laws as foundation
    """
    try:
        logger.info(f"🎓 Student chat ({request.mode.upper()}): Class {request.class_level}, {request.subject}")
        logger.info(f"   Question: {request.question[:100]}...")
        
        # Convert to new enhanced system
        if request.mode == "quick":
            # BASIC MODE: Current + recent lower classes (textbook only)
            answer, source_chunks_list = enhanced_rag_service.answer_question_basic(
                question=request.question,
                subject=request.subject,
                student_class=request.class_level,
                chapter=request.chapter
            )
            
            # Convert chunk format for compatibility
            source_chunks = [chunk.get('text', '') for chunk in source_chunks_list]
            
            # Check if answer is meaningful
            if not source_chunks or len(source_chunks) < 2:
                return ChatResponse(
                    answer=f"I couldn't find enough information in your textbooks. Try asking about specific topics covered in Chapter {request.chapter} of {request.subject}!",
                    used_mode="quick",
                    source_chunks=[]
                )
        
        else:  # deepdive mode
            # DEEP DIVE MODE: ALL prerequisite classes + web content
            answer, source_chunks_list = enhanced_rag_service.answer_question_deepdive(
                question=request.question,
                subject=request.subject,
                student_class=request.class_level,
                chapter=request.chapter
            )
            
            # Convert chunk format
            source_chunks = [chunk.get('text', '') for chunk in source_chunks_list]
        
        logger.info(f"✅ Answer generated: {len(answer)} chars, {len(source_chunks)} sources")
        
        return ChatResponse(
            answer=answer,
            used_mode=request.mode,
            source_chunks=source_chunks
        )
    
    except Exception as e:
        logger.error(f"❌ Student chat error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ==================== IMAGE-BASED CHAT ENDPOINT ====================

class ImageChatResponse(BaseModel):
    """Response schema for image-based chat."""
    answer: str = Field(..., description="RAG-generated answer")
    used_mode: str = Field(..., description="Mode used (quick/deepdive)")
    source_chunks: List[str] = Field(default=[], description="Source text chunks used")
    image_analysis: dict = Field(..., description="Image analysis metadata")


# Constants for image validation
MAX_IMAGE_SIZE_MB = 5
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/jpg", "image/webp"]


@router.post("/image", response_model=ImageChatResponse)
async def image_chat(
    image: UploadFile = File(..., description="Image file (jpg/png, max 5MB)"),
    class_level: int = Form(..., ge=5, le=12, description="Class level (5-12)"),
    subject: str = Form(..., description="Subject name"),
    mode: str = Form("quick", description="Chat mode: quick or deepdive"),
    chapter: int = Form(1, ge=1, description="Chapter number"),
    user_query: Optional[str] = Form(None, description="Optional user text to accompany image")
):
    """
    🖼️ Image-Based Chat: Extract text from student photos → Generate RAG answer
    
    Students can upload photos of:
    - Textbook pages
    - Diagrams and charts
    - Handwritten questions
    - Mathematical formulas
    
    **Flow:**
    1. Validate and preprocess image
    2. Extract text using Intel OpenVINO OCR
    3. Classify image type (textbook/diagram/handwritten/formula)
    4. Generate query from extracted text AND user input
    5. Run RAG pipeline for answer generation
    
    **Supported formats:** JPEG, PNG, WebP (max 5MB)
    """
    try:
        logger.info(f"🖼️ Image chat request: Class {class_level}, {subject}, Ch. {chapter}, Mode: {mode}, Query: {user_query}")
        
        # 1. Validate image file
        if image.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image type: {image.content_type}. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}"
            )
        
        # Read image content
        image_bytes = await image.read()
        
        # Check file size
        if len(image_bytes) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"Image too large. Maximum size: {MAX_IMAGE_SIZE_MB}MB"
            )
        
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty image file")
        
        logger.info(f"   Image: {image.filename}, {len(image_bytes) / 1024:.1f}KB, {image.content_type}")
        
        # 2. Convert to OpenCV numpy array
        try:
            # Use PIL to open image, then convert to numpy array
            pil_image = Image.open(io.BytesIO(image_bytes))
            pil_image = pil_image.convert("RGB")  # Ensure RGB format
            image_array = np.array(pil_image)
            logger.info(f"   Converted to array: {image_array.shape}")
        except Exception as e:
            logger.error(f"Failed to parse image: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to parse image: {str(e)}")
        
        # 3. Analyze image with OpenVINO Vision Service
        vision_service = get_openvino_vision_service()
        image_analysis = vision_service.analyze_image(image_array)
        
        ocr_text = image_analysis.get("text", "").strip()
        image_type = image_analysis.get("image_type", "unknown")
        
        logger.info(f"   OCR extracted: {len(ocr_text)} chars, Type: {image_type}")
        
        # 4. Generate query from OCR text AND user input
        
        # If we have user query, we can proceed even with little OCR text
        if (not ocr_text or len(ocr_text) < 10) and not user_query:
            # Not enough text AND no user query - provide guidance
            return ImageChatResponse(
                answer="I couldn't extract enough text from this image. Please try:\n"
                       "1. Take a clearer photo with better lighting\n"
                       "2. Make sure the text is in focus\n"
                       "3. Avoid shadows and glare\n"
                       "Or, you can type your question directly along with the image!",
                used_mode=mode,
                source_chunks=[],
                image_analysis=image_analysis
            )
        
        # Construct the final query
        query_parts = []
        if user_query:
            query_parts.append(f"User Question: {user_query}")
        
        if ocr_text:
            if image_type == "formula":
                query_parts.append(f"Image Content (Formula): {ocr_text}")
            elif image_type == "diagram":
                query_parts.append(f"Image Content (Diagram labels): {ocr_text}")
            elif image_type == "handwritten":
                query_parts.append(f"Image Content (Handwritten): {ocr_text}")
            else:
                query_parts.append(f"Image Content (Textbook): {ocr_text}")
        
        query = "\n\n".join(query_parts)
        
        # If we only have user query (OCR failed), treat it as a normal question but with image context awareness
        if not ocr_text and user_query:
            query = f"User Question about uploaded image: {user_query}\n(Note: OCR could not extract text from the image)"

        logger.info(f"   Generated query: {query[:100]}...")
        
        # 5. Run RAG pipeline
        if mode == "quick":
            answer, source_chunks_list = enhanced_rag_service.answer_question_basic(
                question=query,
                subject=subject,
                student_class=class_level,
                chapter=chapter
            )
        else:  # deepdive
            answer, source_chunks_list = enhanced_rag_service.answer_question_deepdive(
                question=query,
                subject=subject,
                student_class=class_level,
                chapter=chapter
            )
        
        # Convert chunk format for response
        source_chunks = [chunk.get('text', '') for chunk in source_chunks_list]
        
        logger.info(f"✅ Image chat complete: {len(answer)} chars, {len(source_chunks)} sources")
        
        return ImageChatResponse(
            answer=answer,
            used_mode=mode,
            source_chunks=source_chunks,
            image_analysis=image_analysis
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Image chat error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
