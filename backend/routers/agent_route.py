import os
import asyncio
import requests
import json
from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, Response
from fastapi.responses import StreamingResponse
from io import BytesIO


from pydantic import BaseModel
from contextlib import asynccontextmanager
from bs4 import BeautifulSoup
from typing import List, Dict, Any

from pipecat.frames.frames import TextFrame, EndFrame, TTSSpeakFrame, TranscriptionFrame, TTSAudioRawFrame
from pipecat.frames.frames import InputAudioRawFrame, AudioRawFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask
from pipecat.pipeline.runner import PipelineRunner
from pipecat.services.openai import OpenAILLMService, OpenAISTTService, OpenAITTSService

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

router = APIRouter()
qa_chain = None 
@asynccontextmanager
async def lifespan(app: FastAPI):
    global qa_chain
    yield


# Store conversation history in memory
conversation_history: List[Dict[str, str]] = []

class URLRequest(BaseModel):
    url: str

class VoiceRequest(BaseModel):
    audio_data: bytes

class ImageRequest(BaseModel):
    prompt: str

@router.get("/ask")
async def ask_question(question: str):
    global qa_chain, conversation_history
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
    
    # Store in conversation history
    conversation_history.append({"role": "user", "content": question})
    conversation_history.append({"role": "assistant", "content": answer['result']})

    return {"question": question, "answer": answer['result']}

@router.websocket("/voice-chat")
async def voice_chat(websocket: WebSocket):
    await websocket.accept()
    
    # Initialize services
    stt_service = OpenAISTTService(
        name="Speech-to-Text",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    tts_service = OpenAITTSService(
        name="Text-to-Speech",
        api_key=os.getenv("OPENAI_API_KEY"),
        voice="alloy"  # Can be customized or made selectable
    )
    
    llm_service = OpenAILLMService(
        name="LLM",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4",
        system_prompt="""You are a helpful assistant that can answer questions about web documents. 
        Be concise and informative in your responses."""
    )
    
    # Create the pipeline for voice conversation
    pipeline = Pipeline([stt_service, llm_service, tts_service])
    
    try:
        while True:
            # Create a new task for each conversation turn
            task = PipelineTask(pipeline)
            runner = PipelineRunner()
            
            # Tell the client we're ready for audio
            await websocket.send_text(json.dumps({"status": "ready"}))
            
            # Receive audio data from client
            audio_data = await websocket.receive_bytes()
            
            # Convert received data to audio format Pipecat can understand
            # For WebM audio format used by browser's MediaRecorder
            
            # Queue the audio frame
            await task.queue_frames([
                # InputAudioRawFrame for STT processing
                InputAudioRawFrame(
                    audio=audio_data,
                    sample_rate=48000,  # Common sample rate
                    num_channels=1      # Mono audio
                )
            ])
            
            # End the input after sending audio
            await task.queue_frames([EndFrame()])
            
            # Process frames and handle the outputs
            async for frame in runner.stream(task):
                if isinstance(frame, TranscriptionFrame):
                    # Speech recognition result
                    transcription = frame.message.text
                    await websocket.send_text(json.dumps({
                        "type": "transcription",
                        "text": transcription
                    }))
                    
                    # Process with RAG if we have a vector store
                    if qa_chain is not None:
                        # Get context-enhanced answer
                        answer = qa_chain.invoke({"query": transcription})
                        answer_text = answer['result']
                        
                        # Use the answer in the conversation
                        await task.queue_frames([
                            TextFrame(answer_text),
                            TTSSpeakFrame(text=answer_text)
                        ])
                        
                        # Store in conversation history
                        conversation_history.append({"role": "user", "content": transcription})
                        conversation_history.append({"role": "assistant", "content": answer_text})
                    else:
                        # No RAG context available
                        response_text = "Please provide a URL to crawl first so I can answer questions about specific content."
                        await task.queue_frames([
                            TextFrame(response_text),
                            TTSSpeakFrame(text=response_text)
                        ])
                
                elif isinstance(frame, TextFrame):
                    # LLM response text
                    await websocket.send_text(json.dumps({
                        "type": "response",
                        "text": frame.text
                    }))
                    
                elif isinstance(frame, TTSAudioRawFrame):  # TTS audio output
                    # Send audio back to client
                    await websocket.send_bytes(frame.audio)  # Access the audio property
                    
            # Wait for client to indicate they're done listening
            confirmation = await websocket.receive_text()
            if json.loads(confirmation).get("status") == "complete":
                continue
                
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@router.post("/crawl")
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
