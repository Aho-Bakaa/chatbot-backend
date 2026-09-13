FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The API key is supplied at runtime via the environment (see .env.example).
ENV GROQ_API_KEY=""

EXPOSE 10000
CMD ["uvicorn", "chatbot:app", "--host", "0.0.0.0", "--port", "10000"]
