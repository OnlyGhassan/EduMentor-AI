import streamlit as st
import requests

BACKEND = "http://127.0.0.1:8000/generate"

st.title("Job-Related Technical Skills Review 💼")

st.markdown("""
Enhance your **technical expertise** by reviewing and strengthening your skills across various specialties.  
You can **generate practice questions**, **receive explanations**, and **get feedback** to prepare for:
- **Technical interviews**
- **Professional certifications**
- **Career advancement in your chosen field**

Simply select a specialty below to get started.
""")

specialties = [
    "Angular",
    "ASP.Net Core",
    "Blockchain",
    "Cloud",
    "Data Analysis",
    "Data Science",
    "Database",
    "DevOps",
    "Ethical Hacking",
    "Flutter",
    "Generative AI",
    "IT Support",
    "Java",
    "Laravel",
    "Machine Learning",
    "Network",
    "Python",
    "React",
    "UI/UX"
]

specialty = st.selectbox("Choose a specialty:", specialties)

if st.button("Generate Questions"):
    st.info("This feature is coming soon! 🚧")
