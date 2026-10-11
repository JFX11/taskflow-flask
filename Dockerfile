FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd --create-home taskflow && mkdir -p /data && chown taskflow:taskflow /data
COPY app app
COPY wsgi.py .
USER taskflow
ENV DATABASE=/data/tasks.sqlite
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "wsgi:app"]
