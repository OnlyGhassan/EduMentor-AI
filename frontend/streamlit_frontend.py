########################### 3
 



"""
Streamlit frontend for EduMentorAI (ChatGPT-like UI)
Run with: `streamlit run streamlit_frontend.py`
Make sure backend is running at http://localhost:8000
"""

import streamlit as st
import requests
from streamlit.components.v1 import html as st_html
import hashlib
import re, json
import time


BACKEND = "http://localhost:8000"
st.set_page_config(page_title="EduMentorAI", layout="wide", initial_sidebar_state="auto")

# ---------- Sidebar: sessions + language ----------
logo_url = 'logo.png'
st.sidebar.image(logo_url)



# UI language (English / Arabic)
ui_lang = st.sidebar.radio(
    "Language / اللغة",
    ("English", "العربية"),
    index=0,
    key="ui_lang_radio",
)
is_ar_ui = (ui_lang == "العربية")

# with st.sidebar:
#     if not st.user.is_logged_in:
#         login_label = "Log in" if not is_ar_ui else "تسجيل الدخول"
#         if st.button(login_label, use_container_width=True):
#             st.login()
#     else:
#         logout_label = "Log out" if not is_ar_ui else "تسجيل الخروج"
#         greeting = f"Hello, {st.user.name}!" if not is_ar_ui else f"مرحبًا، {st.user.name}!"
#         st.write(greeting)
#         if st.button(logout_label, use_container_width=True):
#             st.logout()



# --- Config ---
BACKEND_BASE = st.secrets.get("BACKEND_BASE", "http://localhost:8000")
is_ar_ui = st.secrets.get("AR_UI", False)

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
L = TXT_AR if is_ar_ui else TXT

st.set_page_config(page_title=L["title"], layout="wide")
st.title(L["title"])

# --- Auth sidebar ---
with st.sidebar:
    if "token" not in st.session_state:
        st.subheader(L["login"])

        # Login form
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(L["email"])
            password = st.text_input(L["password"], type="password")
            do_login = st.form_submit_button(L["login"])
        if do_login:
            # FastAPI expects OAuth2PasswordRequestForm (form encoded) with username/password fields.
            # We pass email into "username".
            try:
                resp = api_request(
                    "POST",
                    "/auth/login",
                    data={"username": email, "password": password},
                )
                token = resp.json()["access_token"]
                # Get current user using /auth/me
                me = api_request("GET", "/auth/me").json()
                set_auth(token, me)
                st.success(f"{L['you_are_in']} {me['name']}")
            except Exception as e:
                st.error(str(e))

        st.write(L["or"])

        # Register form
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
                st.success(L["register"] + " ✔️ — now log in.")
            except Exception as e:
                st.error(str(e))

    else:
        user = st.session_state["user"]
        st.write(f"{L['hello']}, {user['name']}!")
        if st.button(L["logout"], use_container_width=True):
            clear_auth()
            st.rerun()

# --- Protected actions (examples) ---
if "token" in st.session_state:
    c1, c2 = st.columns(2)
    with c1:
        if st.button(L["list_sessions"]):
            try:
                data = api_request("GET", "/session/list").json()
                st.json(data)
            except Exception as e:
                st.error(str(e))
    with c2:
        with st.form("new_session"):
            sname = st.text_input(L["create_session"], value="Untitled Session")
            create = st.form_submit_button("OK")
        if create:
            try:
                # you might have a POST /session/create in your real code;
                # if not, this is a placeholder to show how to call protected endpoints.
                # Replace with your actual "create session" endpoint when available.
                st.info("Call your create-session endpoint here.")
            except Exception as e:
                st.error(str(e))











# Create new session button (unique key)
if st.sidebar.button("➕ New Session" if not is_ar_ui else "➕ جلسة جديدة", key="new_session_btn", use_container_width=True):
    try:
        r = requests.post(f"{BACKEND}/session/new")
        r.raise_for_status()
        sid = r.json().get("session_id")
        st.session_state.current_session = sid
        st.session_state.pop("last_uploaded", None)  # reset uploaded file tracker
        st.rerun()


    except Exception as e:
        st.sidebar.error(f"Could not create session: {e}")

# load sessions list
try:
    r = requests.get(f"{BACKEND}/sessions")
    sessions = r.json() if r.status_code == 200 else []
except Exception:
    sessions = []

