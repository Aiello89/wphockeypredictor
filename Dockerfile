# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable
ENV FLASK_APP=WPP_method_web_adv_v3.py

# Run WPP_method_web_adv when the container launches
CMD sh -c 'gunicorn --bind 0.0.0.0:$PORT --workers 1 WPP_method_web_adv_v3:app'



