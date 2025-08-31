import streamlit as st
import google.generativeai as genai
import json
import os
import sqlite3
from cryptography.fernet import Fernet
import base64
import time
import re

# Streamlit page config
st.set_page_config(page_title="TalentScout Hiring Assistant", page_icon="🤖", layout="wide")

# ---------------------- 📦 NLP Imports ----------------------
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

try:
    from transformers import pipeline
    HF_AVAILABLE = True
    sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")
    ner_pipeline = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english", grouped_entities=True)
except ImportError:
    HF_AVAILABLE = False
    sentiment_pipeline, ner_pipeline = None, None
    st.warning("⚠️ Hugging Face transformers not installed. Run: pip install transformers torch")

# ---------------------- 🔑 Gemini API Setup ----------------------
api_key = None
try:
    if 'GEMINI_API_KEY' in st.secrets:
        api_key = st.secrets['GEMINI_API_KEY']
except Exception:
    pass

if not api_key:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
    except ImportError:
        pass
    except Exception:
        pass

try:
    genai.configure(api_key=api_key)
    st.success("✅ Gemini API configured successfully! Use paid tier in production to avoid rate limits.")
except Exception as e:
    st.error(f"Failed to configure Gemini API: {str(e)}")
    st.stop()

# ---------------------- 🤖 System Prompt ----------------------
DOMAIN = os.getenv('DOMAIN', 'technology')  # Configurable for any domain
SYSTEM_PROMPT = f"""
You are an intelligent Hiring Assistant chatbot for TalentScout, a recruitment agency specializing in {DOMAIN} placements.
Your role is to assist in the initial screening of candidates by gathering details and asking tailored questions.
Key Guidelines:
- Greet the candidate warmly: "Welcome to TalentScout! I'm here to help with your initial screening for {DOMAIN} positions. I'll gather some basic info and ask relevant questions based on your skills."
- Gather information step-by-step: Full Name, Email Address, Phone Number, Years of Experience, Desired Position(s), Current Location, Key Skills/Stack.
- Confirm skills and generate 3-5 relevant, challenging but fair questions for each major skill area.
- Pose questions one at a time, acknowledge responses, and proceed.
- Conclude politely after all questions.
- Analyze sentiment internally, respond neutrally.
- Output a JSON block with gathered data (e.g., ```json
"""

# ---------------------- 🔮 Gemini Response Function ----------------------
def get_llm_response(messages, retries=3, backoff_factor=2):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = ""
        for msg in messages:
            if msg["role"] == "system":
                prompt += msg["content"] + "\n\n"
            elif msg["role"] == "user":
                prompt += f"Candidate: {msg['content']}\n\n"
            elif msg["role"] == "assistant":
                prompt += f"Assistant: {msg['content']}\n\n"

        for attempt in range(retries):
            try:
                response = model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.3,
                        "max_output_tokens": 500,
                    }
                )
                return response.text.strip()
            except Exception as e:
                if "rate limit" in str(e).lower() and attempt < retries - 1:
                    sleep_time = backoff_factor ** attempt
                    time.sleep(sleep_time)
                else:
                    raise e
        return "⚠️ Rate limit exceeded after retries. Please try again later or upgrade to paid tier."
    except Exception as e:
        return f"⚠️ Error generating response: {str(e)}"

# ---------------------- 😊 Sentiment Analysis ----------------------
def analyze_sentiment(text):
    try:
        if HF_AVAILABLE and sentiment_pipeline:
            result = sentiment_pipeline(text)[0]
            return f"{result['label']} ({result['score']:.2f})"
        elif TEXTBLOB_AVAILABLE:
            blob = TextBlob(text)
            score = blob.sentiment.polarity
            if score > 0.5:
                return "Positive"
            elif score < -0.5:
                return "Negative"
            else:
                return "Neutral"
        else:
            return "N/A (No sentiment model available)"
    except Exception as e:
        return f"Error: {str(e)}"

# ---------------------- 📌 Candidate Info Extraction ----------------------
def extract_candidate_info(text):
    extracted_data = {}
    try:
        if HF_AVAILABLE and ner_pipeline:
            entities = ner_pipeline(text)
            for ent in entities:
                label = ent['entity_group']
                word = ent['word']
                if label in ["PER", "PERSON"]:
                    extracted_data["Name"] = word
                elif label in ["LOC", "GPE"]:
                    extracted_data["Location"] = word
                elif label == "ORG":
                    extracted_data["Organization"] = word
        # Fallback regex for email and phone
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if emails:
            extracted_data["Email"] = emails[0]
        phones = re.findall(r'\b(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})\b', text)
        if phones:
            extracted_data["Phone"] = ' '.join(phones[0])
        return extracted_data
    except Exception as e:
        return {"error": str(e)}