# If no sessions at all, create one automatically (first-time user)
if not sessions:
    try:
        r = requests.post(f"{BACKEND}/session/new")
        r.raise_for_status()
        sid = r.json().get("session_id")
        st.session_state.current_session = sid

        # reload sessions
        r2 = requests.get(f"{BACKEND}/sessions")
        sessions = r2.json() if r2.status_code == 200 else []
    except Exception:
        pass

# Display sessions in sidebar with delete button
st.sidebar.markdown("---")

# for idx, s in enumerate(sessions):
#     name = s.get("name") or "Untitled Session"
#     session_id_val = s.get("id", f"session_{idx}")

#     col_open, col_del = st.sidebar.columns([4, 1])

#     open_key = f"open_session_btn_{session_id_val}_{idx}"
#     del_key = f"delete_session_btn_{session_id_val}_{idx}"
#     ########edit the style
#     if col_open.button(name, key=open_key, use_container_width=True):
#         st.session_state.current_session = session_id_val
#         st.session_state.messages = s.get("messages", [])
#         # ✅ Reset upload tracking when switching sessions
#         st.session_state.pop("last_uploaded", None)
#         st.rerun()


#     if col_del.button("X", key=del_key):
#         try:
#             requests.delete(f"{BACKEND}/session/{session_id_val}")
#         except Exception:
#             pass
#         st.rerun()
# --- Custom style only for your session buttons ---
st.markdown("""
    <style>
    /* Open session button (secondary) */
    button[kind="secondary"] {
        background-color: #f8fafc !important;
        color: #111827 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 8px !important;
        height: 40px !important;         /* fixed height only */
        font-size: 15px !important;
        font-weight: 500 !important;
        display: flex !important;
        justify-content: flex-start !important;  /* text aligned left */
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
        border-radius: 8px !important;
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
            requests.delete(f"{BACKEND}/session/{session_id_val}")
        except Exception:
            pass
        st.rerun()


st.sidebar.markdown("---")
####center
st.sidebar.markdown(
    "<p style='text-align: center; color: gray;'>EduMentor AI © 2025</p>",
    unsafe_allow_html=True
)
#######edit to display frist session auto.
# ---------- Main area ----------
sid = st.session_state.get("current_session")
if not sid:
    st.info("Create or select a session to begin." if not is_ar_ui else "أنشئ أو اختر جلسة للبدء.")
    st.stop()

# load fresh session data for the selected session
r = requests.get(f"{BACKEND}/session/{sid}")
if r.status_code != 200:
    st.error("Session not found." if not is_ar_ui else "لا توجد الجلسة.")
    st.stop()

session = r.json()
st.title(session.get("name") or ("Untitled Session" if not is_ar_ui else "جلسة بدون اسم"))

# ---------- CSS for fixed bottom control bar (centered) ----------
st.markdown(
    """
    <style>
    .fixed-bar {
        position: fixed;
        left: 50%;
        transform: translateX(-50%);
        bottom: 18px;
        width: 75%;
        max-width: 1200px;
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
        margin-bottom: 180px; /* space for fixed bar */
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

# ---------- Messages display area above control bar ----------
st.markdown('<div class="message-box">', unsafe_allow_html=True)

messages = st.session_state.get("messages", session.get("messages", []))
for m in messages:
    role_label = ("🧑‍🎓 You" if m['role'] == 'user' else "🤖 EduMentor")
    bubble_color = "#FCE4EC" if m['role'] == 'user' else "#E3F2FD"
    st.markdown(
        f"<div style='background-color:{bubble_color}; padding:10px; margin-bottom:6px; border-radius:8px;'>"
        f"<b>{role_label}</b> <i>({m['type']})</i><br>{m['content']}</div>",
        unsafe_allow_html=True,
    )

st.markdown('</div>', unsafe_allow_html=True)

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

# st.markdown('<div class="fixed-bar">', unsafe_allow_html=True)
####################################################################################
# Top row: upload | text input | voice | send
# top_cols = st.columns([1, 9, 1, 1])  # upload | input | voice | send

# # --- Upload (left)
# with top_cols[0]:
#     uploaded = st.file_uploader(
#         "",
#         key="control_upload_widget",
#         type=["pdf", "docx", "txt"],
#         help="Upload files to session"
#     )

#     if uploaded is not None:
#         # Prevent repeated uploads on rerun
        
#         file_hash = hashlib.md5(uploaded.getvalue()).hexdigest()
#         last_uploaded = st.session_state.get("last_uploaded")

#         if last_uploaded != file_hash:
#             try:
#                 files = {"file": (uploaded.name, uploaded.getvalue())}
#                 resp = requests.post(f"{BACKEND}/session/{sid}/upload", files=files)

#                 if resp.status_code == 200:
#                     # After upload succeeds, refresh session messages
#                     r_refresh = requests.get(f"{BACKEND}/session/{sid}")
#                     if r_refresh.status_code == 200:
#                         st.session_state["messages"] = r_refresh.json().get("messages", [])

#                     # Mark this file as uploaded so we don't re-upload on rerun
#                     st.session_state["last_uploaded"] = file_hash

#                     st.success("Uploaded" if not is_ar_ui else "تم الرفع")
#                     st.rerun()
#                 else:
#                     st.error(resp.json().get("detail", "Upload failed"))

#             except Exception as e:
#                 st.error(f"Upload error: {e}")

# # --- Input (middle)
# with top_cols[1]:
#     # Render the text_input normally; Streamlit will manage the value in session_state
#     user_text = st.text_input(
#         "",
#         value=st.session_state.get("main_input_text", ""),
#         key="main_input_text",
#         placeholder=("Type a message..." if not is_ar_ui else "اكتب رسالة..."),
#     )

# # --- Voice button
# with top_cols[2]:
#     st.button(
#         "🎤",
#         key="voice_btn_main",
#         help="Voice input",
#     )
#     # Click handled by JS later

# # --- Send button (arrow in a circle)
# with top_cols[3]:
#     send_clicked = st.button(
#         "➤",
#         key="send_btn_main",
#         help="Send (Enter works too)",
#     )


# --- Custom CSS (scoped only to this input area)
st.markdown("""
<style>
.voice-btn {
    background-color: #4f46e5;
    color: white;
    border: none;
    border-radius: 50%;
    width: 60px;
    height: 100px;
    font-size: 22px;
    cursor: pointer;
    transition: background 0.3s ease;
}
.voice-btn:hover {
    background-color: #4338ca;
}
[data-testid="stChatInput"] {
    background-color: #f8fafc !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 14px !important;
    padding: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# st.markdown("""
# <style>
# div[data-testid="stAudioInput"] {
#     margin-top: 10px;
# }
# </style>
# """, unsafe_allow_html=True)

# --- Top layout with voice + chat input

# --- Helper function to send message ---
def send_message(user_text):
    st.session_state["processing"] = True
    try:
        resp = requests.post(f"{BACKEND}/session/{sid}/message", data={"text": user_text})
        resp.raise_for_status()
        data = resp.json()
        st.session_state["messages"] = data["session"]["messages"]
    except Exception as e:
        st.error(f"Error sending message: {e}")
    finally:
        st.session_state["processing"] = False
        st.rerun()  # refresh chat after sending

# --- Define session-specific keys ---
audio_widget_key = f"voice_input_{sid}"
audio_processed_list_key = f"audio_processed_list_{sid}"

# --- Initialize processed audio list for this session ---
if audio_processed_list_key not in st.session_state:
    st.session_state[audio_processed_list_key] = []

# --- Chat layout ---
chat_cols = st.columns([12, 1])

# 🎤 Voice input
with chat_cols[1]:
    audio_data = st.audio_input("🎤", key=audio_widget_key, label_visibility="collapsed")

# --- Process audio immediately ---
if audio_data is not None:
    # Prevent re-processing the same audio object
    if audio_data not in st.session_state[audio_processed_list_key]:
        audio_bytes = audio_data.read()
        files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
        try:
            resp = requests.post(f"{BACKEND}/session/{sid}/transcribe", files=files)
            if resp.status_code == 200:
                user_text = resp.json().get("transcription", "").strip()
                if user_text:
                    st.success(f"🗣️ Transcribed: {user_text}")
                    send_message(user_text)
            else:
                st.error("Failed to transcribe audio")
        except Exception as e:
            st.error(f"Error sending audio to backend: {e}")
        finally:
            # Mark this audio as processed so it won't repeat
            st.session_state[audio_processed_list_key].append(audio_data)
            if audio_widget_key in st.session_state:
                del st.session_state[audio_widget_key]
            st.rerun()  # reset widget to allow next recording

# 💬 Normal chat input
with chat_cols[0]:
    user_input = st.chat_input(
        placeholder="Type a message or upload a file..." if not is_ar_ui else "اكتب رسالة أو ارفع ملف...",
        accept_file=True,
        file_type=["pdf", "docx", "txt"],
        key="main_chat_input"
    )

# # --- Handle typed messages or file uploads ---
# if user_input:
#     # Handle files
#     if isinstance(user_input, dict) and user_input.get("files"):
#         for uploaded_file in user_input["files"]:
#             file_bytes = uploaded_file.getvalue()
#             files = {"file": (uploaded_file.name, file_bytes)}
#             resp = requests.post(f"{BACKEND}/session/{sid}/upload", files=files)
#             r_refresh = requests.get(f"{BACKEND}/session/{sid}")
#             if r_refresh.status_code == 200:
#                 st.session_state["messages"] = r_refresh.json().get("messages", [])
#             st.success(f"Uploaded {uploaded_file.name}")
#     # Handle text
#     elif isinstance(user_input, str) and user_input.strip():
#         send_message(user_input.strip())

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
                    resp = requests.post(f"{BACKEND}/session/{sid}/upload", files=files)

                    if resp.status_code == 200:
                        # Refresh messages
                        r_refresh = requests.get(f"{BACKEND}/session/{sid}")
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
                resp = requests.post(f"{BACKEND}/session/{sid}/message", data={"text": user_text})
                resp.raise_for_status()
                data = resp.json()
                st.session_state["messages"] = data["session"]["messages"]
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                st.session_state["processing"] = False
                st.rerun()

# # --- Handle typed messages ---
# if user_text_input:
#     if isinstance(user_text_input, str) and user_text_input.strip():
#         send_message(user_text_input.strip())

#     elif isinstance(user_text_input, dict):
#         # --- Handle files ---
#         if user_text_input.get("files"):
#             for uploaded_file in user_text_input["files"]:
#                 file_bytes = uploaded_file.getvalue()
#                 file_hash = hashlib.md5(file_bytes).hexdigest()
#                 last_uploaded = st.session_state.get("last_uploaded")

#                 if last_uploaded != file_hash:
#                     try:
#                         files = {"file": (uploaded_file.name, file_bytes)}
#                         resp = requests.post(f"{BACKEND}/session/{sid}/upload", files=files)
#                         if resp.status_code == 200:
#                             # Refresh messages
#                             r_refresh = requests.get(f"{BACKEND}/session/{sid}")
#                             if r_refresh.status_code == 200:
#                                 st.session_state["messages"] = r_refresh.json().get("messages", [])
#                             st.session_state["last_uploaded"] = file_hash
#                             st.success(f"Uploaded {uploaded_file.name}")
#                             st.rerun()
#                         else:
#                             st.error(resp.json().get("detail", "Upload failed"))
#                     except Exception as e:
#                         st.error(f"Upload error: {e}")

#         # --- Handle text from chat_input ---
#         elif user_text_input.get("text"):
#             user_text = user_text_input["text"].strip()
#             if user_text:
#                 send_message(user_text)






####################################################################################
# Language selector + actions row (under top row)
# lang_cols = st.columns([2, 8])

# with lang_cols[0]:
#     st.session_state["action_lang"] = st.radio(
#         "Action Lang" if not is_ar_ui else "لغة الأفعال",
#         ("en", "ar"),
#         index=(0 if st.session_state["action_lang"] == "en" else 1),
#         key="action_lang_radio",
#     )

# with lang_cols[1]:
#     # Render action buttons horizontally, each with unique key
#     st.markdown("<div class='actions-row'>", unsafe_allow_html=True)

#     action_labels_en = {
#         "summarize": "Summarize",
#         "quiz": "Quiz",
#         "flashcards": "Flashcards",
#         "resources": "Resources",
#         "report": "Report",
#         "grammar": "Grammar",
#     }
#     action_labels_ar = {
#         "summarize": "تلخيص",
#         "quiz": "اختبار",
#         "flashcards": "بطاقات",
#         "resources": "مصادر",
#         "report": "تقرير",
#         "grammar": "تصحيح",
#     }

#     # We'll track clicks in a controlled way instead of relying on st.session_state['act_*']
#     clicked_action_local = None
#     for idx_a, a in enumerate(["summarize", "quiz", "flashcards", "resources", "report", "grammar"]):
#         label = action_labels_ar[a] if is_ar_ui else action_labels_en[a]
#         # give each action its own stable unique key
#         if st.button(label, key=f"action_btn_{a}_{idx_a}"):
#             clicked_action_local = a

#     # after loop, commit clicked action (if any)
#     if clicked_action_local:
#         st.session_state["clicked_action"] = clicked_action_local
#         st.session_state["processing"] = True
#         st.rerun()


#     st.markdown("</div>", unsafe_allow_html=True)

# st.markdown('</div>', unsafe_allow_html=True)  # close fixed-bar container


# # --- Define action labels ---
# is_ar_ui = False  # or True if your UI is Arabic

# action_labels_en = {
#     "summarize": "Summarize",
#     "quiz": "Quiz",
#     "flashcards": "Flashcards",
#     "resources": "Resources",
#     "report": "Report",
#     "grammar": "Grammar",
# }
# action_labels_ar = {
#     "summarize": "تلخيص",
#     "quiz": "اختبار",
#     "flashcards": "بطاقات",
#     "resources": "مصادر",
#     "report": "تقرير",
#     "grammar": "تصحيح",
# }

# actions = ["summarize", "quiz", "flashcards", "resources", "report", "grammar"]

# # --- Create one column per button ---
# btn_cols = st.columns([1]*len(actions))
# clicked_action_local = None

# for idx, (col, action) in enumerate(zip(btn_cols, actions)):
#     label = action_labels_ar[action] if is_ar_ui else action_labels_en[action]
#     with col:
#         if st.button(label, key=f"action_btn_{action}_{idx}", use_container_width=True):
#             clicked_action_local = action

# # --- Handle click ---
# if clicked_action_local:
#     st.session_state["clicked_action"] = clicked_action_local
#     st.session_state["processing"] = True
#     st.rerun()

    # st.markdown("</div>", unsafe_allow_html=True)

# st.markdown('</div>', unsafe_allow_html=True)  # close fixed-bar container


##=====================
# --- Language setting ---
is_ar_ui = False  # True if Arabic

# --- Labels ---
action_labels_en = {
    "summarize": "Summarize",
    "flashcards": "Flashcards",
    "resources": "Resources",
    "quiz": "Quiz",
    "report": "Report",
    "grammar": "Grammar",
}
action_labels_ar = {
    "summarize": "تلخيص",
    "flashcards": "بطاقات",
    "resources": "مصادر",
    "quiz": "اختبار",
    "report": "تقرير",
    "grammar": "تصحيح",
}

# --- Action list ---
actions = ["summarize", "flashcards", "resources", "quiz", "report", "grammar"]

# --- Columns for buttons ---
btn_cols = st.columns([1]*len(actions))
clicked_action_local = None
#########
# --- Function to open dialog ---
# --- QUIZ Dialog ---
@st.dialog("🧠 Quiz Settings")
def open_quiz_dialog():
    output_placeholder = st.empty()

    # Initialize quiz session state
    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = None
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}
    if "quiz_started" not in st.session_state:
        st.session_state.quiz_started = False
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False
    if "quiz_num_questions" not in st.session_state:
        st.session_state.quiz_num_questions = 5
    if "quiz_saved" not in st.session_state:
        st.session_state.quiz_saved = False

    # --- Store per-session quiz history ---
    if "quiz_history" not in st.session_state:
        st.session_state.quiz_history = {}  # store per session
    if sid not in st.session_state.quiz_history:
        st.session_state.quiz_history[sid] = []  # initialize for this session

    # --- Step 0: Settings ---
    if not st.session_state.quiz_started:
        st.markdown("### ⚙️ Quiz Options")
        difficulty = st.selectbox("Select quiz difficulty:", ["Easy", "Medium", "Hard"])
        st.session_state.quiz_num_questions = st.slider(
            "Number of questions:", 1, 10, st.session_state.quiz_num_questions
        )

        if st.button("Start Quiz"):
            st.session_state.quiz_started = True
            st.session_state.quiz_submitted = False

            payload = {
                "text": "",
                "lang": "en",
                "difficulty": difficulty.lower(),
                "num_questions": st.session_state.quiz_num_questions,
            }

            with st.spinner("Generating quiz... ⏳"):
                try:
                    resp = requests.post(f"{BACKEND}/session/{sid}/generate/quiz", data=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_quiz = data.get("reply", "")
                        match = re.search(r"(\[.*\])", raw_quiz, re.DOTALL)
                        if match:
                            try:
                                st.session_state.quiz_data = json.loads(match.group(1))
                            except Exception:
                                st.session_state.quiz_data = []
                                st.error("Failed to parse quiz JSON from backend.")
                        else:
                            st.session_state.quiz_data = []
                            st.error("No quiz JSON found in backend response.")
                        st.rerun()
                    else:
                        st.error(f"Failed: {resp.text}")
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- Step 1: Show Questions ---
    elif st.session_state.quiz_started and not st.session_state.quiz_submitted:
        st.markdown("### 📝 Quiz Questions:")
        for i, q in enumerate(st.session_state.quiz_data):
            st.markdown(f"**Q{i+1}: {q['question']}**")
            options = q.get("options", [])
            st.session_state.quiz_answers[i] = st.radio(
                f"Select your answer for Q{i+1}", options, key=f"quiz_q{i}"
            )

        if st.button("Submit Quiz"):
            with st.spinner("Submitting quiz... ⏳"):
                time.sleep(1)
                st.session_state.quiz_submitted = True
                st.rerun()

    # --- Step 2: Show Results ---
    elif st.session_state.quiz_submitted:
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

        st.markdown("### Quiz Results:")
        for idx, r in enumerate(results, start=1):
            color = "green" if r["is_correct"] else "red"
            st.markdown(f"**Q{idx}:** {r['question']}")
            st.markdown(f"- **Your answer:** <span style='color:{color}'>{r['your_answer']}</span>", unsafe_allow_html=True)
            st.markdown(f"- **Correct answer:** <span style='color:green'>{r['correct_answer']}</span>", unsafe_allow_html=True)
            st.markdown("✅ Correct!" if r["is_correct"] else "❌ Incorrect")
            st.markdown("---")

        # --- Save this attempt for current session ---
        if not st.session_state.quiz_saved:
            st.session_state.quiz_history[sid].append(results)
            st.session_state.quiz_saved = True

        total = len(results)
        correct = sum(r["is_correct"] for r in results)
        st.markdown(f"### 🏆 Score: {correct}/{total} ({(correct/total)*100:.1f}%)")
        st.info(f"📊 Total quiz attempts in this session: {len(st.session_state.quiz_history[sid])}")

        if st.button("Take Another Quiz"):
            st.session_state.quiz_data = None
            st.session_state.quiz_answers = {}
            st.session_state.quiz_started = False
            st.session_state.quiz_submitted = False
            st.session_state.quiz_saved = False
            st.rerun()


# --- REPORT Dialog ---
@st.dialog("📊 Generate Report")
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
                    resp = requests.post(f"{BACKEND}/session/{sid}/generate/report", data=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        report_output = data.get("reply", "No response from backend.")
                        st.markdown("### ✅ Generated Report:")
                        st.markdown(report_output)
                    else:
                        st.error(f"Failed: {resp.text}")
                except Exception as e:
                    st.error(f"Error: {e}")


# --- GRAMMAR Dialog ---
@st.dialog("🔤 Grammar Checker")
def open_grammar_dialog():
    output_placeholder = st.empty()
    text = st.text_area("Enter text to check grammar:")
    if st.button("Check Grammar"):
        payload = {"text": text, "lang": "en"}
        with st.spinner("Checking grammar... ⏳"):
            try:
                resp = requests.post(f"{BACKEND}/session/{sid}/generate/grammar", data=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    grammar_output = data.get("reply", "No response from backend.")
                    output_placeholder.markdown("### ✅ Grammar Check Result:")
                    output_placeholder.markdown(grammar_output)
                else:
                    output_placeholder.error(f"Failed: {resp.text}")
            except Exception as e:
                output_placeholder.error(f"Error: {e}")



#########

# --- Create buttons ---
for idx, (col, action) in enumerate(zip(btn_cols, actions)):
    label = action_labels_ar[action] if is_ar_ui else action_labels_en[action]
    with col:
        if st.button(label, key=f"action_btn_{action}_{idx}", use_container_width=True):
            clicked_action_local = action

# # Check if file uploaded
# file_uploaded = st.session_state.get("last_uploaded", None)

# # --- Create buttons with upload check ---
# for idx, (col, action) in enumerate(zip(btn_cols, actions)):
#     label = action_labels_ar[action] if is_ar_ui else action_labels_en[action]
#     with col:
#         # Disable if no file uploaded and not grammar
#         disabled = not file_uploaded and action != "grammar"
#         if st.button(label, key=f"action_btn_{action}_{idx}", use_container_width=True, disabled=disabled):
#             clicked_action_local = action

# # --- Warn user if clicking disabled buttons ---
# if not file_uploaded:
#     st.info("📄 Please upload a file first to use these features.")

# --- Handle clicks ---
if clicked_action_local:
    if clicked_action_local == "quiz":
        open_quiz_dialog()
    elif clicked_action_local == "report":
        open_report_dialog()
    elif clicked_action_local == "grammar":
        open_grammar_dialog()
    else:
        # Handle normal actions (summarize, flashcards, resources, etc.)
        st.session_state["clicked_action"] = clicked_action_local
        st.session_state["processing"] = True
        st.rerun()

# ---------- JavaScript: Enter-to-send & voice transcription ----------
js_code = """
<script>
const input = window.parent.document.querySelector('input[id="main_input_text"]');

// send on Enter
if (input) {
  input.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      // click the send button with text '➤'
      let buttons = window.parent.document.querySelectorAll('button');
      for (let b of buttons) {
        if (b.innerText && b.innerText.trim() === '➤') {
          b.click();
          break;
        }
      }
    }
  });
}

// voice recognition function (Web Speech API)
function startRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert('Speech Recognition API not supported in this browser.');
    return;
  }

  // try English first
  let recognition = new SpeechRecognition();
  recognition.lang = 'en-US';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onresult = (event) => {
    let text = event.results[0][0].transcript;
    const arabicRegex = /[\\u0600-\\u06FF]/;
    if (arabicRegex.test(text)) {
      // Looks Arabic, retry in Arabic
      let rec2 = new SpeechRecognition();
      rec2.lang = 'ar-SA';
      rec2.interimResults = false;
      rec2.maxAlternatives = 1;
      rec2.onresult = (ev2) => {
        const t2 = ev2.results[0][0].transcript;
        if (input) {
          input.value = t2;
          input.dispatchEvent(new Event('change', { bubbles: true }));
        }
      };
      rec2.start();
      return;
    }

    // English result
    if (input) {
      input.value = text;
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }
  };

  recognition.onerror = (e) => {
    // fallback to Arabic directly
    let rec2 = new SpeechRecognition();
    rec2.lang = 'ar-SA';
    rec2.interimResults = false;
    rec2.maxAlternatives = 1;
    rec2.onresult = (ev2) => {
      const t2 = ev2.results[0][0].transcript;
      if (input) {
        input.value = t2;
        input.dispatchEvent(new Event('change', { bubbles: true }));
      }
    };
    rec2.start();
  };

  recognition.start();
}

// bind 🎤 button click
let voice_btn = null;
let allButtons = window.parent.document.querySelectorAll('button');
for (let b of allButtons) {
  if (b.innerText && b.innerText.trim() === '🎤') {
    voice_btn = b;
    break;
  }
}
if (voice_btn) {
  voice_btn.onclick = () => startRecognition();
}
</script>
"""
st_html(js_code, height=0)

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

# ---------- Handle send (chat) ----------
# if send_clicked:
#     user_text = st.session_state.get("main_input_text", "").strip()
#     # st.session_state["processing"] = True

#     if user_text != "":
#         st.session_state["processing"] = True
#         try:
#             resp = requests.post(f"{BACKEND}/session/{sid}/message", data={"text": user_text})
#             resp.raise_for_status()
#             data = resp.json()
#             st.session_state["messages"] = data["session"]["messages"]
#         except Exception as e:
#             st.error(f"Error: {e}")
#         finally:
#             st.session_state["processing"] = False
#             st.rerun()


# ---------- Handle action buttons (summarize, quiz, etc.) ----------
if st.session_state.get("clicked_action"):
    which_action = st.session_state["clicked_action"]
    add_text = st.session_state.get("main_input_text", "")
    lang_pref = st.session_state.get("action_lang", "en")

    st.session_state["processing"] = True
    try:
        resp = requests.post(
            f"{BACKEND}/session/{sid}/generate/{which_action}",
            data={"text": add_text, "lang": lang_pref},
        )
        resp.raise_for_status()
        data = resp.json()
        st.session_state["messages"] = data["session"]["messages"]
    except Exception as e:
        st.error(f"Action error: {e}")
    finally:
        st.session_state["processing"] = False
        st.session_state["clicked_action"] = None
        st.rerun()