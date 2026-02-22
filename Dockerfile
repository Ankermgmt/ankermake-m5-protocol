# First stage: build environment
FROM python:3.11-bullseye AS build-env

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

# Configurable UID/GID for the non-root user (override with --build-arg)
ARG UID=1000
ARG GID=1000

# Create non-root user for running the application
RUN groupadd -g ${GID} ankerctl && \
    useradd -u ${UID} -g ${GID} -m -s /bin/bash ankerctl && \
    mkdir -p /home/ankerctl/.config/ankerctl && \
    chown -R ankerctl:ankerctl /home/ankerctl

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Copy the script and libraries
COPY --chown=ankerctl:ankerctl ankerctl.py /app/
COPY --chown=ankerctl:ankerctl web /app/web/
COPY --chown=ankerctl:ankerctl ssl /app/ssl/
COPY --chown=ankerctl:ankerctl static /app/static/
COPY --chown=ankerctl:ankerctl libflagship /app/libflagship/
COPY --chown=ankerctl:ankerctl cli /app/cli/

# Copy the installed dependencies from the build environment
COPY --from=build-env /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

STOPSIGNAL SIGINT

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python3 -c "import urllib.request, os; h=os.getenv('FLASK_HOST','127.0.0.1'); h='127.0.0.1' if h in ('0.0.0.0','::','') else h; urllib.request.urlopen('http://'+h+':'+os.getenv('FLASK_PORT','4470')+'/api/health',timeout=4)" 2>/dev/null || exit 1

# Run as non-root user
USER ankerctl

ENTRYPOINT ["/app/ankerctl.py"]
CMD ["webserver", "run"]
