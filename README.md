# Agentic
This application is a RAG applications. User specifies a url and the application crawls it, store the text in a vector store (Chroma) and user can just chat with the system about the document. The project aims at giving a user the posibility to have a natural vioce to voice conversation with the provided document in the url.

# Requirements
- Python 3.12
- Docker
- Docer-compose

# Installation

```bash
 git clone https://github.com/85nnamdi/agentic.git
 cd agentic/backend/
 ```
- create a .env file
 ```nano .env``` or ```sudo nano .env```
- copy your OPEN API key into .env
 ```OPENAI_API_KEY=Get API key from OpenAI API page ```
 ```bash
 cd ..
 docker-compose up --build -d
  ```
- open in browser at **localhost:3000**


# Remote url
The application is currently running on [http://16.171.200.180/](http://16.171.200.180/) or [http://13.60.174.43/](http://13.60.174.43/).

# Testing locally
## Backend
The backend is a FastAPI backend. Therefore we can immediately use swagger documentation. via  [localhost:8000/docs ](localhost:8000/docs)
## Frontend
The frontend is a Reactjs App and is runs on [localhost:3000](localhost:3000)

# Usage
- First thing you need to do is provide the url to crawl and then you can ask your questions.


# .env content
- setup environment variables in .env file
These keys provide us with the posibility to have a natural vioce to voice conversation with the provided document.
```bash
OPENAI_API_KEY=Get API key from OpenAI API page
DAILY_SAMPLE_ROOM_URL="https://nnamdi.daily.co/philipp" # replace with your daily room URL from daily.co
DAILY_API_KEY="your_daily_api_key" # replace with your daily API key navigate to https://dashboard.daily.co/ to get it
CARTESIA_API_KEY="" # replace with your cartesia API key from https://play.cartesia.ai/keys
CARTESIA_VOICE_ID="-" # replace with your cartesia voice ID from https://play.cartesia.ai/voices/
```

# Stack
- Ollama for running LLMS like Gamma 3 locally.
- Whisper for speech-to-text trascription
- Orpheus for high-quality text-to-speech synthesis

