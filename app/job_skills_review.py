import streamlit as st
import openai
import re
import random
import json
from pathlib import Path
import os
from dotenv import load_dotenv
from fpdf import FPDF
import base64
import requests

# --- Load environment ---
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OpenAI API key not found! Please add it to your .env file as OPENAI_API_KEY")
    st.stop()

client = openai.OpenAI(api_key=api_key)

# --- Files ---
history_file = Path("quiz_history.json")
if not history_file.exists():
    history_file.write_text(json.dumps([]))

# --- Streamlit page ---
st.markdown("""
# Technical Skills Quiz
Enhance your **technical expertise** by practicing questions across specialties.  

You can **generate practice questions**, **receive detailed feedback**, and **download performance reports**.
""")

# --- Auth check ---
if "token" not in st.session_state:
    st.warning("🔐 Please log in first to use this feature.")
    st.stop()

# --- User Inputs ---
specialty = st.text_input("Enter a specialty (e.g., Python, Data Science):")
num_questions = st.number_input("Number of questions:", min_value=1, max_value=20, value=5, step=1)

# --- Session State ---
for key in ["quiz", "questions_text", "quiz_submitted", "user_answers", "feedback", "recommendations", "show_history_only"]:
    if key not in st.session_state:
        st.session_state[key] = None if key not in ["quiz_submitted", "show_history_only"] else False

