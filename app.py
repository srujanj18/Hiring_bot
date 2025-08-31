import streamlit as st

# Streamlit page config
st.set_page_config(page_title="TalentScout Hiring Assistant", page_icon="🤖", layout="wide")

import google.generativeai as genai
import json
import os

# TextBlob import with error handling
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    st.warning("TextBlob not installed. Sentiment analysis will be disabled.")
    st.info("To install TextBlob, run: pip install textblob")

# Set up Gemini API key
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

# Configure Gemini
try:
    genai.configure(api_key=api_key)
    st.success("Gemini API configured successfully!")
except Exception as e:
    st.error(f"Failed to configure Gemini API: {str(e)}")
    st.stop()

# System prompt
SYSTEM_PROMPT = """
You are an intelligent Hiring Assistant chatbot for TalentScout, a fictional recruitment agency specializing in technology placements.
Your role is to assist in the initial screening of candidates by gathering details and asking tailored technical questions.
Key Guidelines:
- Greet the candidate warmly upon the first interaction: "Welcome to TalentScout! I'm here to help with your initial screening for tech positions. I'll gather some basic info and ask technical questions based on your skills."
- Gather information step-by-step in a natural conversation flow: Full Name, Email Address, Phone Number, Years of Experience, Desired Position(s), Current Location, Tech Stack (programming languages, frameworks, databases, tools).
- Once all information is gathered, confirm the tech stack and generate 3-5 relevant technical questions for each major technology in the stack to assess proficiency. Questions should be challenging but fair, covering fundamentals to advanced topics (e.g., for Python: list comprehensions, decorators; for Django: ORM, views).
- Pose questions one at a time, acknowledge the candidate's response, and proceed to the next.
- After all questions, conclude: Thank the candidate, inform them that their responses will be reviewed, and say "A recruiter will contact you soon if there's a match."
- Detect conversation-ending keywords like 'bye', 'exit', 'quit', 'end' and conclude politely.
- Maintain context and coherence. If input is unclear, ask for clarification without deviating from the purpose.
- Handle sensitive information securely; do not store or share it unnecessarily.
- Do not discuss topics outside recruitment screening.
- If the user provides answers, analyze sentiment briefly in your internal thought but respond neutrally.
- When information is complete, output a JSON block with the gathered data (e.g., ```json\n{...}\n```).

Always respond in a professional, engaging, and concise manner. [/INST]
"""

# Function to get Gemini response
def get_llm_response(messages):
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Combine messages into one prompt
        prompt = ""
        for msg in messages:
            if msg["role"] == "system":
                prompt += msg["content"] + "\n\n"
            elif msg["role"] == "user":
                prompt += f"Candidate: {msg['content']}\n\n"
            elif msg["role"] == "assistant":
                prompt += f"Assistant: {msg['content']}\n\n"

        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 500,
            }
        )
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Error generating response: {str(e)}"

# Sentiment analysis (bonus)
def analyze_sentiment(text):
    if not TEXTBLOB_AVAILABLE:
        return "N/A (TextBlob not installed)"
    try:
        blob = TextBlob(text)
        sentiment = blob.sentiment.polarity
        if sentiment > 0.5:
            return "Positive"
        elif sentiment < -0.5:
            return "Negative"
        else:
            return "Neutral"
    except Exception as e:
        return f"Error: {str(e)}"

# Custom styling
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; font-family: 'Segoe UI', Tahoma, sans-serif; }
    .stChatFloatingContainer { border: 1px solid #444; border-radius: 12px; padding: 15px; background-color: #121212; }
    .stButton > button { background-color: #1a73e8; color: white; font-weight: 600; border-radius: 6px; }
    .stButton > button:hover { background-color: #155ab6; }
    </style>
""", unsafe_allow_html=True)

st.title("TalentScout Intelligent Hiring Assistant 🤖")
st.subheader("Your AI-powered recruitment screening partner")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    # Intro greeting
    intro_message = (
        "👋 Welcome to **TalentScout**! I'm your AI Hiring Assistant. "
        "I'll guide you through the initial screening process. "
        "First, I'll collect some basic details, and then ask technical questions based on your skills. "
        "Let's get started — could you please tell me your **full name**?"
    )
    st.session_state.messages.append({"role": "assistant", "content": intro_message})

if "candidate_data" not in st.session_state:
    st.session_state.candidate_data = {}

if "sentiment_log" not in st.session_state:
    st.session_state.sentiment_log = []

# Display chat history
for message in st.session_state.messages[1:]:  # Skip system prompt
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Type your message here..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Sentiment analysis
    sentiment = analyze_sentiment(prompt)
    st.session_state.sentiment_log.append({"input": prompt, "sentiment": sentiment})

    # Assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = get_llm_response(st.session_state.messages)
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})

    # Extract JSON (if any) for candidate data
    if "```json" in response:
        try:
            json_str = response.split("```json")[1].split("```")[0]
            data = json.loads(json_str)
            st.session_state.candidate_data.update(data)
        except Exception:
            pass

# Sidebar admin panel
# --- Sidebar Styling ---
st.markdown("""
    <style>
    /* Sidebar background */
    [data-testid="stSidebar"] {
        background-color: #111111;
        padding: 20px;
        border-right: 2px solid #1a73e8;
    }

    /* Sidebar header */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #1a73e8;
        font-weight: 700;
    }

    /* Sidebar text */
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] div {
        color: #ffffff;
        font-size: 14px;
    }

    /* Sidebar JSON */
    [data-testid="stSidebar"] pre {
        background-color: #1a1a1a;
        border-radius: 8px;
        padding: 10px;
        font-size: 13px;
    }

    /* Buttons in sidebar */
    [data-testid="stSidebar"] button {
        background: linear-gradient(90deg, #1a73e8, #4285f4);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        cursor: pointer;
    }
    [data-testid="stSidebar"] button:hover {
        background: linear-gradient(90deg, #155ab6, #2a65d8);
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar content
with st.sidebar:
    st.markdown("## ⚙️ Admin Panel")
    st.markdown("### 📌 Candidate Data")
    st.json(st.session_state.candidate_data)

    st.markdown("### 😊 Sentiment Log")
    for log in st.session_state.sentiment_log:
        st.write(f"➡️ {log['input'][:40]}... | Sentiment: **{log['sentiment']}**")

    st.markdown("---")
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.session_state.candidate_data = {}
        st.session_state.sentiment_log = []
        st.rerun()
