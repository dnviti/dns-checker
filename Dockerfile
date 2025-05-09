FROM python:3.12-slim
WORKDIR /app
COPY check_dns.py .
CMD ["python", "/app/check_dns.py"]
