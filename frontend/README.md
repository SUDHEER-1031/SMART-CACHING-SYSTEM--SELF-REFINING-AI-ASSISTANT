# AuraCache: Smart Caching System

# TEAM MEMBERS DETAILS (WORK DONE BY)
1. Akhilesh .C
   Reg No: 23X51A0503
   gmail: (23x51a0503@srecnandyal.edu.in)
2. A. Guru Naga Ajay Reddy
   Reg No: 23X51A0507   
   gmail: (23x51a0507@srecnandyal.edu.in)
3. D. Srinivas
   Reg No: 23X51A0549
   gmail: (23x51a0549@srecnandyal.edu.in)
4. D. Mahammad Basha
   Reg No: 23X51A0552
   gmail: (23x51a0552@srecnandyal.edu.in)
5. B.Sudheer
   Reg No: 24X51A508
   gmail: (24x51a0508@srecnandyal.edu.in)

# Smart Cache System is a highly intelligent, self-refining AI assistant built using:

- React (Vite)
- FastAPI (Python)
- Groq API (Llama-3 Models)
- Firebase (Firestore Database)
- AI Evaluator / Judge Logic
- Zero-Bloat Context Injection (Prompt Stuffing)

# The project is designed to provide:

- Blazing fast AI responses
- Reduced API costs through smart caching
- Continuous self-improvement via an AI Judge
- Custom knowledge injection without heavy vector databases
- A seamless, premium, and distraction-free user interface

---

# Features

## AI Chat Assistant

AuraCache can answer complex questions dynamically using advanced models openai/gpt-oss-20b & openai/gpt-oss-120b. It provides formatted, easy-to-read Markdown responses directly in a sleek, minimalist UI.

---

## Smart Caching & Self-Refining AI (The Judge)

Smart Cache System doesn't just store answers; it evaluates them:

- It checks Firebase for a previously saved answer to your exact question.
- It concurrently fetches a fresh answer from a fast LLM.
- A massive "Judge" LLM compares the cached answer vs. the new answer.
- If the new answer is better, it automatically overwrites the Firebase database to ensure the cache gets smarter over time.

---

## Minimalist Professional UI

The frontend is built for enterprise-grade elegance:

- Creamy off-white editorial background.
- Floating, borderless input field.
- Seamless scrolling with hidden scrollbars.
- Real-time Markdown rendering for code blocks, lists, and headers.

---

# Project Structure

```text
Smart Cache System/
│
├── backend/
│   ├── main.py                     # FastAPI server and core Judge logic
│   ├── policy.txt                  # Custom knowledge base file
│   ├── firebase-credentials.json   # Firebase authentication
│   ├── requirements.txt            # Python dependencies
│   └── .env                        # Groq API keys (api_request, api_compare)
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx                 # React UI and API connection
│   │   └── App.css                 # UI styling
│
└── README.md