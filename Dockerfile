FROM python:3.11-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    assemblyai \
    yt-dlp

WORKDIR /app

# Copy main script
COPY chapterize.py /usr/local/bin/chapterize
RUN chmod +x /usr/local/bin/chapterize

ENTRYPOINT ["chapterize"]
CMD ["--help"]
