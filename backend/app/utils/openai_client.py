from openai import OpenAI
from ..settings import get_settings

_settings = get_settings()
client = OpenAI(api_key=_settings.OPENAI_API_KEY)

def generate_title(prompt: str) -> str:
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Generate a short (3–5 words) title summarizing the topic of this text. Or generate the title based on the action. Only return the title."},
                {"role": "user", "content": prompt},
            ],
        )
        title = (res.choices[0].message.content or "").strip().strip('"')
        if not title:
            raise ValueError("empty")
        parts = title.split()
        return " ".join(parts[:10]) if len(parts) > 10 else title
    except Exception:
        s = (prompt or "").strip()
        if not s:
            return "New Session"
        return " ".join(s.split()[:6])

def detect_language_simple(text: str) -> str:
    if any("\u0600" <= ch <= "\u06FF" or "\u0750" <= ch <= "\u077F" for ch in text):
        return "ar"
    return "en"

def chat(messages):
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    return res.choices[0].message.content
