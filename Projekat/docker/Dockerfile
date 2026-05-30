FROM python:3.10-slim

RUN groupadd -g 1000 appuser && \
    useradd -r -u 1000 -g appuser appuser

WORKDIR /app

COPY backend/requirements.txt /tmp/backend-requirements.txt
RUN pip install --no-cache-dir -r /tmp/backend-requirements.txt

RUN chown -R appuser:appuser /app

USER appuser

CMD ["python", "backend/app.py"]