# --- Helper Functions ---
def generate_questions(specialty, num_questions):
    prompt = f"""
    Generate {num_questions} multiple-choice questions for learning {specialty}. 
    Each question should have 4 options labeled A, B, C, D, and indicate the correct answer.
    Format like:
    1. Question text
    A) Option 1
    B) Option 2
    C) Option 3
    D) Option 4
    Answer: B
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    questions_text = response.choices[0].message.content.strip()
    questions_text = re.sub(r"^(Here are|Below are).*?:", "", questions_text, flags=re.I)
    return questions_text

def parse_questions(text):
    questions = []
    pattern = re.compile(
        r"\d+[\.\)]\s*(.*?)\s*A\)\s*(.*?)\s*B\)\s*(.*?)\s*C\)\s*(.*?)\s*D\)\s*(.*?)\s*Answer[:\s]*([A-D])",
        re.S | re.I
    )
    for match in pattern.finditer(text):
        q = {
            "question": match.group(1).strip(),
            "options": [match.group(2).strip(), match.group(3).strip(), match.group(4).strip(), match.group(5).strip()],
            "answer": match.group(6).strip().upper()
        }
        questions.append(q)
    return questions

def sanitize_text(text):
    """Remove non-ASCII characters (like emojis) to prevent PDF encoding errors."""
    return text.encode('ascii', errors='ignore').decode('ascii')

def save_history(specialty, score, total, feedback, recommendations):
    history = json.loads(history_file.read_text())
    history.append({
        "specialty": specialty,
        "score": score,
        "total": total,
        "feedback": feedback,
        "recommendations": recommendations
    })
    history_file.write_text(json.dumps(history, indent=2))

def create_pdf_report(history):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Quiz Performance Report", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", '', 12)
    for idx, h in enumerate(history, 1):
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 8, f"Attempt {idx}: {sanitize_text(h.get('specialty','N/A'))}", ln=True)
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 8, f"Score: {sanitize_text(str(h.get('score','N/A')))}/{sanitize_text(str(h.get('total','N/A')))}", ln=True)
        pdf.ln(3)

        for q_idx, q in enumerate(h.get('feedback', []), 1):
            pdf.multi_cell(0, 8, f"Q{q_idx}: {sanitize_text(q.get('question',''))}")
            pdf.multi_cell(0, 8, f"- Your answer: {sanitize_text(q.get('user_answer',''))}")
            pdf.multi_cell(0, 8, f"- Correct answer: {sanitize_text(q.get('correct_answer',''))}")
            pdf.multi_cell(0, 8, f"- Result: {sanitize_text(q.get('result',''))}")
            pdf.multi_cell(0, 8, f"- Feedback: {sanitize_text(q.get('feedback',''))}")
            pdf.ln(2)

        pdf.multi_cell(0, 8, f"Overall Recommendations: {sanitize_text(h.get('recommendations',''))}")
        pdf.ln(10)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

    pdf_path = "quiz_report.pdf"
    pdf.output(pdf_path)
    return pdf_path

# --- Buttons in the same line ---
col1, col2 = st.columns(2)

with col1:
    generate_clicked = st.button("Generate Questions", key="generate_btn", use_container_width=True)

with col2:
    history_clicked = st.button("Quiz History", key="history_btn", use_container_width=True)

# --- Handle History click ---
if history_clicked:
    st.session_state.show_history_only = True
elif generate_clicked:
    st.session_state.show_history_only = False

# --- Show History Only ---
if st.session_state.show_history_only:
    history = json.loads(history_file.read_text())
    if history:
        st.markdown("### Your Quiz History")
        for idx, h in enumerate(history, 1):
            with st.expander(f"Attempt {idx}: {h.get('specialty','')} — Score: {h.get('score','')}/{h.get('total','')}"):
                for q_idx, q in enumerate(h.get('feedback', []), 1):
                    st.markdown(f"**Q{q_idx}:** {q.get('question','')}")
                    st.markdown(f"- Your answer: {q.get('user_answer','')}")
                    st.markdown(f"- Correct answer: {q.get('correct_answer','')}")
                    st.markdown(f"- Result: {q.get('result','')}")
                    st.markdown(f"- Feedback: {q.get('feedback','')}")
                st.markdown(f"**Overall Recommendations:** {h.get('recommendations','')}")
    else:
        st.info("No quiz attempts yet.")
else:
    # --- Generate Questions ---
    if generate_clicked:
        if not specialty:
            st.warning("Please enter a specialty first.")
        else:
            st.session_state.quiz = None
            st.session_state.quiz_submitted = False
            st.session_state.user_answers = {}
            st.session_state.questions_text = ""
            st.session_state.feedback = []
            st.session_state.recommendations = ""

            with st.spinner("Generating questions... 🚀"):
                questions_text = generate_questions(specialty, num_questions)
                quiz = parse_questions(questions_text)
                if not quiz:
                    st.error("Failed to parse questions. Try again. ⚠️")
                else:
                    random.shuffle(quiz)
                    for q in quiz:
                        options = q['options']
                        correct_option = q['answer']
                        zipped = list(zip(["A", "B", "C", "D"], options))
                        random.shuffle(zipped)
                        q['shuffled_labels'], q['shuffled_options'] = zip(*zipped)
                        q['correct_index'] = q['shuffled_labels'].index(correct_option)

                    st.session_state.quiz = quiz
                    st.session_state.questions_text = questions_text

    # --- Quiz Form & Submit ---
    if st.session_state.quiz:
        quiz = st.session_state.quiz
        if not st.session_state.quiz_submitted:
            user_answers = {}
            with st.form("quiz_form"):
                for i, q in enumerate(quiz):
                    user_choice = st.radio(
                        f"{i+1}. {q['question']}",
                        options=["A", "B", "C", "D"],
                        format_func=lambda x, opts=q['shuffled_options'], labels=q['shuffled_labels']: f"{x}) {opts[labels.index(x)]}",
                        key=f"q_{i}"
                    )
                    user_answers[i] = user_choice

                submitted = st.form_submit_button("Submit Answers")
                if submitted:
                    st.session_state.quiz_submitted = True
                    st.session_state.user_answers = user_answers

                    # --- Evaluate & GPT Feedback ---
                    score = 0
                    feedback = []
                    for i, q in enumerate(quiz):
                        correct_label = q['shuffled_labels'][q['correct_index']]
                        correct_text = q['shuffled_options'][q['correct_index']]
                        user_label = user_answers[i]
                        user_text = q['shuffled_options'][q['shuffled_labels'].index(user_label)]

                        feedback_prompt = f"""
                        The user answered the following question in {specialty} quiz:
                        Question: {q['question']}
                        Options: {', '.join([f'{l}) {o}' for l,o in zip(q['shuffled_labels'], q['shuffled_options'])])}
                        Correct answer: {correct_label}) {correct_text}
                        User's answer: {user_label}) {user_text}
                        Provide a concise feedback starting with "Feedback:" explaining why the user's answer is correct or incorrect.
                        """
                        feedback_response = client.chat.completions.create(
                            model="gpt-4",
                            messages=[{"role":"user","content":feedback_prompt}],
                            temperature=0
                        )
                        gpt_feedback = feedback_response.choices[0].message.content.strip()

                        result = "Correct ✅" if user_label == correct_label else "Incorrect ❌"
                        if user_label == correct_label:
                            score += 1

                        feedback.append({
                            "question": q['question'],
                            "user_answer": f"{user_label}) {user_text}",
                            "correct_answer": f"{correct_label}) {correct_text}",
                            "result": result,
                            "feedback": gpt_feedback
                        })

                    # GPT Overall Recommendations
                    summary_prompt = f"""
                    Based on the user's answers in the {specialty} quiz:
                    Questions and correct answers:
                    {st.session_state.questions_text}

                    User's answers:
                    {', '.join([f'{i+1}:{ans}' for i, ans in enumerate(user_answers)])}

                    Provide concise overall recommendations and tips to improve in this specialty.
                    """
                    summary_response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[{"role":"user","content":summary_prompt}],
                        temperature=0.5
                    )
                    recommendations = summary_response.choices[0].message.content.strip()

                    st.session_state.feedback = feedback
                    st.session_state.recommendations = recommendations

                    # Save history once
                    save_history(specialty, score, len(quiz), feedback, recommendations)

    # --- Display Quiz Results ---
    if st.session_state.quiz_submitted:
        st.markdown(f"### Your Score: {len([f for f in st.session_state.feedback if 'Correct' in f['result']])}/{len(st.session_state.quiz)}")
        st.markdown("### Detailed Feedback:")
        for f in st.session_state.feedback:
            st.markdown(f"**Q:** {f['question']}")
            st.markdown(f"- Your answer: {f['user_answer']}")
            st.markdown(f"- Correct answer: {f['correct_answer']}")
            st.markdown(f"- Result: {f['result']}")
            st.markdown(f"- {f['feedback']}")
            st.write("---")
        st.markdown("### Overall Recommendations:")
        st.markdown(st.session_state.recommendations)

# --- Download PDF ---
history = json.loads(history_file.read_text())
if history:
    pdf_file = create_pdf_report(history)
    with open(pdf_file, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="quiz_report.pdf">⬇️ Download Full Quiz Report (PDF)</a>'
    st.markdown(href, unsafe_allow_html=True)
