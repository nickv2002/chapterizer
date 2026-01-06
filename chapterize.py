#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys

# Import assemblyai and set up API key handling
import assemblyai
import assemblyai as aai


def download_video(url, cookies_file, output_dir=".", audio_only=False):
    """Download video using yt-dlp"""
    if audio_only:
        print(f"📥 Downloading audio from {url}...")
    else:
        print(f"📥 Downloading video from {url}...")

    cmd = ["yt-dlp"]
    if cookies_file:
        cmd.extend(["--cookies", cookies_file])
    if audio_only:
        cmd.extend(["-x", "--audio-format", "m4a"])
    cmd.extend(["-o", f"{output_dir}/%(title)s.%(ext)s", url])

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Error downloading video: {result.stderr}")
        sys.exit(1)

    # Extract filename from output
    output_lines = result.stdout.split("\n")
    for line in output_lines:
        if "Merging formats into" in line or "Destination:" in line:
            # Extract filename
            if '"' in line:
                filename = line.split('"')[1]
                if os.path.exists(filename):
                    print(f"✅ Downloaded: {filename}")
                    return filename

    # Fallback: look for video file in directory
    for file in os.listdir(output_dir):
        if file.endswith((".mp4", ".mkv", ".webm", ".mp3", ".m4a")):
            filepath = os.path.join(output_dir, file)
            # Check if recently created
            if os.path.getmtime(filepath) > os.path.getmtime(__file__) - 300:
                print(f"✅ Downloaded: {filepath}")
                return filepath

    print("❌ Could not determine downloaded filename")
    sys.exit(1)


def extract_audio(video_file, output_dir="."):
    """Extract audio from video file using ffmpeg"""
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    audio_file = os.path.join(output_dir, f"{base_name}-audio.m4a")

    # Skip if already exists
    if os.path.exists(audio_file):
        print(f"✅ Audio file already exists: {audio_file}")
        return audio_file

    print("🎵 Extracting audio from video...")
    print("   This will take a few minutes for large files...\n")
    cmd = [
        "ffmpeg",
        "-i",
        video_file,
        "-vn",  # No video
        "-acodec",
        "aac",
        "-b:a",
        "128k",  # Lower bitrate for faster upload
        "-y",  # Overwrite
        audio_file,
    ]

    # Don't capture output so ffmpeg progress is visible
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("\n❌ Error extracting audio")
        sys.exit(1)

    print(f"✅ Audio extracted: {audio_file}")
    return audio_file


def transcribe_and_generate_chapters(video_file, api_key, output_dir="."):
    """Transcribe video and generate chapter metadata"""
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    transcript_id_file = os.path.join(output_dir, f"{base_name}-transcript-id.txt")

    # Check if we have a saved transcript ID (for resume)
    transcript_id = None
    if os.path.exists(transcript_id_file):
        with open(transcript_id_file, "r") as f:
            transcript_id = f.read().strip()
        print(f"\n📋 Found existing transcript ID: {transcript_id}")
        print("⏳ Checking transcript status...")

        try:
            transcript = aai.Transcript.get_by_id(transcript_id)

            if transcript.status == aai.TranscriptStatus.completed:
                print("✅ Transcript already completed!")
            elif transcript.status == aai.TranscriptStatus.error:
                print(f"❌ Previous transcript failed: {transcript.error}")
                print("🔄 Starting new transcription...")
                transcript_id = None  # Start fresh
            else:
                print(f"⏳ Transcript status: {transcript.status}")
                print("⏳ Waiting for completion...")
                transcript = transcript.wait_for_completion()
        except Exception as e:
            print(f"⚠️  Could not retrieve transcript: {e}")
            print("🔄 Starting new transcription...")
            transcript_id = None

    # Start new transcription if needed
    if transcript_id is None:
        # Extract audio first
        print("\n🎵 Step 1: Extracting audio from video...")
        audio_file = extract_audio(video_file, output_dir)

        print("\n📤 Step 2: Uploading audio to AssemblyAI...")
        config = aai.TranscriptionConfig(auto_chapters=True)

        transcriber = aai.Transcriber()
        transcript = transcriber.submit(audio_file, config)

        # Save transcript ID for resume
        with open(transcript_id_file, "w") as f:
            f.write(transcript.id)

        print(f"✅ Upload complete! Transcript ID: {transcript.id}")
        print(f"💾 Saved transcript ID to: {transcript_id_file}")
        print("⏳ Step 3: Waiting for transcription (this may take several minutes)...")
        print("   💡 You can press Ctrl+C to exit and resume later\n")

        transcript = transcript.wait_for_completion()

    print(f"\n{'=' * 60}")
    print(f"Transcription status: {transcript.status}")
    print(f"Transcript ID: {transcript.id}")
    print(f"{'=' * 60}\n")

    if transcript.status == "error":
        print(f"❌ Error: {transcript.error}")
        sys.exit(1)

    if transcript.status != "completed":
        print(f"⏳ Status: {transcript.status}")
        sys.exit(1)

    print("✅ Transcription completed successfully!")
    print(f"📊 Found {len(transcript.chapters)} chapters\n")

    # Write FFMETADATA file
    metadata_file = os.path.join(output_dir, "FFMETADATA")
    print(f"💾 Writing chapter metadata to {metadata_file}...")

    with open(metadata_file, "w") as f:
        f.write(";FFMETADATA1\n")

        for chapter in transcript.chapters:
            f.write("[CHAPTER]\n")
            f.write("TIMEBASE=1/1000\n")
            f.write(f"START={chapter.start}\n")
            f.write(f"END={chapter.end}\n")
            f.write(f"title={chapter.headline}\n")
            f.write("\n")

    print(f"   ✓ Created {metadata_file}\n")

    # Clean up transcript ID file and extracted audio on success
    if os.path.exists(transcript_id_file):
        os.remove(transcript_id_file)
        print("🧹 Cleaned up transcript ID file")

    # Clean up extracted audio file
    audio_file = os.path.join(output_dir, f"{base_name}-audio.m4a")
    if os.path.exists(audio_file):
        os.remove(audio_file)
        print("🧹 Cleaned up extracted audio file")

    return metadata_file


