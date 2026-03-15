## 🌟 Key Features

### 🤖 Intelligent Agent Architecture
This application uses a dual-agent design to analyze and interact with medical reports.

**Analysis Agent**
- Performs detailed medical report analysis
- Uses contextual learning from previous analyses
- Includes a built-in medical knowledge base for better explanations

**Chat Agent**
- Allows users to ask follow-up questions about the report
- Implements Retrieval-Augmented Generation (RAG)
- Uses FAISS vector search and HuggingFace embeddings for contextual responses

---

### 🧠 Smart Model Cascade
The system integrates multiple LLM models via the Groq API with automatic fallback.

Model priority flow:

Primary → Secondary → Tertiary → Backup

This ensures high reliability even if one model becomes unavailable.

---

### 💬 Persistent Chat Sessions
Users can create multiple report analysis sessions.

Each session stores:
- Uploaded medical report
- Generated analysis
- Chat history

All session data is securely stored in Supabase.

---

### 📄 Flexible Report Input
Users can analyze reports in two ways:

• Upload a medical PDF report  
• Use a built-in sample report for testing

System validation:
- Maximum file size: 20MB
- Maximum pages: 50
- File type and content validation included

---

### 🔒 Secure Authentication
Authentication is handled using Supabase Auth with:

- Secure login and signup
- Session validation
- Configurable session timeout

---

### 📊 Session History
Users can:
- View previous sessions
- Switch between reports
- Delete old sessions
- Continue conversations after page reload

---

### 🎨 Modern UI
The application is built using Streamlit with a responsive interface.

Features include:
- Sidebar session manager
- User greeting
- Real-time feedback
- Clean and intuitive design

---

## 🛠 Tech Stack

**Frontend**
- Streamlit

**AI / Machine Learning**
- Groq LLM API
- LangChain
- HuggingFace Embeddings
- FAISS Vector Store

**Database**
- Supabase (PostgreSQL)

Tables used:
- users
- chat_sessions
- chat_messages

**Document Processing**
- PDFPlumber (PDF text extraction)
- filetype (file validation)

**Core Libraries**
- LangChain
- sentence-transformers
- FAISS (CPU)

---

## 🚀 Installation

### Requirements

- Python 3.8+
- Streamlit
- Supabase account
- Groq API key

---

1️⃣ Clone the Repository

```bash
git clone https://github.com/adhityamarp/AI_doctor_Agent.git
cd AI_doctor_Agent

2️⃣ Install Dependencies
pip install -r requirements.txt
3️⃣ Configure Environment Variables

Create the file:

.streamlit/secrets.toml

Add the following:

SUPABASE_URL = "your-supabase-url"
SUPABASE_KEY = "your-supabase-key"
GROQ_API_KEY = "your-groq-api-key"
4️⃣ Setup Database

Run the SQL script located at:

public/db/script.sql

This will create the required tables:

users

chat_sessions

chat_messages

5️⃣ Run the Application
streamlit run src/main.py

📁 Project Structure

AI_doctor_Agent
│
├── requirements.txt
├── README.md
│
├── src
│   ├── main.py
│   ├── auth
│   │   ├── auth_service.py
│   │   └── session_manager.py
│   │
│   ├── components
│   │   ├── analysis_form.py
│   │   ├── auth_pages.py
│   │   ├── header.py
│   │   └── sidebar.py
│   │
│   ├── agents
│   │   ├── analysis_agent.py
│   │   ├── chat_agent.py
│   │   └── model_manager.py
│   │
│   ├── services
│   │   └── ai_service.py
│   │
│   ├── config
│   │   ├── app_config.py
│   │   ├── prompts.py
│   │   └── sample_data.py
│   │
│   └── utils
│       ├── validators.py
│       └── pdf_extractor.py
│
└── public
    └── db
        ├── script.sql
        └── schema.png
🤝 Contributing

Contributions are welcome!

Ways to contribute:

Improve documentation

Report issues

Suggest new features

Submit pull requests

👨‍💻 Author

Marpu Adhitya
AI / ML Engineer
Email: adhimarpu@gmail.com
