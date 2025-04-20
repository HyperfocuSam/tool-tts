# Use an official Python runtime as a parent image
# Using slim-bullseye for a smaller image size, includes Debian package manager (apt)
FROM python:3.11-slim-bullseye

# Set the working directory in the container
WORKDIR /app

# Install ffmpeg
# Update package list and install ffmpeg, then clean up apt cache to reduce image size
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
# This includes main.py and the templates directory
COPY . .

# Make port 8000 available to the world outside this container
# Hosting platforms will map this internal port to an external one.
EXPOSE 8000

# Define environment variable for the port (useful for some platforms, though Gunicorn often uses --bind)
# ENV PORT=8000 # Optional, depends on platform

# Command to run the application using Gunicorn
# -w 4: Use 4 worker processes (adjust based on server resources)
# -k uvicorn.workers.UvicornWorker: Use Uvicorn workers for ASGI compatibility
# main:app: The application instance to run (app in main.py)
# --bind 0.0.0.0:8000: Listen on all network interfaces on port 8000 inside the container
# Platforms like Render will automatically use the $PORT environment variable if available, overriding the :8000 here.
# Check your specific platform's documentation for how they handle port binding.
# Added --timeout 300 to allow 5 minutes for worker processes to handle requests (e.g., transcription)
# Reduced workers from 4 to 2 to lower memory usage
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000", "--timeout", "300"]
