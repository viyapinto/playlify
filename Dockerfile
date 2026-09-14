FROM python:3.10-slim

# Create a non-root user (Required by Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Set the working directory
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY --chown=user:user backend/requirements.txt /app/backend/

# Install dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the models and backend directories
COPY --chown=user:user models /app/models
COPY --chown=user:user backend /app/backend

# Change working directory to backend where main.py lives
WORKDIR /app/backend

# Set the Hugging Face default port
ENV PORT=7860
EXPOSE 7860

# Allow all origins for the frontend connection (or you can specify your Vercel URL in HF Space Settings)
ENV FRONTEND_URL="*"

# Start the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
