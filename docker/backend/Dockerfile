FROM python:3.10-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry==1.6.1

# Copy ALL application files first
COPY . .

# Configure poetry to not use a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi