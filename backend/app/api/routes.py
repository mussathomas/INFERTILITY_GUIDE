import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.service import authenticate_user, create_user, get_user_by_email
from app.database import get_db
from app.models import Conversation, Message, User
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    MessageResponse,
    SourceCitation,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.auth.service import create_access_token
from app.rag.engine import get_rag_engine

router = APIRouter()

MEDICAL_DISCLAIMER = (
    "This information is for educational purposes only and does not constitute medical advice. "
    "Always consult a qualified fertility specialist or healthcare provider for diagnosis and treatment."
)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = create_user(db, payload.email, payload.full_name, payload.password)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


def _parse_sources(raw: str | None) -> list[SourceCitation] | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return [SourceCitation(**item) for item in data]
    except (json.JSONDecodeError, TypeError):
        return None


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())
        .all()
    )
    result = []
    for conv in conversations:
        messages = [
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                sources=_parse_sources(m.sources),
                created_at=m.created_at,
            )
            for m in conv.messages
        ]
        result.append(
            ConversationResponse(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at,
                messages=messages,
            )
        )
    return result


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == payload.conversation_id, Conversation.user_id == current_user.id)
            .first()
        )
        if not conversation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    else:
        title = payload.message[:60] + ("..." if len(payload.message) > 60 else "")
        conversation = Conversation(user_id=current_user.id, title=title)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    user_message = Message(conversation_id=conversation.id, role="user", content=payload.message)
    db.add(user_message)

    engine = get_rag_engine()
    reply, sources = engine.generate_response(payload.message)
    sources_json = json.dumps(sources)

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=reply,
        sources=sources_json,
    )
    db.add(assistant_message)
    db.commit()

    return ChatResponse(
        conversation_id=conversation.id,
        reply=reply,
        sources=[SourceCitation(**s) for s in sources],
        disclaimer=MEDICAL_DISCLAIMER,
    )


@router.post("/knowledge-base/ingest")
def ingest_knowledge_base(current_user: User = Depends(get_current_user)):
    engine = get_rag_engine()
    result = engine.ingest_knowledge_base()
    return {"status": "ok", **result}
