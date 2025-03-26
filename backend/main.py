from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, Response
from routers import agent_route,  image_gen_route

from fastapi.middleware.cors import CORSMiddleware



# Load environment variables
load_dotenv()

#app = FastAPI()



app = FastAPI(lifespan=agent_route.lifespan)
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

app.include_router(image_gen_route.router)
app.include_router(agent_route.router, tags=["Agent"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    