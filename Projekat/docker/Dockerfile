FROM python:3.10-slim

RUN groupadd -g 1000 appuser && \
    useradd -r -u 1000 -g appuser appuser

WORKDIR /app

RUN chown -R appuser:appuser /app

USER appuser

CMD ["python", "--version"]