import os
import asyncio
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup

from pipecat.frames.frames import TextFrame, EndFrame, TTSSpeakFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask
from pipecat.pipeline.runner import PipelineRunner
from pipecat.services.openai import OpenAILLMService

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

#app = FastAPI()


qa_chain = None 
@asynccontextmanager
async def lifespan(app: FastAPI):
    global qa_chain
    yield

app = FastAPI(lifespan=lifespan)
origins = [
    
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:80",
    "http://13.60.174.43:3000/",
    "http://13.60.174.43:80/",
    "http://13.60.174.43/"

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class URLRequest(BaseModel):
    url: str

@app.get("/ask")
async def ask_question(question: str):
    global qa_chain
    if qa_chain is None:
        raise HTTPException(status_code=500, detail="Please ensure the vector store is populated.")
    
    # Set up the LLM service using OpenAI
    llm = OpenAILLMService(
        name="LLM",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4"
    )
    
    
    # Define pipeline that processes text using the LLM
    pipeline = Pipeline([llm])
    task = PipelineTask(pipeline)
    runner = PipelineRunner()

    # Process the question
    answer = qa_chain.invoke({"query": question})
    await task.queue_frames([
        TextFrame(answer),
        EndFrame()
    ])

    # Run the pipeline task
    await runner.run(task)

    return {"question": question, "answer": answer['result']}

@app.post("/crawl")
async def crawl_and_store(url_request: URLRequest):
    global qa_chain 
    url = url_request.url
    content = await crawl_url(url)
    if not content:
        raise HTTPException(status_code=400, detail="Failed to crawl the URL or no content found.")
    
    # Create and store the QA chain
    qa_chain = create_retrieval_chain(content) 
    
    return {"message": f"Content from {url} has been processed and stored."}

async def crawl_url(url):
    """Fetches the page content and extracts text from paragraphs."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error if the request failed
    except requests.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return ""
    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = soup.find_all('p')
    text_content = "\n".join(p.get_text() for p in paragraphs)
    print(f"Crawled {len(text_content)} characters from {url}")
    return text_content


def create_retrieval_chain(document_text):
    """Splits the text, builds embeddings, creates a Chroma vectorstore and returns a QA chain."""
    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
    docs = splitter.split_text(document_text)
    
    # OpenAIEmbeddings will look for OPENAI_API_KEY in your environment variables.
    api_key = os.environ.get("OPENAI_API_KEY")  
    embeddings = OpenAIEmbeddings()
    
    # Create a Chroma vectorstore
    vectorstore = Chroma.from_texts(docs, embeddings)
    
    # Use ChatOpenAI instead of OpenAI for GPT-4
    llm = ChatOpenAI(model_name="gpt-4", api_key=api_key)
    
    # Create a QA chain using the vectorstore as a retriever.
    qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=vectorstore.as_retriever())
    return qa_chain

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    