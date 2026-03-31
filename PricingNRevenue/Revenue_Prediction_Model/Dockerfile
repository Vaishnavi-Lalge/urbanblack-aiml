# ▣ Base Image
FROM python:3.11-slim

# ▣ Environment Variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ▣ Set Working Directory
WORKDIR /app

# ▣ Install System Dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ▣ Copy Requirements First (for caching)
COPY requirements.txt .

# ▣ Install Python Dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ▣ Copy Project Files
COPY . .

# ▣ Expose Port
EXPOSE 8000

# ▣ Run FastAPI with Uvicorn
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]