import json, re
from uuid import uuid4, UUID
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..models import User, Session as DBSession, Document, Message
from ..schemas import SessionOut, SessionDetail
from ..utils.file_extract import extract_text_from_file
from ..utils.openai_client import generate_title, detect_language_simple, chat

router = APIRouter(prefix="/session", tags=["sessions"])

# Build model context from DB entities
def build_context(db_sess: DBSession, include_recent: int = 30):
    msgs = []
    msgs.append({"role":"system","content":"You are EduMentorAI, an educational assistant. When asked, respond in the requested language."})
    for d in db_sess.documents:
        excerpt = (d.content or "")[:2000]
        msgs.append({"role":"user","content": f"Document '{d.filename}' content (excerpt):\n{excerpt}"})
    last = sorted(db_sess.messages, key=lambda m: m.created_at)[-include_recent:]
    for m in last:
        msgs.append({"role": m.role, "content": m.content})
    return msgs

@router.get("/list", response_model=list[dict])
def list_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = db.query(DBSession).filter(DBSession.user_id == current_user.id).order_by(DBSession.created_at.desc()).all()
    out = []
    for s in sessions:
        out.append({
            "id": str(s.id),
            "name": s.name,
            "created_at": s.created_at.isoformat(),
            "messages": [
                {
                    "id": str(m.id),
                    "role": m.role, "type": m.type, "content": m.content,
                    "created_at": m.created_at.isoformat()
                } for m in sorted(s.messages, key=lambda x: x.created_at)
            ]
        })
    return out

