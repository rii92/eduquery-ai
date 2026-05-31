FROM python:3.12-slim

WORKDIR /app

ENV UV_PYTHON_PREFERENCE=only-system \
    PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1

RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
    git gcc g++ make && \
    pip install uv --no-cache-dir && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --no-cache --python-preference only-system

COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
