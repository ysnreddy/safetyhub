# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the backend_api directory contents into the container at /app
COPY ./backend_api/ /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set default API port
ENV API_PORT 8000

# Make port 8000 available to the world outside this container (matches default API_PORT)
EXPOSE 8000

# Run main.py when the container launches, using API_PORT environment variable
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port $API_PORT"