def add_chapters_to_video(
    input_video, metadata_file, output_video=None, output_dir="output"
):
    """Add chapters to video using ffmpeg"""
    if output_video is None:
        basename = os.path.basename(input_video)
        base, ext = os.path.splitext(basename)
        output_video = os.path.join(output_dir, f"{base} - with chapters{ext}")

    print("🎬 Adding chapters to video with ffmpeg...")
    print(f"   Input: {input_video}")
    print(f"   Output: {output_video}")

    cmd = [
        "ffmpeg",
        "-i",
        input_video,
        "-i",
        metadata_file,
        "-map_metadata",
        "1",
        "-codec",
        "copy",
        output_video,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Error adding chapters: {result.stderr}")
        sys.exit(1)

    print("\n✅ Successfully created chaptered video!")
    print(f"   📁 {output_video}\n")
    return output_video


def main():
    parser = argparse.ArgumentParser(
        description="Add AI-generated chapters to videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download from URL and add chapters
  chapterize --url "https://nebula.tv/videos/..." --cookies cookies.txt --api-key YOUR_KEY

  # Download only audio and add chapters
  chapterize --url "https://youtube.com/watch?v=..." --audio-only --api-key YOUR_KEY

  # Add chapters to existing file
  chapterize --input video.mp4 --api-key YOUR_KEY
        """,
    )

    parser.add_argument(
        "--url", help="Video URL to download (supports YouTube, Nebula, etc.)"
    )
    parser.add_argument("--cookies", help="Cookies file for authentication")
    parser.add_argument("--input", help="Input video file (skip download)")
    parser.add_argument(
        "--output",
        help="Output video file (default: adds '- with chapters' to filename)",
    )
    parser.add_argument(
        "--api-key",
        help="AssemblyAI API key (or set ASSEMBLYAI_API_KEY env var, or create api-key.txt)",
    )
    parser.add_argument(
        "--work-dir", default="/app", help="Working directory (default: /app)"
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory for processed files (default: output)",
    )
    parser.add_argument(
        "--audio-only", action="store_true", help="Download only audio, not video"
    )

    args = parser.parse_args()

    # Get API key from multiple sources (priority: arg > env > file)
    api_key = args.api_key
    if not api_key:
        api_key = os.environ.get("ASSEMBLYAI_API_KEY")
    if not api_key:
        api_key_file = os.path.join(args.work_dir, "api-key.txt")
        if os.path.exists(api_key_file):
            with open(api_key_file, "r") as f:
                api_key = f.read().strip()
    if not api_key:
        parser.error(
            "API key not found. Provide via --api-key, ASSEMBLYAI_API_KEY env var, or api-key.txt file"
        )

    # Set API key for AssemblyAI
    assemblyai.settings.api_key = api_key

    if not args.url and not args.input:
        parser.error("Either --url or --input must be specified")

    os.chdir(args.work_dir)

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Step 1: Download video if URL provided
    if args.url:
        video_file = download_video(
            args.url, args.cookies, args.output_dir, args.audio_only
        )
    else:
        video_file = args.input
        if not os.path.exists(video_file):
            print(f"❌ Error: Input file not found: {video_file}")
            sys.exit(1)

    # Step 2: Transcribe and generate chapters
    metadata_file = transcribe_and_generate_chapters(
        video_file, api_key, args.output_dir
    )

    # Step 3: Add chapters to video
    output_video = add_chapters_to_video(
        video_file, metadata_file, args.output, args.output_dir
    )

    print("🎉 All done!\n")


if __name__ == "__main__":
    main()
