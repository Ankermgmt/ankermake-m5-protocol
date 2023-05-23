# First stage: build environment
FROM python:3.11-slim AS build-env

COPY .docker-os-detect /tmp/docker-os-detect
RUN sh /tmp/docker-os-detect

# Copy the requirements file
COPY requirements.txt .

# Disable warning about running as "root"
ENV PIP_ROOT_USER_ACTION=ignore

# Disable caching - we just want the output
ENV PIP_NO_CACHE_DIR=1

# Install the dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Second stage: runtime environment
FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

RUN mkdir -p /root/.config/

# Copy the script and libraries
COPY ankerctl.py /app/
COPY web /app/web/
COPY ssl /app/ssl/
COPY static /app/static/
COPY libflagship /app/libflagship/
COPY cli /app/cli/

# Copy the installed dependencies from the build environment
COPY --from=build-env /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

STOPSIGNAL SIGINT

ENTRYPOINT ["/app/ankerctl.py"]
CMD ["webserver", "run"]
