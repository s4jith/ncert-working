"""
Chat API Routes - Main chatbot endpoint with RAG
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.config import settings
from app.api.auth import get_current_active_user
from app.db.models import (
    ChatRequest, ChatResponse, ChatHistoryResponse, 
    ChatMessage, ChatSource, LLMProvider
)
from app.db.mongodb import save_chat, get_chat_history, set_cached_response, invalidate_cache
from app.services.rag_service import get_rag_service
from app.services.llm_service import LLMServiceFactory

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Main chat endpoint with RAG pipeline
    
    Features:
    - Grade-specific retrieval
    - Multilingual support
    - Citation tracking
    - Response caching
    """
    start_time = datetime.utcnow()
    user_id = str(current_user["_id"])
    
    # Generate conversation ID if not provided
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    try:
        # Get LLM service first
        llm_service = LLMServiceFactory.get_service(request.model)
        
        context = ""
        sources = []
        is_in_scope = True
        
        # Try RAG pipeline if Pinecone is available
        try:
            rag_service = get_rag_service()
            
            # Retrieve context and sources
            context, sources, is_in_scope = await rag_service.process_query(
                query=request.message,
                grade=request.grade or current_user.get("grade"),
                subject=request.subject,
                language=request.language,
                conversation_id=conversation_id
            )
            
            # Build prompt with context
            prompt = rag_service.build_prompt(
                query=request.message,
                context=context,
                language=request.language
            )
        except RuntimeError as e:
            # Pinecone not initialized - use direct LLM response
            logger.warning(f"RAG unavailable, using direct LLM: {e}")
            prompt = f"""You are a helpful NCERT tutor specializing in Mathematics, Physics, Chemistry, and other subjects for students in grades 5-12.

Question: {request.message}

Guidelines:
- For MATH: Show step-by-step solution with formulas
- For PHYSICS: Include relevant formulas and units
- For CHEMISTRY: Write chemical equations properly
- Explain in simple, student-friendly language
- If you don't know something, say so honestly

Your Answer:"""
        except Exception as e:
            # Other RAG errors - log and continue with simple prompt
            logger.warning(f"RAG error, falling back: {e}")
            prompt = f"""You are a helpful NCERT tutor specializing in Mathematics, Physics, Chemistry, and other subjects for students in grades 5-12.

Question: {request.message}

Guidelines:
- For MATH: Show step-by-step solution with formulas
- For PHYSICS: Include relevant formulas and units  
- For CHEMISTRY: Write chemical equations properly
- Explain in simple, student-friendly language

Your Answer:"""
        
        # Generate response with LLM
        response_text = await llm_service.generate(prompt)
        
        # Calculate response time
        response_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Save to database
        await save_chat(
            user_id=user_id,
            question=request.message,
            answer=response_text,
            conversation_id=conversation_id,
            model_used=request.model.value,
            sources=[s for s in sources],
            language=request.language,
            response_time_ms=response_time_ms
        )
        
        # Cache if in-scope with good sources
        if is_in_scope and len(sources) >= 1:
            try:
                rag_service = get_rag_service()
                question_hash = rag_service._hash_question(
                    request.message, 
                    request.grade, 
                    request.subject
                )
                await set_cached_response(
                    question_hash=question_hash,
                    question=request.message,
                    answer=response_text,
                    sources=sources
                )
            except Exception:
                pass  # Caching failed, continue anyway
        
        # Format sources for response
        formatted_sources = [
            ChatSource(
                type=s.get("type", "ncert_textbook"),
                name=s.get("name", ""),
                class_num=s.get("class"),
                subject=s.get("subject"),
                chapter=s.get("chapter"),
                page=s.get("page"),
                relevance=s.get("relevance")
            )
            for s in sources
        ]
        
        return ChatResponse(
            message=response_text,
            sources=formatted_sources,
            images=[],
            model_used=request.model,
            language_detected=request.language,
            response_time_ms=response_time_ms,
            cached=False,
            conversation_id=conversation_id,
            citation_count=len(sources)
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=ChatHistoryResponse)
async def get_history(
    conversation_id: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
    current_user: dict = Depends(get_current_active_user)
):
    """Get user's chat history"""
    user_id = str(current_user["_id"])
    skip = (page - 1) * per_page
    
    messages = await get_chat_history(
        user_id=user_id,
        conversation_id=conversation_id,
        limit=per_page,
        skip=skip
    )
    
    # Format messages
    formatted = []
    for msg in messages:
        # Add user question
        formatted.append(ChatMessage(
            role="user",
            content=msg.get("question", ""),
            timestamp=msg.get("created_at", datetime.utcnow())
        ))
        # Add assistant answer
        formatted.append(ChatMessage(
            role="assistant",
            content=msg.get("answer", ""),
            timestamp=msg.get("created_at", datetime.utcnow()),
            sources=[ChatSource(**s) for s in msg.get("sources", [])]
        ))
    
    return ChatHistoryResponse(
        messages=formatted,
        total=len(messages) * 2,
        page=page,
        per_page=per_page
    )


@router.post("/report")
async def report_wrong_answer(
    question_hash: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Report a wrong answer to invalidate cache"""
    await invalidate_cache(question_hash)
    return {"status": "success", "message": "Answer reported and cache invalidated"}


@router.websocket("/stream")
async def chat_stream(websocket: WebSocket):
    """WebSocket endpoint for streaming chat responses"""
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            query = data.get("message", "")
            model = LLMProvider(data.get("model", "gemini"))
            grade = data.get("grade")
            subject = data.get("subject")
            language = data.get("language", "en")
            
            # Get RAG context
            rag_service = get_rag_service()
            context, sources, is_in_scope = await rag_service.process_query(
                query=query,
                grade=grade,
                subject=subject,
                language=language
            )
            
            # Build prompt
            prompt = rag_service.build_prompt(
                query=query,
                context=context,
                language=language
            )
            
            # Send sources first
            await websocket.send_json({
                "type": "sources",
                "sources": sources
            })
            
            # Stream LLM response
            llm_service = LLMServiceFactory.get_service(model)
            
            await websocket.send_json({"type": "start"})
            
            full_response = ""
            async for chunk in llm_service.generate_stream(prompt):
                full_response += chunk
                await websocket.send_json({
                    "type": "chunk",
                    "content": chunk
                })
            
            await websocket.send_json({
                "type": "end",
                "full_response": full_response
            })
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1000)
