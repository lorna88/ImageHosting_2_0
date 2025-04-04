FROM python:3.12-alpine

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r  requirements.txt

COPY . .
COPY static/upload.html upload.html
COPY static/success.html success.html

EXPOSE 8000

CMD ["python", "app.py"]