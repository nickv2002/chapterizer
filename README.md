# Chapterize

Automatically add AI-generated chapters to videos using Docker, yt-dlp, and AssemblyAI.

## What It Does

Chapterize is a Docker-based CLI tool that:

1. **Downloads** videos from YouTube, Nebula, and other platforms using [yt-dlp](https://github.com/yt-dlp/yt-dlp)
2. **Transcribes** audio and detects chapter points using [AssemblyAI's AI API](https://www.assemblyai.com/)
3. **Embeds** the chapters into your video file with no re-encoding (preserves original quality)

The output video will have chapters that work in most video players (VLC, Kodi, Overcast, etc.).

## Requirements

- **Docker** - [Get Docker](https://docs.docker.com/get-docker/)
- **AssemblyAI API Key** - [Sign up for free](https://www.assemblyai.com/) (includes free credits)

### Optional: Cookies for authenticated sites

Some platforms like Nebula require authentication. You can provide cookies to access them.

## Quick Start

```bash
# 1. Build the Docker image
make build

# 2. Add your AssemblyAI API key
echo "YOUR_ASSEMBLYAI_API_KEY" > api-key.txt

# 3. Run with a video URL
docker run --rm -v "$PWD:/app" chapterize \
  --url "https://www.youtube.com/watch?v=pSSfzWw6lCw"
```

Or use the shortcut:

```bash
make run-example
```

This will download audio from a YouTube video and add AI-generated chapters.

> **Note:** The tool automatically reads the API key from `api-key.txt`, the `ASSEMBLYAI_API_KEY` environment variable, or the `--api-key` command-line argument (in that order).

## Setting Up Your API Key

The tool looks for your API key in this order:

1. **Command-line argument**: `--api-key YOUR_KEY`
2. **Environment variable**: `ASSEMBLYAI_API_KEY=YOUR_KEY`
3. **File**: `api-key.txt` in the working directory

### Method 1: Using api-key.txt (Recommended for local development)

```bash
cp api-key.txt.example api-key.txt
echo "YOUR_API_KEY_HERE" > api-key.txt
```

The tool will automatically use it when you run commands.

### Method 2: Using Environment Variable

```bash
export ASSEMBLYAI_API_KEY="YOUR_API_KEY_HERE"
make run-example
```

### Method 3: Using Command-line Argument

```bash
docker run --rm -v "$PWD:/app" chapterize \
  --url "https://youtube.com/watch?v=..." \
  --api-key "YOUR_API_KEY_HERE"
```

Both `api-key.txt` and `cookies.txt` are automatically gitignored and won't be committed.

## Using Cookies for Authenticated Sites

Some platforms like Nebula require authentication. To download from them:

1. **Install the extension**: [Get Cookies.txt Locally](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) for Chrome/Chromium

2. **Visit and log in**: Open Nebula (or your target platform) in Chrome while logged in

3. **Export cookies**: Click the extension icon and select "Export cookies"

4. **Save the file**: Save as `cookies.txt` in your project directory

5. **Run with cookies**:

   ```bash
   docker run --rm -v "$PWD:/app" chapterize \
     --url "https://nebula.tv/videos/your-video" \
     --cookies cookies.txt
   ```

## Usage Examples

### Download a YouTube video and add chapters

```bash
docker run --rm -v "$PWD:/app" chapterize \
  --url "https://www.youtube.com/watch?v=pSSfzWw6lCw"
```

### Download only audio (faster processing)

When you only need audio (like for a podcast), use `--audio-only`:

```bash
docker run --rm -v "$PWD:/app" chapterize \
  --url "https://www.youtube.com/watch?v=pSSfzWw6lCw" \
  --audio-only
```

This skips video processing and saves bandwidth/time.

### Download from authenticated sites (like Nebula)

```bash
docker run --rm -v "$PWD:/app" chapterize \
  --url "https://nebula.tv/videos/your-video" \
  --cookies cookies.txt
```

### Process an existing video file

If you already have a video file, skip the download step:

```bash
docker run --rm -v "$PWD:/app" chapterize \
  --input my-video.mp4
```

### Customize output file name

By default, the tool adds " - with chapters" to the filename:

```bash
docker run --rm -v "$PWD:/app" chapterize \
  --url "https://youtube.com/watch?v=..." \
  --output my-video-chapters.mp4
```

## CLI Options

```txt
--url URL             Video URL to download (supports YouTube, Nebula, etc.)
--cookies FILE        Cookies file for authentication (required for some sites)
--input FILE          Input video file (skip download)
--output FILE         Output video file (default: adds ' - with chapters' to filename)
--output-dir DIR      Output directory for processed files (default: output)
--audio-only          Download only audio, not video (faster & smaller bandwidth)
--api-key KEY         AssemblyAI API key (optional, auto-detected from api-key.txt or env var)
--work-dir DIR        Working directory (default: /app)
```

## How It Works

The tool follows these steps:

1. **Download** (if URL provided) - Uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) to download video from YouTube, Nebula, or other platforms
2. **Extract Audio** - Converts video to audio for processing (if needed)
3. **Transcribe & Detect Chapters** - Uploads to [AssemblyAI API](https://www.assemblyai.com/) for AI-powered transcription with automatic chapter detection
4. **Embed Chapters** - Uses ffmpeg to add chapters to the video file (no re-encoding, so it's fast and lossless)

## Makefile Commands

Quick shortcuts for common tasks:

```bash
make build          # Build the Docker image
make run-example    # Download and process a YouTube example
make test           # Display help and usage information
make clean          # Remove output files and Docker image
make help           # Show all available commands
```

## Tips & Notes

- **Fast processing**: Video processing uses copy codec (no re-encoding), so it's fast and preserves quality
- **Bandwidth-friendly**: Use `--audio-only` to download just audio, which saves time and bandwidth
- **Format support**: The tool uses AAC/MP4 format which supports chapters in most players (VLC, QuickTime, Overcast, etc.)
- **Processing time**: AssemblyAI transcription typically takes a few minutes for a 2-hour video
- **Output location**: Processed files are saved to the `output/` directory by default (git ignored)
- **Resume capability**: If a transcription is interrupted, the tool can resume using the saved transcript ID

## External Resources

- [yt-dlp documentation](https://github.com/yt-dlp/yt-dlp) - Video download tool
- [AssemblyAI API docs](https://www.assemblyai.com/docs) - AI transcription API
- [ffmpeg documentation](https://ffmpeg.org/documentation.html) - Audio/video processing

## License

MIT
