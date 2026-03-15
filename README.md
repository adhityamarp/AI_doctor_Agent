🌟 Key Capabilities
🤖 Intelligent Agent System

This application is powered by a dual-agent architecture designed for medical report understanding and interaction.

Analysis Engine

Performs detailed medical report analysis

Uses contextual learning from previous analyses

Integrates a built-in medical knowledge base for better explanations

Interactive Chat Agent

Enables follow-up questions about the report

Implements Retrieval-Augmented Generation (RAG) using FAISS vector search and HuggingFace embeddings

Provides contextual responses based on the uploaded report

🧠 Smart Model Selection

The system uses a multi-model cascade strategy through the Groq API.

If the primary model fails or is unavailable, the system automatically switches to fallback models.

Model priority pipeline:

Primary → Secondary → Tertiary → Backup Model

This ensures high reliability and minimal downtime.

💬 Persistent Chat Sessions

Users can manage multiple analysis sessions.

Each session stores:

Uploaded medical report

Generated analysis

Chat conversation history

Session data is securely stored in Supabase.

📄 Flexible Report Input

Users can analyze reports using two options:

• Upload a custom PDF medical report
• Use a preloaded sample report for quick testing

System validation:

Max file size: 20MB

Max pages: 50

Validates medical-report structure

🔒 Secure Authentication

Authentication is handled using Supabase Auth with:

Secure login & registration

Session validation

Configurable session timeout

📊 Session Management

The platform keeps a history of previous analyses.

Users can:

Switch between sessions

View previous reports

Delete old sessions

Continue chat conversations even after page refresh

🎨 Modern User Interface

The application is built with a responsive UI using Streamlit.

Features include:

Sidebar session manager

Personalized user greeting

Real-time analysis feedback

Clean and intuitive layout

🛠 Technology Stack
Frontend

Streamlit

AI / Machine Learning

Multi-model inference using Groq

Retrieval-Augmented Generation with LangChain

Vector search using FAISS

Embeddings via Sentence Transformers

Database

Supabase (PostgreSQL)

Database tables:

users

chat_sessions

chat_messages

Document Processing

PDFPlumber

File validation with filetype

Core Libraries

LangChain

HuggingFace embeddings

FAISS (CPU)

sentence-transformers

🚀 Installation Guide
Prerequisites

Before starting, ensure you have:

Python 3.8 or higher

Streamlit installed

A Supabase account

A Groq API key

1️⃣ Clone the Repository
git clone https://github.com/adhityamarp/AI_doctor_Agent.git
cd AI_doctor_Agent
2️⃣ Install Dependencies
pip install -r requirements.txt
3️⃣ Configure Environment Variables

Create the file:

.streamlit/secrets.toml

Add the following credentials:

SUPABASE_URL = "your-supabase-url"
SUPABASE_KEY = "your-supabase-key"
GROQ_API_KEY = "your-groq-api-key"
4️⃣ Configure the Database

The project requires three database tables:

users
chat_sessions
chat_messages

Run the SQL script located at:

public/db/script.sql

This will initialize the complete schema.

5️⃣ Launch the Application

Run the Streamlit app:

streamlit run src/main.py

After launching, open the provided local URL in your browser.

📁 Project Architecture
AI_doctor_Agent
│
├── requirements.txt
├── README.md
│
├── src
│   ├── main.py
│   │
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
🤝 Contributions

Contributions are welcome!

Ways to contribute:

Improve documentation

Report issues

Suggest new features

Submit pull requests

Please follow the repository contribution guidelines before submitting changes.

👨‍💻 Author

Marpu Adhitya
AI / ML Engineer
📧 adhimarpu@gmail.com
