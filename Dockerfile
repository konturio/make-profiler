FROM python:3.11-slim
RUN apt-get update && apt-get install -y graphviz && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt && pip install pytest
COPY . .
CMD ["pytest", "-q"]
