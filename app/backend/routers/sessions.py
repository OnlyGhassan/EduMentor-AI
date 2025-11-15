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

# @router.get("/sessions")
# def sessions_alias(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
#     sessions = db.query(DBSession).filter(DBSession.user_id == current_user.id).all()
#     return [
#         {
#             "id": str(s.id),
#             "name": s.name,
#             "created_at": s.created_at.isoformat()
#         }
#         for s in sessions
#     ]


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
    text_grammar: Optional[str] = Form(None),
    report_type: Optional[str] = Form(None)
):
    valid_actions = {"summarize","quiz","flashcards","resources","report","grammar"}
    if action not in valid_actions:
        raise HTTPException(status_code=400, detail="Invalid action")

    s = db.query(DBSession).filter(DBSession.id == sid, DBSession.user_id == current_user.id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    docs_text = "\n\n".join([d.content for d in s.documents])
    # if not docs_text and not text:
    if action != "grammar" and not docs_text and not text:
        raise HTTPException(status_code=400, detail="No documents or additional text provided for this action")
    

    prompt_map = {
        "summarize": "Summarize the following content clearly and concisely. if there was (Text bar input) use it only without (Documents content)",
        "flashcards": "Generate 5 study flashcards in Q&A format from the content.",
        "resources": "Suggest 3 free online resources to study the topic of the content.",
        
    }

    if action == "quiz":
        n = num_questions or 5
        base_prompt = (
            f"Create exactly {n} total multiple-choice quiz questions based on the provided material. "
            f"Difficulty: {difficulty or 'medium'}. "
            "If multiple documents are provided, distribute coverage roughly evenly across them, "
            "but the TOTAL number of questions must remain exactly as requested. "
            "Return ONLY a valid JSON array (no code fences, no prose) using this exact shape:\n"
            "[{\"question\": \"...\", \"options\": [\"A) ...\", \"B) ...\", \"C) ...\", \"D) ...\"], \"answer\": \"A\"}]\n"
            "Where 'answer' is just the correct LETTER (A, B, C, or D)."
        )
    elif action == "report":
        base_prompt = (
            "Generate a {report_type}.\n\n"
            "The learner has completed multiple quizzes. Each quiz contains questions, the learner's answers, "
            "and correctness information. Analyze all quizzes together to assess the learner's overall performance. "
            "Summarize accuracy, identify strengths and weaknesses, and provide constructive feedback with "
            "suggestions for improvement. Use the given data to produce a meaningful report."
        )
    elif action == "grammar":
        if not text_grammar:
            raise HTTPException(status_code=400, detail="No text provided for grammar check")

        base_prompt = (
            f"Analyze the following English text for grammar, spelling, and clarity errors:\n\n{text_grammar}\n\n"
            "Please provide:\n"
            "1️⃣ The original text with errors highlighted using Markdown "
            "(e.g., ~~wrong word~~ (error type)).\n"
            "2️⃣ The corrected version (fully rewritten and polished)."
        )
    else:
        base_prompt = prompt_map.get(action, "")

    system_lang = "Respond in Arabic." if lang == "ar" else "Respond in English."

    
    if action == "grammar":
        combined = base_prompt
    else:
        # --- Combine all content for model ---
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





@router.post("/{sid}/transcribe")
async def transcribe_audio(
    sid: UUID,
    file: UploadFile = File(...),
    lang: Optional[str] = Form("en"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    s = db.query(DBSession).filter(DBSession.id == sid, DBSession.user_id == current_user.id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    temp_path = "temp_audio.wav"
    audio_bytes = await file.read()
    with open(temp_path, "wb") as f:
        f.write(audio_bytes)

    try:
        from ..utils.openai_client import client
        with open(temp_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=f,
                language=lang or "en"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
    finally:
        import os
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # db.add(Message(
    #     id=uuid4(),
    #     session_id=s.id,
    #     role="assistant",
    #     type="transcription",
    #     content=transcript.text,
    #     created_at=datetime.utcnow()
    # ))
    # db.commit()

    return {"transcription": transcript.text}





# @router.post("/{sid}/transcribe")
# async def transcribe_audio(
#     sid: UUID,
#     file: UploadFile = File(...),
#     lang: Optional[str] = Form("en"),
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     import os
#     from pydub import AudioSegment
#     from tempfile import NamedTemporaryFile

#     s = db.query(DBSession).filter(DBSession.id == sid, DBSession.user_id == current_user.id).first()
#     if not s:
#         raise HTTPException(status_code=404, detail="Session not found")

#     # Save uploaded Streamlit file to temp path
#     audio_bytes = await file.read()
#     with NamedTemporaryFile(delete=False, suffix=".wav") as temp_in:
#         temp_in.write(audio_bytes)
#         temp_in_path = temp_in.name

#     # Normalize & re-encode to standard mono 16kHz PCM WAV
#     temp_out_path = temp_in_path.replace(".wav", "_norm.wav")
#     try:
#         sound = AudioSegment.from_file(temp_in_path)
#         sound = sound.set_frame_rate(16000).set_channels(1)
#         sound.export(temp_out_path, format="wav")
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"Audio format error: {e}")

#     try:
#         from ..utils.openai_client import client
#         with open(temp_out_path, "rb") as f:
#             transcript = client.audio.transcriptions.create(
#                 model="gpt-4o-transcribe",
#                 file=f,
#                 language=lang or "en"
#             )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
#     finally:
#         for p in (temp_in_path, temp_out_path):
#             if os.path.exists(p):
#                 os.remove(p)

#     # Store transcription message in DB
#     # db.add(Message(
#     #     id=uuid4(),
#     #     session_id=s.id,
#     #     role="assistant",
#     #     type="transcription",
#     #     content=transcript.text,
#     #     created_at=datetime.utcnow()
#     # ))
#     # db.commit()

#     return {"transcription": transcript.text}


# @router.post("/{sid}/transcribe")
# async def transcribe_audio(
#     sid: UUID,
#     file: UploadFile = File(...),
#     lang: Optional[str] = Form("en"),
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     s = db.query(DBSession).filter(DBSession.id == sid, DBSession.user_id == current_user.id).first()
#     if not s:
#         raise HTTPException(status_code=404, detail="Session not found")

#     input_path = "temp_input"
#     output_path = "temp_audio.wav"
#     audio_bytes = await file.read()
#     with open(input_path, "wb") as f:
#         f.write(audio_bytes)

#     # Convert to proper mono 16kHz WAV
#     sound = AudioSegment.from_file(input_path)
#     sound = sound.set_frame_rate(16000).set_channels(1)
#     sound.export(output_path, format="wav")

#     try:
#         from ..utils.openai_client import client
#         with open(output_path, "rb") as f:
#             transcript = client.audio.transcriptions.create(
#                 model="gpt-4o-transcribe",
#                 file=f,
#                 language=lang or "en"
#             )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
#     finally:
#         for p in (input_path, output_path):
#             if os.path.exists(p):
#                 os.remove(p)

#     # db.add(Message(
#     #     id=uuid4(),
#     #     session_id=s.id,
#     #     role="assistant",
#     #     type="transcription",
#     #     content=transcript.text,
#     #     created_at=datetime.utcnow()
#     # ))
#     # db.commit()

#     return {"transcription": transcript.text}






# @router.post("/{sid}/transcribe")
# async def transcribe_audio(
#     sid: UUID,
#     file: UploadFile = File(...),
#     lang: Optional[str] = Form("en"),  # 👈 allow manual language override
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     s = db.query(DBSession).filter(DBSession.id == sid, DBSession.user_id == current_user.id).first()
#     if not s:
#         raise HTTPException(status_code=404, detail="Session not found")

#     # Save temp audio
#     temp_path = "temp_audio.wav"
#     audio_bytes = await file.read()
#     with open(temp_path, "wb") as f:
#         f.write(audio_bytes)

#     try:
#         from ..utils.openai_client import client
#         with open(temp_path, "rb") as f:
#             transcript = client.audio.transcriptions.create(
#                 model="gpt-4o-transcribe",
#                 file=f,
#                 language=lang or "en"  # 👈 enforce or default to English
#             )
#             print(f)
#             print(transcript.text)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
#     finally:
#         import os
#         if os.path.exists(temp_path):
#             os.remove(temp_path)

#     # Save transcript
#     # db.add(Message(
#     #     id=uuid4(),
#     #     session_id=s.id,
#     #     role="assistant",
#     #     type="transcription",
#     #     content=transcript.text,
#     #     created_at=datetime.utcnow()
#     # ))
#     # db.commit()

#     return {"transcription": transcript.text, "language": lang or "en"}





# @router.post("/{sid}/transcribe")
# async def transcribe_audio(
#     sid: UUID,
#     file: UploadFile = File(...),
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     s = db.query(DBSession).filter(DBSession.id == sid, DBSession.user_id == current_user.id).first()
#     if not s:
#         raise HTTPException(status_code=404, detail="Session not found")

#     # Save and transcribe audio file
#     audio_bytes = await file.read()
#     temp_path = "temp_audio.wav"
#     with open(temp_path, "wb") as f:
#         f.write(audio_bytes)

#     try:
#         from ..utils.openai_client import client
#         with open(temp_path, "rb") as f:
#             transcript = client.audio.transcriptions.create(
#                 model="gpt-4o-transcribe",
#                 file=f
#             )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

#     # Save transcript as assistant message
#     # db.add(Message(
#     #     id=uuid4(),
#     #     session_id=s.id,
#     #     role="assistant",
#     #     type="transcription",
#     #     content=transcript.text,
#     #     created_at=datetime.utcnow()
#     # ))
#     # db.commit()

#     return {"transcription": transcript.text}
