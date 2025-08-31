TalentScout Hiring Assistant
Overview
The TalentScout Hiring Assistant is a Streamlit-based web application designed as an AI-powered recruitment screening tool for TalentScout, a recruitment agency adaptable to any domain (default: technology). It leverages Google's Gemini AI for conversational screening, Hugging Face Transformers for advanced NLP (sentiment analysis and Named Entity Recognition), and SQLite for secure, persistent data storage. The app collects candidate information, asks tailored questions based on their skills, and securely stores data with encryption, overcoming limitations of the original implementation.
Features and Functionality
Core Functionality

Conversational Screening:
Greets candidates warmly and collects details step-by-step: Full Name, Email, Phone, Years of Experience, Desired Position(s), Location, and Key Skills/Stack.
Confirms skills and generates 3-5 challenging, domain-specific questions per skill area, posed one at a time with neutral acknowledgment.
Outputs a JSON block with gathered data upon completion.


AI Response Generation:
Uses Gemini AI (gemini-1.5-flash/2.5-flash) for dynamic, conversational responses.
Implements exponential backoff retry logic to handle API rate limits.
Configurable generation: temperature (0.3) and max tokens (500).


Sentiment Analysis:
Uses Hugging Face's distilbert-base-uncased-finetuned-sst-2-english for accurate sentiment analysis, with TextBlob as fallback.
Logs sentiment internally (e.g., "Positive (0.85)") without affecting responses.


Candidate Data Extraction:
Employs Hugging Face's dbmdz/bert-large-cased-finetuned-conll03-english for precise NER to extract Name, Location, Organization, etc.
Uses regex fallback for email and phone to improve accuracy.


Data Persistence:
Stores candidate data in an SQLite database (candidates.db) with timestamps.
Encrypts sensitive fields (email, phone) using cryptography.Fernet.


JSON Parsing:
Robustly extracts JSON from AI responses with validation for json and  delimiters, handling malformed or missing JSON gracefully.



UI and Admin Features

Chat Interface:
Dark-themed UI with custom CSS for a modern look.
Displays chat history (excluding system prompt) and a "Thinking..." spinner during AI responses.


Admin Sidebar:
Shows decrypted candidate data in JSON format.
Logs sentiment for each user input (truncated to 40 characters).
Includes a "Clear Conversation" button to reset session state.


Error Handling:
Handles missing dependencies, API failures, and JSON parsing errors with warnings.
Ensures app continuity even if JSON parsing or NLP fails.



Limitations Addressed

Real-Time Persistence: Uses SQLite instead of local file storage; supports cloud DB integration (e.g., PostgreSQL) for production.
API Rate Limits: Implements retry logic and recommends Gemini's paid tier.
NLP Accuracy: Uses advanced Hugging Face models and regex fallback for better accuracy.
Security: Encrypts sensitive data and recommends HTTPS deployment.
Domain Flexibility: Configurable DOMAIN environment variable (e.g., technology, finance, healthcare).

Installation and Setup
Prerequisites

Python 3.8+.
Google Gemini API key (obtain from Google AI Studio).
Optional: GPU for faster Hugging Face model inference.

Dependencies
Install required packages:
pip install streamlit google-generativeai textblob transformers torch cryptography python-dotenv

Configuration

API Key and Domain:

Create a .env file:GEMINI_API_KEY=your_api_key_here
DOMAIN=technology  # Optional: set to finance, healthcare, etc.


Alternatively, add GEMINI_API_KEY and DOMAIN to Streamlit secrets (secrets.toml).


Database:

SQLite database (candidates.db) is created automatically.
For production, configure a cloud database (e.g., PostgreSQL) with libraries like psycopg2.


Run the App:
streamlit run app.py


Access at http://localhost:8501.


Production Deployment:

Deploy with HTTPS (e.g., Streamlit Cloud, Heroku, AWS).
Use Gemini's paid tier to avoid rate limits.
Integrate a cloud database for scalability.



Usage Instructions

Start Screening:

Open the app and respond to the assistant’s prompt for your full name.
Provide details (e.g., "John Doe, john@example.com, 123-456-7890") as requested.


Skill Questions:

Share your skills/stack (e.g., "Python, Django, SQL" for technology).
Answer tailored questions one by one.


Completion:

The assistant outputs a JSON block with your data.
Data is encrypted and stored in candidates.db.


Admin Monitoring:

View decrypted candidate data and sentiment logs in the sidebar.
Use "Clear Conversation" to reset for a new candidate.


Troubleshooting:

API Errors: Check API key and internet; consider paid tier.
NLP Issues: Ensure transformers and torch are installed.
JSON Parsing: Malformed JSON is logged as a warning without crashing.



File Structure

app.py: Main application script.
candidates.db: SQLite database for candidate data.
secret.key: Auto-generated encryption key for sensitive data.
.env: Environment variables (API key, domain).
README.md: This documentation.

Limitations and Notes

Scalability: SQLite is suitable for small-scale use; switch to PostgreSQL/MySQL for production.
NLP Accuracy: While improved, manual review of extracted data is recommended.
Security: Ensure HTTPS and secure DB connections in production.
API Costs: Paid Gemini tier required for high-volume usage.

Contributing
Fork the repository and submit pull requests for enhancements (e.g., cloud DB integration, additional NLP features). Report issues via GitHub.
License
MIT License. See LICENSE for details.
Contact
For support, contact [your-email@example.com].
