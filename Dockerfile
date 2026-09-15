FROM python:3.10-slim

# Create a non-root user (Required by Hugging Face Spaces / Container platforms)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy requirements first for build caching
COPY --chown=user:user backend/requirements.txt /app/backend/

# Install CPU-only PyTorch and dependencies
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r backend/requirements.txt

# Copy model artifacts and backend source
COPY --chown=user:user models /app/models
COPY --chown=user:user backend /app/backend

# Set working directory to backend where main.py lives
WORKDIR /app/backend

# Default port
ENV PORT=7860
EXPOSE 7860

# Default CORS policy for container deployment
ENV FRONTEND_URL="*"

# Start FastAPI app with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
