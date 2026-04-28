FROM python:3.11-alpine

RUN mkdir /app

WORKDIR /app

# Set environment variables
# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1

#Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip

COPY requirements.txt  /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "qualityapp/manage.py", "runserver", "0.0.0.0:8000"]