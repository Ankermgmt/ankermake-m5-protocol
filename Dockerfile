# First stage: build environment
FROM python:3.11-bullseye AS build-env

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Second stage: runtime environment
FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

RUN mkdir -p /root/.config/

# Copy the script and libraries
COPY ankerctl.py /app/
COPY web /app/web/
COPY static /app/static/
COPY libflagship /app/libflagship/
COPY cli /app/cli/

# Copy the installed dependencies from the build environment
COPY --from=build-env /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

ENTRYPOINT ["/app/ankerctl.py"]
CMD ["webserver", "run"]
