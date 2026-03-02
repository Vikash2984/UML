FROM python:3.11-slim

# Prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Streamlit config for cloud
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]