"""
Streamlit frontend for EduMentorAI (ChatGPT-like UI)
Run with: `streamlit run streamlit_frontend.py`
Make sure backend is running at http://localhost:8000
"""

import streamlit as st
import requests
from streamlit.components.v1 import html as st_html
#import streamlit.components.v1 as components
import hashlib
import re, json
import time
from typing import Optional
import os


#BACKEND_BASE = "http://localhost:8000"
# BACKEND_BASE = "http://api:5000"
BACKEND_BASE = os.getenv("BACKEND_BASE_URL", "http://api:5000")
st.set_page_config(page_title="EduMentorAI", layout="wide", initial_sidebar_state="auto")

# ---------- Sidebar: sessions + language ----------
logo_url = "logo2.png"
st.sidebar.image(logo_url)






# --- Session helpers ---
def set_auth(token: str, user: dict):
    st.session_state["token"] = token
    st.session_state["user"] = user

def clear_auth():
    for k in ("token", "user"):
        if k in st.session_state:
            del st.session_state[k]

def get_token() -> Optional[str]:
    return st.session_state.get("token")

def api_request(method: str, path: str, **kwargs):
    """Calls the FastAPI backend and automatically attaches Bearer token if present."""
    headers = kwargs.pop("headers", {})
    token = get_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"{BACKEND_BASE.rstrip('/')}/{path.lstrip('/')}"
    resp = requests.request(method, url, headers=headers, **kwargs)
    # Raise nice error for debugging
    if not resp.ok:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise RuntimeError(f"{method} {path} failed [{resp.status_code}]: {detail}")
    return resp

# --- UI labels ---
TXT = {
    "title": "EduMentorAI",
    "hello": "Hello",
    "login": "Log in",
    "logout": "Log out",
    "register": "Register",
    "email": "Email",
    "name": "Name",
    "password": "Password",
    "or": "— or —",
    "you_are_in": "You are logged in as",
    "list_sessions": "List My Sessions",
    "create_session": "Create a Session",
    "session_created": "Session created!",
}

TXT_AR = {
    "title": "إديومينتورAI",
    "hello": "مرحبًا",
    "login": "تسجيل الدخول",
    "logout": "تسجيل الخروج",
    "register": "إنشاء حساب",
    "email": "البريد الإلكتروني",
    "name": "الاسم",
    "password": "كلمة المرور",
    "or": "— أو —",
    "you_are_in": "تم تسجيل دخولك باسم",
    "list_sessions": "عرض جلساتي",
    "create_session": "إنشاء جلسة",
    "session_created": "تم إنشاء الجلسة!",
}
L =  TXT

# st.set_page_config(page_title=L["title"], layout="wide")
# st.title(L["title"])

# # --- Auth sidebar ---
# with st.sidebar:
#     if "token" not in st.session_state:
#         st.subheader(L["login"])

#         # Login form
#         with st.form("login_form", clear_on_submit=False):
#             email = st.text_input(L["email"])
#             password = st.text_input(L["password"], type="password")
#             do_login = st.form_submit_button(L["login"])
#         if do_login:
#             # FastAPI expects OAuth2PasswordRequestForm (form encoded) with username/password fields.
#             # We pass email into "username".
#             try:
#                 resp = api_request(
#                     "POST",
#                     "/auth/login",
#                     data={"username": email, "password": password},
#                 )
#                 token = resp.json()["access_token"]
#                 print(token)
#                 # Get current user using /auth/me
#                 st.session_state["token"] = token #####################################
#                 print(st.session_state["token"])
#                 me = api_request("GET", "/auth/me").json() ##################################################
#                 print(me)
#                 set_auth(token, me)
#                 st.success(f"{L['you_are_in']} {me['name']}")
#             except Exception as e:
#                 st.error(str(e))

#         st.write(L["or"])

