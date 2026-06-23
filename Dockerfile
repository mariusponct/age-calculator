# Start from a small official Python image
FROM python:3.13-slim

# All following commands run inside /app in the container
WORKDIR /app

# Copy the dependency list first so Docker can cache the install layer.
COPY requirements.txt .

# Install dependencies; --no-cache-dir keeps the image smaller
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the application code
COPY main.py .

# The app reads PORT from the environment (defaults to 8080 in the code).
ENV PORT=8080
EXPOSE 8080

# Command that starts the app when the container runs
CMD ["python", "main.py"]