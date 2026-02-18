FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml uv.lock* ./
RUN pip install --no-cache-dir -e . && pip install --no-cache-dir uvicorn

COPY . .

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