#         # Register form
#         with st.form("register_form", clear_on_submit=False):
#             r_name = st.text_input(L["name"], key="reg_name")
#             r_email = st.text_input(L["email"], key="reg_email")
#             r_password = st.text_input(L["password"], type="password", key="reg_pass")
#             do_register = st.form_submit_button(L["register"])
#         if do_register:
#             try:
#                 resp = api_request(
#                     "POST",
#                     "/auth/register",
#                     json={"name": r_name, "email": r_email, "password": r_password},
#                 )
#                 st.success(L["register"] + " ✔️ — now log in.")
#             except Exception as e:
#                 st.error(str(e))

#     else:
#         user = st.session_state["user"]
#         st.write(f"{L['hello']}, {user['name']}!")
#         if st.button(L["logout"], use_container_width=True):
#             clear_auth()
#             st.rerun()






@st.dialog("🔐 Authentication")
def auth_dialog():
    if "token" not in st.session_state:
        st.subheader(L["login"])

        # --- Login form ---
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(L["email"])
            password = st.text_input(L["password"], type="password")
            do_login = st.form_submit_button(L["login"])
        if do_login:
            try:
                resp = api_request(
                    "POST",
                    "/auth/login",
                    data={"username": email, "password": password},
                )
                token = resp.json()["access_token"]
                st.session_state["token"] = token
                me = api_request("GET", "/auth/me").json()
                set_auth(token, me)
                st.success(f"{L['you_are_in']} {me['name']}")
                st.rerun()
            except Exception as e:
                st.error(str(e))

        st.write(L["or"])

        # --- Register form ---
        with st.form("register_form", clear_on_submit=False):
            r_name = st.text_input(L["name"], key="reg_name")
            r_email = st.text_input(L["email"], key="reg_email")
            r_password = st.text_input(L["password"], type="password", key="reg_pass")
            do_register = st.form_submit_button(L["register"])
        if do_register:
            try:
                resp = api_request(
                    "POST",
                    "/auth/register",
                    json={"name": r_name, "email": r_email, "password": r_password},
                )
                st.success(L["register"] + " ✔ — now log in.")
            except Exception as e:
                st.error(str(e))
   


with st.sidebar:
    # If user is not logged in → show "Log in / Register" button
    if "token" not in st.session_state:
        if st.button("🔐 Log in / Register", use_container_width=True):
            auth_dialog()

    # If user is logged in → show "Hello" + Logout button directly
    else:
        user = st.session_state.get("user", {})
        st.write(f"👋 {L['hello']}, {user.get('name', 'User')}!")
        if st.button("🚪 " + L["logout"], use_container_width=True):
            clear_auth()
            st.rerun()




# --- Sessions helper using the authorized client ---
def load_sessions():
    try:
        return api_request("GET", "/session/list").json()
    except Exception:
        return []

def ensure_at_least_one_session():
    try:
        resp = api_request("POST", "/session/new")  # Authorized
        return resp.json().get("session_id")
    except Exception:
        return None



# ---- Initial data fetch (needs auth) ----
sessions = []
if "token" in st.session_state:
    sessions = load_sessions()
    if not sessions:
        sid = ensure_at_least_one_session()
        if sid:
            st.session_state.current_session = sid
            sessions = load_sessions()





















# st.sidebar.markdown("---")
if "current_page" not in st.session_state:
    st.session_state.current_page = "chat"  # default


# Define only one page
pages = {
    "Test My Knowledge": [
        st.Page("job_skills_review.py", title="Test My Knowledge"),
    ],
}

# Create the navigation (top menu)
pg = st.navigation(pages, position="hidden")

# Sidebar button
if st.sidebar.button("🧠 Test My Knowledge", use_container_width=True):
    st.session_state.current_page = "job_skills_review"
    st.rerun()  # refresh to switch page

if st.sidebar.button("💬 Chat", use_container_width=True):
    st.session_state.current_page = "chat"
    st.rerun()

if st.session_state.current_page == "job_skills_review":
    st.sidebar.markdown("""
    <hr>
    <p style='text-align: center; color: gray;'>EduMentor AI ©️ 2025</p>
    """, unsafe_allow_html=True)

