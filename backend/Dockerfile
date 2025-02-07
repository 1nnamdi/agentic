FROM python:3.12

WORKDIR /app

# Copy the FastAPI app source code
COPY . .

# Install FastAPI dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install FAISS (choose the appropriate version)
# RUN pip install faiss-cpu
RUN pip install langchain-chroma
RUN pip install chromadb

# Expose the port for the FastAPI app
EXPOSE 8000

# Start the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]