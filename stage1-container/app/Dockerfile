FROM python:3.12-slim
ENV TZ=UTC PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["sh", "-c", "python seed.py && gunicorn --workers 1 --bind 0.0.0.0:5000 app:app"]