if st.session_state.current_page == "chat":
    st.sidebar.markdown("---")
    # Create new session button (unique key)
    if "token" in st.session_state:
    # Create new session button (unique key)
        if st.sidebar.button("➕ New Session", key="new_session_btn", use_container_width=True):
            try:
                r = api_request("POST", "/session/new")

                r.raise_for_status()
                sid = r.json().get("session_id")
                st.session_state.current_session = sid
                st.session_state.pop("last_uploaded", None)  # reset uploaded file tracker
                st.rerun()


            except Exception as e:
                st.sidebar.error(f"Could not create session: {e}")

    # load sessions list
    try:
        r = api_request("GET", "/session/list")
        sessions = r.json() if r.status_code == 200 else []
    except Exception:
        sessions = []

    # If no sessions at all, create one automatically (first-time user)
    if not sessions:
        try:
            r = api_request("POST", "/session/new")
            r.raise_for_status()
            sid = r.json().get("session_id")
            st.session_state.current_session = sid

            # reload sessions
            r2 = api_request("GET", "/session/list")
            sessions = r2.json() if r2.status_code == 200 else []
        except Exception:
            pass

    # Display sessions in sidebar with delete button
    # st.sidebar.markdown("---")

    # --- Custom style only for your session buttons ---
    st.markdown("""
    <style>
    /* Open session button (secondary) */
    button[kind="secondary"] {
        background-color: #f8fafc !important;
        color: #111827 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 15px !important;
        height: 40px !important;         /* fixed height only */
        font-size: 15px !important;
        font-weight: 500 !important;
        display: flex !important;
        justify-content: center !important;  /* text aligned left */
        align-items: center !important;
        padding-left: 10px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    button[kind="secondary"]:hover {
        background-color: #e5e7eb !important;
    }

    /* Delete button (primary) */
    button[kind="primary"] {
        background-color: #ef4444 !important;
        color: white !important;
        border-radius: 15px !important;
        width: 35px !important;
        height: 35px !important;
        font-weight: bold !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
    button[kind="primary"]:hover {
        background-color: #dc2626 !important;
    }
    </style>
    """, unsafe_allow_html=True)


    if "token" in st.session_state:
        # --- Your loop ---
        for idx, s in enumerate(sessions):
            name = s.get("name") or "Untitled Session"
            session_id_val = s.get("id", f"session_{idx}")

            col_open, col_del = st.sidebar.columns([4, 1])

            open_key = f"open_session_btn_{session_id_val}_{idx}"
            del_key = f"delete_session_btn_{session_id_val}_{idx}"

            # ✅ Open button (full width + truncated text)
            if col_open.button(name, key=open_key, type="secondary", use_container_width=True):
                st.session_state.current_session = session_id_val
                st.session_state.messages = s.get("messages", [])
                st.session_state.pop("last_uploaded", None)
                st.rerun()

            # ✅ Delete button (small fixed red)
            if col_del.button("X", key=del_key, type="primary"):
                try:
                    api_request("DELETE", f"/session/{session_id_val}")
                except Exception:
                    pass
                st.rerun()


    st.sidebar.markdown("""
    <hr>
    <p style='text-align: center; color: gray;'>EduMentor AI ©️ 2025</p>
    """, unsafe_allow_html=True)




    # ---------- Main area ----------
    if "token" in st.session_state:
        sid = st.session_state.get("current_session")

        if not sid:
            if sessions:
                st.session_state.current_session = sessions[0]["id"]
                sid = sessions[0]["id"]
            else:
                # no sessions — create one
                sid = ensure_at_least_one_session()
                st.session_state.current_session = sid

        # ✅ fetch selected session
        r = api_request("GET", f"/session/{sid}")
        if r.status_code != 200:
            st.error("Session not found.")
            st.stop()

        session = r.json()
    else:
        st.info("Please log in to start.")
        st.stop()





    st.title(session.get("name") or ("Untitled Session"))

    # # --- Add vertical space below the title (same spacing as reference version) ---
    # st.markdown("<div style='margin-top: 35px;'></div>", unsafe_allow_html=True)

    # ---------- Messages display area ----------
    st.markdown('<div class="message-box">', unsafe_allow_html=True)
    messages = st.session_state.get("messages", session.get("messages", []))
    st.markdown('</div>', unsafe_allow_html=True)

    for m in messages:
        role = "user" if m["role"] == "user" else "assistant"
        role_label = "🧑‍🎓 You" if role == "user" else "🤖 EduMentor"

        with st.chat_message(role):
            if m["type"] == "quiz":
                # st.markdown("### 🧩 Quiz Time!")

                try:
                    quiz_data = json.loads(m["content"])
                except Exception:
                    quiz_data = m["content"]

                if isinstance(quiz_data, list):
                    for i, q in enumerate(quiz_data, 1):
                        st.markdown(f"**Q{i}.** {q['question']}")
                        for opt in q.get("options", []):
                            st.markdown(f"- {opt}")
                        # Correct key is "answer" in your data
                        if "answer" in q:
                            st.markdown(f"**✅ Correct Answer:** {q['answer']}")
                        st.markdown("---")
                else:
                    st.markdown(quiz_data)

            # --- Custom display for report messages ---
            elif m["type"] == "report":
                if role == "user":
                    # Show a simple placeholder for the user
                    st.markdown("📄 Report based on your quiz performance")
                else:
                    # Show the assistant’s detailed report normally
                    st.markdown(m["content"])
            
            # --- Custom display for grammer messages ---
            elif m["type"] == "grammar":
                if role == "user":
                    # Show a simple placeholder for the user
                    st.markdown("Checking grammar")
                else:
                    # Show the assistant’s detailed grammar normally
                    st.markdown(m["content"])

            # --- Default display for other message types ---
            else:
                st.markdown(m["content"])

    # ---------- Control bar container ----------
    # persistent UI state
    if "action_lang" not in st.session_state:
        st.session_state["action_lang"] = "en"
    if "main_chat_input" not in st.session_state:
        st.session_state["main_chat_input"] = ""
    if "processing" not in st.session_state:
        st.session_state["processing"] = False
    if "clicked_action" not in st.session_state:
        st.session_state["clicked_action"] = None


    # ---------- CSS for fixed bottom control bar (centered) ----------
    st.markdown(
    """
    
    <style>
    h1 {
    margin-bottom: 70px !important;
    }
    .fixed-bar {
        position: fixed;
        left: 50%;
        transform: translateX(-50%);
        bottom: 18px;
        width: 90%;
        max-width: 1500px;
        background-color: white;
        border: 1px solid #e6e6e6;
        border-radius: 12px;
        padding: 12px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
        z-index: 9999;
    }
    .actions-row {
        display:flex;
        flex-wrap: wrap;
        gap:8px;
        margin-top:8px;
        justify-content:center;
    }
    .message-box {
      
    }
    .send-circle {
        width:48px;
        height:48px;
        border-radius:24px;
        display:flex;
        align-items:center;
        justify-content:center;
        border:none;
        background: #0b5fff;
        color:white;
        font-size:18px;
    }
    .voice-btn {
        width:48px;
        height:48px;
        border-radius:24px;
        display:flex;
        align-items:center;
        justify-content:center;
        border:1px solid #ddd;
        background: white;
        font-size:16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
    )


    # --- Top layout with voice + chat input

    #################
    # --- Helper function to send message ---
    def send_message(user_text):
        st.session_state["processing"] = True
        try:
            resp = api_request("POST", f"/session/{sid}/message", data={"text": user_text})
            resp.raise_for_status()
            data = resp.json()
            st.session_state["messages"] = data["session"]["messages"]
        except Exception as e:
            st.error(f"Error sending message: {e}")
        finally:
            st.session_state["processing"] = False
            st.rerun()  # refresh chat after sending

    def add_message_to_session(role: str, content: str, msg_type: str = "info"):
        """Append a message (bot or user) directly to backend session."""
        try:
            payload = {"role": role, "content": content, "type": msg_type}
            # requests.post(f"{BACKEND}/session/{sid}/add_message", json=payload)
            # Refresh the local message list
            r = api_request("GET", f"/session/{sid}")
            if r.status_code == 200:
                st.session_state["messages"] = r.json().get("messages", [])
        except Exception as e:
            st.error(f"Failed to add message: {e}")

    # --- Define session-specific keys ---
    audio_widget_key = f"voice_input_{sid}"
    audio_processed_list_key = f"audio_processed_list_{sid}"
    transcribed_text_key = f"transcribed_text_{sid}"
    pending_send_key = f"pending_send_{sid}"

    # --- Initialize processed audio list ---
    if audio_processed_list_key not in st.session_state:
        st.session_state[audio_processed_list_key] = []

    # --- Define the voice dialog once ---
    @st.dialog("🎤 Record your voice")
    def voice_dialog():
        audio_data = st.audio_input("Start recording:", key=f"voice_input_dialog_{sid}")
        


        if audio_data:
            audio_bytes = audio_data.read()
            files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
            st.write(f"Audio size: {len(audio_bytes)} bytes")
            try:
                # resp = requests.post(f"{BACKEND}/session/{sid}/transcribe", files=files)
                resp = api_request("POST", f"/session/{sid}/transcribe", files=files)
                if resp.status_code == 200:
                    transcription = resp.json().get("transcription", "").strip()
                    st.session_state[transcribed_text_key] = transcription
                    st.info("🎤 Audio transcribed! Edit below if needed.")
                else:
                    st.error("Failed to transcribe audio")
            except Exception as e:
                st.error(f"Error sending audio to backend: {e}")

        # Editable transcription
        if transcribed_text_key in st.session_state:
            edited_text = st.text_area(
                "📝 Edit your transcription before sending:",
                value=st.session_state[transcribed_text_key],
                height=150
            )
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("✅ Confirm", key=f"confirm_voice_{sid}"):
                    st.session_state[pending_send_key] = edited_text.strip()
                    del st.session_state[transcribed_text_key]
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", key=f"cancel_voice_{sid}"):
                    del st.session_state[transcribed_text_key]
                    st.rerun()

    # ---------- Chat input & action buttons ----------
    chat_cols = st.columns([12, 0.55])

    # 💬 Normal chat input
    with chat_cols[0]:
        user_input = st.chat_input(
            placeholder="Type a message or upload a file...",
            accept_file=True,
            file_type=["pdf", "docx", "txt"],
            key="main_chat_input"
        )

    # 🎤 Voice input button
    with chat_cols[1]:
        if st.button("🎤︎", use_container_width=True):
            voice_dialog()  # <-- This actually opens the dialog
    
    # --- Handle pending send ---
    if pending_send_key in st.session_state:
        pending_text = st.session_state.pop(pending_send_key)
        if pending_text and pending_text.strip():
            send_message(pending_text.strip())
            st.success("✅ Message sent successfully.")

    
    if user_input:
        # --- Handle uploaded files
        if user_input["files"]:
            for uploaded_file in user_input["files"]:
                file_bytes = uploaded_file.getvalue()
                file_hash = hashlib.md5(file_bytes).hexdigest()
                last_uploaded = st.session_state.get("last_uploaded")

                if last_uploaded != file_hash:
                    try:
                        files = {"file": (uploaded_file.name, file_bytes)}
                        resp = api_request("POST", f"/session/{sid}/upload", files=files)

                        if resp.status_code == 200:
                            # Refresh messages
                            r_refresh = api_request("GET", f"/session/{sid}")
                            if r_refresh.status_code == 200:
                                st.session_state["messages"] = r_refresh.json().get("messages", [])

                            # Mark as uploaded
                            st.session_state["last_uploaded"] = file_hash
                            st.success(f"Uploaded {uploaded_file.name}")
                            st.rerun()
                        else:
                            st.error(resp.json().get("detail", "Upload failed"))

                    except Exception as e:
                        st.error(f"Upload error: {e}")

        # --- Handle text input
        elif user_input["text"]:
            # user_input = st.session_state.get("main_chat_input", None)
            user_text = user_input["text"].strip()
            if user_text != "":
                st.session_state["processing"] = True
                try:
                    resp = api_request("POST", f"/session/{sid}/message", data={"text": user_text})
                    resp.raise_for_status()
                    data = resp.json()
                    st.session_state["messages"] = data["session"]["messages"]
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    st.session_state["processing"] = False
                    st.rerun()

    # Action buttons
    actions = ["summarize", "flashcards", "resources", "quiz", "report", "grammar"]
    action_labels_en = {
        "summarize": "📝 Summarize",
        "flashcards": "📚 Flashcards", 
        "resources": "🔗 Resources",
        "quiz": "🧩 Quiz",
        "report": "📊 Report",
        "grammar": "✏️ Grammar",
    }
    btn_cols = st.columns(6)
    clicked_action_local = None

    # --- Function to open dialog ---
    # --- Quiz ---
    if "quiz_history" not in st.session_state:
        st.session_state.quiz_history = {}

    # Ensure this session id exists
    if sid not in st.session_state.quiz_history:
        st.session_state.quiz_history[sid] = []

    # --- Step 1: Quiz Settings ---
    @st.dialog("🧠 Quiz Settings") 
    def quiz_settings():
        st.markdown("### ⚙️ Quiz Options")
        difficulty = st.selectbox("Select quiz difficulty:", ["Easy", "Medium", "Hard"])
        st.session_state.quiz_num_questions = st.slider(
            "Number of questions:", 1, 10, st.session_state.get("quiz_num_questions", 5)
        )
        if "quiz_started" not in st.session_state:
            st.session_state.quiz_started = False
        if "quiz_submitted" not in st.session_state:
            st.session_state.quiz_submitted = False

        if st.button("Start Quiz"):
            st.session_state.quiz_started = True
            st.session_state.quiz_submitted = False
            st.session_state.quiz_difficulty = difficulty.lower()

            # Fetch quiz from backend
            payload = {
                "text": "",
                "lang": "en",
                "difficulty": st.session_state.quiz_difficulty,
                "num_questions": st.session_state.quiz_num_questions,
            }
            with st.spinner("Generating quiz... ⏳"):
                try:
                    resp = api_request("POST", f"/session/{sid}/generate/quiz", data=payload)
                    resp.raise_for_status()
                    raw_quiz = resp.json().get("reply", "")
                    match = re.search(r"(\[.*\])", raw_quiz, re.DOTALL)
                    st.session_state.quiz_data = json.loads(match.group(1)) if match else []
                except Exception as e:
                    st.error(f"Failed to generate quiz: {e}")
                    st.session_state.quiz_data = []

            st.session_state.must_show_questions = True
            st.rerun()


    # --- Step 2: Show Questions ---
    @st.dialog("📝 Quiz Questions")
    def show_questions():
        if not st.session_state.get("quiz_data"):
            st.warning("No quiz data available. Go back to settings.")
            return

        st.session_state.quiz_answers = {}
        for i, q in enumerate(st.session_state.quiz_data):
            st.session_state.quiz_answers[i] = st.radio(
                f"Q{i+1}: {q['question']}", q.get("options", []), key=f"quiz_q{i}"
            )

        if st.button("Submit Quiz"):
            st.session_state.quiz_submitted = True
            st.session_state.must_show_results = True
            st.rerun()


    # --- Step 3: Show Results ----
    @st.dialog("🏆 Quiz Results", on_dismiss="rerun")
    def show_results():
        results = []
        for i, q in enumerate(st.session_state.quiz_data):
            correct_letter = q.get("answer", "").upper()
            options = q.get("options", [])
            correct_text = next((opt for opt in options if opt.startswith(correct_letter)), correct_letter)
            user_ans = st.session_state.quiz_answers.get(i, "")
            user_text = next((opt for opt in options if user_ans and opt.startswith(user_ans[0].upper())), user_ans or "No answer")
            is_correct = user_ans and user_ans[0].upper() == correct_letter
            results.append({
                "question": q["question"],
                "your_answer": user_text,
                "correct_answer": correct_text,
                "is_correct": is_correct
            })

        # --- Ensure quiz_history structure exists ---
        if "quiz_history" not in st.session_state:
            st.session_state.quiz_history = {}
        if sid not in st.session_state.quiz_history:
            st.session_state.quiz_history[sid] = []

        # --- Save this quiz attempt ---
        if not st.session_state.get("quiz_saved", False):
            st.session_state.quiz_history[sid].append(results)
            st.session_state.quiz_saved = True
        # --- Prepare display ---
        quiz_md = "### 🧠 EduMentor (Quiz)\n\n"
        for idx, r in enumerate(results, start=1):
            color = "green" if r["is_correct"] else "red"
            quiz_md += f"*Q{idx}:* {r['question']}\n"
            quiz_md += f"- *Your answer:* <span style='color:{color}'>{r['your_answer']}</span><br>\n"
            quiz_md += f"- *Correct answer:* <span style='color:green'>{r['correct_answer']}</span><br>\n"
            quiz_md += "✅ Correct!\n\n" if r["is_correct"] else "❌ Incorrect\n\n"
            quiz_md += "---\n"

        total = len(results)
        correct = sum(r["is_correct"] for r in results)
        quiz_md += f"### 🏆 Score: {correct}/{total} ({(correct/total)*100:.1f}%)\n"

        # --- Display attempts counter (per session only) ---
        session_attempts = len(st.session_state.quiz_history[sid])
        st.info(f"📊 Attempts in this session: {session_attempts}")

        # --- Display results in dialog ---
        st.markdown(quiz_md, unsafe_allow_html=True)

        # --- Save results to chat session for report ---
        add_message_to_session("assistant", quiz_md, "quiz")

        # --- Option to retake quiz ---
        if st.button("Take Another Quiz"):
            st.session_state.quiz_data = None
            st.session_state.quiz_answers = {}
            st.session_state.quiz_started = False
            st.session_state.quiz_submitted = False
            st.session_state.must_show_questions = False
            st.session_state.must_show_results = False
            st.session_state.quiz_saved = False  # ✅ reset here
            st.rerun()



    if st.session_state.get("must_show_questions"):
        st.session_state.must_show_questions = False
        show_questions()

    if st.session_state.get("must_show_results"):
        st.session_state.must_show_results = False
        show_results()

    ###############

    # --- REPORT Dialog ---
    @st.dialog("📊 Generate Report",on_dismiss="rerun")
    def open_report_dialog():
        if (
            "quiz_history" not in st.session_state
            or sid not in st.session_state.quiz_history
            or len(st.session_state.quiz_history[sid]) == 0
        ):
            st.warning("No quiz results found for this session. Please complete at least one quiz first.")
        else:
            report_type = st.radio("Select report type:", ["Performance based on quiz results"])
            if st.button("Generate Report"):
                all_results = st.session_state.quiz_history[sid]
                payload = {
                    "text": json.dumps(all_results),
                    "lang": "en",
                    "report_type": report_type.lower(),
                }
                with st.spinner("Generating report... ⏳"):
                    try:
                        resp = api_request("POST", f"/session/{sid}/generate/report", data=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            report_output = data.get("reply", "No response from backend.")
                            add_message_to_session("assistant", report_output, "report")
                            st.markdown("### ✅ Generated Report:")
                            st.markdown(report_output)

                        else:
                            st.error(f"Failed: {resp.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")


    ############
    # --- GRAMMAR Dialog ---
    @st.dialog("🔤 Grammar Checker", on_dismiss="rerun")
    def open_grammar_dialog():
        st.markdown("Enter your text below to check for **grammar**, **spelling**, and **clarity** improvements.")

        # --- Reset grammar output when opening the dialog ---
        st.session_state.grammar_output = ""

        # --- Text input area ---
        text_grammar = st.text_area("✏️ Text to check:", height=180)

        # --- Check Grammar button ---
        check_clicked = st.button("✅ Check Grammar", use_container_width=True)

        # --- Placeholder for result below the button ---
        result_placeholder = st.container()

        # --- Grammar check logic ---
        if check_clicked:
            if not text_grammar.strip():
                st.warning("⚠️ Please enter some text first.")
                return

            payload = {"text_grammar": text_grammar, "lang": "en"}
            with st.spinner("Checking grammar... ⏳"):
                try:
                    resp = api_request("POST", f"/session/{sid}/generate/grammar", data=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        grammar_output = data.get("reply", "No response from backend.")
                        st.session_state.grammar_output = grammar_output

                        # Save assistant message to session memory
                        add_message_to_session("assistant", grammar_output, "grammar")

                        # ✅ Show result below the button
                        with result_placeholder:
                            st.markdown("---")
                            st.markdown("### 🪄 Grammar Check Result:")
                            st.markdown(grammar_output)

                        # ✅ Automatically clear text area for next input
                        st.session_state.grammar_text = ""
                    else:
                        result_placeholder.error(f"Failed: {resp.text}")
                except Exception as e:
                    result_placeholder.error(f"Error: {e}")
    #########


    # # Check if a file has been uploaded in the chat history
    # file_uploaded_in_chat = any(
    #     m["role"] == "assistant" and m.get("type") == "upload" for m in messages
    # )

    # # Create buttons
    # for idx, (col, action) in enumerate(zip(btn_cols, actions)):
    #     label = action_labels_en[action]
    #     with col:
    #         if file_uploaded_in_chat:
    #             # Enable button
    #             if st.button(label, key=f"action_btn_{action}_{idx}", use_container_width=True):
    #                 clicked_action_local = action
    #         else:
    #             # Disable button
    #             st.button(label, key=f"action_btn_{action}_{idx}", use_container_width=True, disabled=True)


    # Check if a file has been uploaded in the chat history
    file_uploaded_in_chat = any(
        m["role"] == "assistant" and m.get("type") == "upload" for m in messages
    )

    # Create buttons
    for idx, (col, action) in enumerate(zip(btn_cols, actions)):
        label = action_labels_en[action]
        with col:
            # Enable Grammar button even if no file uploaded
            if file_uploaded_in_chat or action.lower() == "grammar":
                if st.button(label, key=f"action_btn_{action}_{idx}", use_container_width=True):
                    clicked_action_local = action
            else:
                st.button(label, key=f"action_btn_{action}_{idx}", use_container_width=True, disabled=True)
    
    # --- Handle clicks ---
    if clicked_action_local:
        if clicked_action_local == "quiz":
            quiz_settings()
        elif clicked_action_local == "report":
            open_report_dialog()
        elif clicked_action_local == "grammar":
            open_grammar_dialog()
        else:
            # Handle normal actions (summarize, flashcards, resources, etc.)
            st.session_state["clicked_action"] = clicked_action_local
            st.session_state["processing"] = True
            st.rerun()

    # ---------- Processing indicator ----------
    if st.session_state.get("processing"):
        st.markdown(
            "<div style='position:fixed; bottom:110px; left:50%; transform:translateX(-50%); "
            "background:#fff;padding:6px 12px;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.08);"
            "font-size:14px; color:#333; display:flex;align-items:center;gap:8px;'>"
            "<div class='loader' style='width:12px;height:12px;border:2px solid #ccc;"
            "border-top-color:#0b5fff;border-radius:50%;animation:spin 0.6s linear infinite;'></div>"
            "<div>Processing...</div>"
            "<style>@keyframes spin {from{transform:rotate(0deg);} to{transform:rotate(360deg);}}</style>"
            "</div>",
            unsafe_allow_html=True,
        )

    # ---------- Handle action buttons (summarize, quiz, etc.) ----------
    if st.session_state.get("clicked_action"):
        which_action = st.session_state["clicked_action"]
        add_text = st.session_state.get("main_input_text", "")
        lang_pref = st.session_state.get("action_lang", "en")

        st.session_state["processing"] = True
        try:
            resp =  api_request("POST", f"/session/{sid}/generate/{which_action}", data={"text": add_text, "lang": lang_pref})
            resp.raise_for_status()
            data = resp.json()
            st.session_state["messages"] = data["session"]["messages"]
        except Exception as e:
            st.error(f"Action error: {e}")
        finally:
            st.session_state["processing"] = False
            st.session_state["clicked_action"] = None
            st.rerun()

elif st.session_state.current_page == "job_skills_review":
    # ---------- Render job_skills_review page ----------
    pg.run()  # renders your "job_skills_review.py" page