@router.post("/new")
def create_session(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = DBSession(id=uuid4(), user_id=current_user.id, name="Untitled Session")
    db.add(s)
    db.commit()
    db.refresh(s)
    return {"session_id": str(s.id)}

@router.get("/{sid}", response_model=dict)
def get_session(sid: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = db.query(DBSession).filter(DBSession.id == sid, DBSession.user_id == current_user.id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "id": str(s.id),
        "name": s.name,
        "created_at": s.created_at.isoformat(),
        "messages": [
            {"id": str(m.id), "role": m.role, "type": m.type, "content": m.content, "created_at": m.created_at.isoformat()}
            for m in sorted(s.messages, key=lambda x: x.created_at)
        ],
        "documents": [
            {"id": str(d.id), "filename": d.filename, "content": d.content}
            for d in s.documents
        ]
    }

@router.delete("/{sid}")
def delete_session(sid: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = db.query(DBSession).filter(DBSession.id == sid, DBSession.user_id == current_user.id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(s)
    db.commit()
    return {"message": "Session deleted"}

@router.post("/{sid}/upload")
async def upload_file(
    sid: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None)
):
    s = db.query(DBSession).filter(DBSession.id == sid, DBSession.user_id == current_user.id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    if file:
        content = extract_text_from_file(file)
        if not content:
            raise HTTPException(status_code=400, detail="Could not extract text from file")
        d = Document(id=uuid4(), session_id=s.id, filename=file.filename, content=content)
        db.add(d)
        db.add(Message(id=uuid4(), session_id=s.id, role="assistant", type="upload",
                       content=f"📄 Document '{file.filename}' uploaded successfully.", created_at=datetime.utcnow()))
        db.commit()
        return {"message": "File uploaded successfully", "filename": file.filename}

    if text:
        db.add(Message(id=uuid4(), session_id=s.id, role="user", type="text",
                       content=text.strip(), created_at=datetime.utcnow()))
        db.commit()
        return {"message": "Text message received", "text": text.strip()}

    raise HTTPException(status_code=400, detail="No file or text provided.")

@router.post("/{sid}/message")
def send_message(
    sid: UUID,
    text: str = Form(...),
    lang: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    s = db.query(DBSession).filter(DBSession.id == sid, DBSession.user_id == current_user.id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    if s.name == "Untitled Session" and text.strip():
        s.name = generate_title(text)

    if not lang:
        lang = detect_language_simple(text)

    messages_for_model = build_context(s)
    messages_for_model.append({"role": "user", "content": text})
    if lang == "ar":
        messages_for_model.insert(1, {"role":"system","content":"Please respond in Arabic."})
    else:
        messages_for_model.insert(1, {"role":"system","content":"Please respond in English."})

    try:
        assistant_text = chat(messages_for_model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")

    db.add(Message(id=uuid4(), session_id=s.id, role="user", type="chat", content=text, created_at=datetime.utcnow()))
    db.add(Message(id=uuid4(), session_id=s.id, role="assistant", type="chat", content=assistant_text, created_at=datetime.utcnow()))
    db.commit()
    db.refresh(s)

    return {"reply": assistant_text, "session": {
        "id": str(s.id),
        "name": s.name,
        "messages": [
            {"id": str(m.id), "role": m.role, "type": m.type, "content": m.content, "created_at": m.created_at.isoformat()}
            for m in sorted(s.messages, key=lambda x: x.created_at)
        ],
        "documents": [{"id": str(d.id), "filename": d.filename, "content": d.content} for d in s.documents],
    }}

@router.post("/{sid}/generate/{action}")
def generate_action(
    sid: UUID,
    action: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    text: Optional[str] = Form(""),
    lang: Optional[str] = Form("en"),
    difficulty: Optional[str] = Form(None),
    num_questions: Optional[int] = Form(None),
    report_type: Optional[str] = Form(None)
):
    valid_actions = {"summarize","quiz","flashcards","resources","report","grammar"}
    if action not in valid_actions:
        raise HTTPException(status_code=400, detail="Invalid action")

    s = db.query(DBSession).filter(DBSession.id == sid, DBSession.user_id == current_user.id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    docs_text = "\n\n".join([d.content for d in s.documents])
    if not docs_text and not text:
        raise HTTPException(status_code=400, detail="No documents or additional text provided for this action")

    prompt_map = {
        "summarize": "Summarize the following content clearly and concisely. if there was (Text bar input) use it only without (Documents content)",
        "flashcards": "Generate 5 study flashcards in Q&A format from the content.",
        "resources": "Suggest 3 free online resources to study the topic of the content.",
        "grammar": (
            "Analyze the following text carefully.\n\n"
            "1️⃣ Show the original text with the errors highlighted using Markdown "
            "(e.g., ~~wrong word~~ (error type)).\n"
            "2️⃣ Provide the corrected text (fully rewritten and polished)."
        ),
    }

    if action == "quiz":
        n = num_questions or 5
        base_prompt = (
            f"Create exactly {n} total multiple-choice quiz questions based on the provided material. "
            f"Difficulty: {difficulty or 'medium'}. "
            "If multiple documents are provided, distribute coverage roughly evenly across them, "
            "but the TOTAL number of questions must remain exactly as requested. "
            "Return ONLY a valid JSON array (no code fences, no prose) using this exact shape:\n"
            "[{\"question\": \"...\", \"options\": [\"A) ...\", \"B) ...\", \"C) ...\", \"D) ...\"], \"answer\": \"A\"}]"
        )
    elif action == "report":
        base_prompt = (
            "Generate a {report_type}.\n\n"
            "The learner has completed multiple quizzes. Each quiz contains questions, the learner's answers, "
            "and correctness information. Analyze all quizzes together to assess the learner's overall performance. "
            "Summarize accuracy, identify strengths and weaknesses, and provide constructive feedback with "
            "suggestions for improvement. Use the given data to produce a meaningful report."
        )
    else:
        base_prompt = prompt_map.get(action, "")

    system_lang = "Respond in Arabic." if lang == "ar" else "Respond in English."
    combined = f"{base_prompt}\n\nText bar input:\n{text}\n\nDocuments content:\n{docs_text}"

    messages_for_model = build_context(s)
    messages_for_model.insert(1, {"role":"system", "content": system_lang})
    messages_for_model.append({"role":"user","content": combined})

    try:
        assistant_text = chat(messages_for_model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")

    if action == "quiz":
        n = num_questions or 5
        try:
            m = re.search(r"\[[\s\S]*\]", assistant_text)
            arr = json.loads(m.group(0)) if m else []
            if isinstance(arr, list) and len(arr) > n:
                arr = arr[:n]
            assistant_text = json.dumps(arr, ensure_ascii=False) if isinstance(arr, list) else "[]"
        except Exception:
            assistant_text = "[]"

    if s.name == "Untitled Session":
        s.name = generate_title(text or action)

    db.add(Message(id=uuid4(), session_id=s.id, role="user", type=action, content=(text or action.capitalize()), created_at=datetime.utcnow()))
    db.add(Message(id=uuid4(), session_id=s.id, role="assistant", type=action, content=assistant_text, created_at=datetime.utcnow()))
    db.commit()
    db.refresh(s)

    return {
        "reply": assistant_text,
        "session": {
            "id": str(s.id),
            "name": s.name,
            "messages": [
                {"id": str(m.id), "role": m.role, "type": m.type, "content": m.content, "created_at": m.created_at.isoformat()}
                for m in sorted(s.messages, key=lambda x: x.created_at)
            ],
            "documents": [{"id": str(d.id), "filename": d.filename, "content": d.content} for d in s.documents],
        }
    }