# ---------------------- 🔒 Encryption for Security ----------------------
def get_encryption_key():
    key_file = "secret.key"
    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(key)
        return key

encryption_key = get_encryption_key()
cipher = Fernet(encryption_key)

def encrypt_data(data):
    if "Email" in data:
        data["Email"] = base64.urlsafe_b64encode(cipher.encrypt(data["Email"].encode())).decode()
    if "Phone" in data:
        data["Phone"] = base64.urlsafe_b64encode(cipher.encrypt(data["Phone"].encode())).decode()
    return data

def decrypt_data(data):
    if "Email" in data:
        data["Email"] = cipher.decrypt(base64.urlsafe_b64decode(data["Email"])).decode()
    if "Phone" in data:
        data["Phone"] = cipher.decrypt(base64.urlsafe_b64decode(data["Phone"])).decode()
    return data

# ---------------------- 💾 Database Setup ----------------------
DB_FILE = "candidates.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# ---------------------- 🎨 Custom Styling ----------------------
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; font-family: 'Segoe UI', Tahoma, sans-serif; }
    .stChatFloatingContainer { border: 1px solid #444; border-radius: 12px; padding: 15px; background-color: #121212; }
    .stButton > button { background-color: #1a73e8; color: white; font-weight: 600; border-radius: 6px; }
    .stButton > button:hover { background-color: #155ab6; }
    </style>
""", unsafe_allow_html=True)

st.title("TalentScout Intelligent Hiring Assistant 🤖")
st.subheader(f"Your AI-powered recruitment screening partner for {DOMAIN}")

# ---------------------- 💾 Session State ----------------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    intro_message = (
        f"👋 Welcome to **TalentScout**! I'm your AI Hiring Assistant for {DOMAIN} placements. "
        "I'll guide you through the initial screening process. "
        "First, I'll collect some basic details, and then ask relevant questions based on your skills. "
        "Let's get started — could you please tell me your **full name**?"
    )
    st.session_state.messages.append({"role": "assistant", "content": intro_message})

if "candidate_data" not in st.session_state:
    st.session_state.candidate_data = {}

if "sentiment_log" not in st.session_state:
    st.session_state.sentiment_log = []

# ---------------------- 💬 Chat History ----------------------
for message in st.session_state.messages[1:]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------------------- 📝 User Input ----------------------
if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    sentiment = analyze_sentiment(prompt)
    st.session_state.sentiment_log.append({"input": prompt, "sentiment": sentiment})

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = get_llm_response(st.session_state.messages)
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})

    # Fixed JSON extraction
    if "```json" in response and "```" in response.split("```json")[1]:
        try:
            json_str = response.split("```json")[1].split("```")[0].strip()
            data = json.loads(json_str)
            st.session_state.candidate_data.update(data)
        except (IndexError, json.JSONDecodeError) as e:
            st.warning(f"⚠️ Failed to parse JSON from response: {str(e)}")
    else:
        extracted = extract_candidate_info(prompt)
        if extracted:
            st.session_state.candidate_data.update(extracted)

# ---------------------- 🛠️ Sidebar Admin Panel ----------------------
with st.sidebar:
    st.markdown("## ⚙️ Admin Panel")
    st.markdown("### 📌 Candidate Data")
    decrypted_data = decrypt_data(st.session_state.candidate_data.copy())
    st.json(decrypted_data)

    st.markdown("### 😊 Sentiment Log")
    for log in st.session_state.sentiment_log:
        st.write(f"➡️ {log['input'][:40]}... | Sentiment: **{log['sentiment']}**")

    st.markdown("---")
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.session_state.candidate_data = {}
        st.session_state.sentiment_log = []
        st.rerun()

# ---------------------- 💾 Save Candidate Data to DB ----------------------
if st.session_state.candidate_data:
    encrypted_data = encrypt_data(st.session_state.candidate_data.copy())
    cursor.execute("INSERT INTO candidates (data) VALUES (?)", (json.dumps(encrypted_data),))
    conn.commit()