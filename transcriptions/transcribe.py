import sys
from openai import OpenAI
import os
from datetime import datetime
import yt_dlp
import re
import time

# Configure the OpenAI client
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("Error: OpenAI API key is not configured.")
    print("Please set the OPENAI_API_KEY environment variable with your API key.")
    print("You can do this by running the following command in your terminal:")
    print("export OPENAI_API_KEY='your-api-key'")
    sys.exit(1)

client = OpenAI(api_key=api_key)


def transcribe_audio(file_path, output_format):
    """
    Transcribe an audio file using OpenAI's Whisper model.

    :param file_path: Path to the audio file
    :param output_format: Desired output format for the transcription
    :return: Transcription result
    """
    try:
        with open(file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format=output_format,
            )
        return transcription
    except Exception as e:
        return f"Error during transcription: {str(e)}"


def estimate_tokens(text):
    """
    Estimate the number of tokens in a given text.

    :param text: Input text
    :return: Estimated number of tokens
    """
    return len(text) // 4  # Approximately 4 characters per token


def process_text(text):
    """
    Process the transcribed text by splitting it into chunks and formatting it into coherent paragraphs.

    :param text: Input text to process
    :return: Processed text with formatted paragraphs
    """
    try:
        MAX_TOKENS = 4000  # Adjust according to model limits
        CHUNK_SIZE = 3000  # Size of the chunk to process
        OVERLAP = 200  # Overlap to maintain context

        processed_text = ""
        start = 0
        total_chunks = len(text) // CHUNK_SIZE + 1

        print(f"Starting processing of {total_chunks} chunks...")

        for i in range(total_chunks):
            print(f"Processing chunk {i+1} of {total_chunks}...")
            end = min(start + CHUNK_SIZE, len(text))
            chunk = text[start:end]

            # Find the end of the last complete sentence
            last_period = chunk.rfind(".")
            if last_period != -1:
                end = start + last_period + 1
                chunk = text[start:end]

            if estimate_tokens(chunk) > MAX_TOKENS:
                chunk = chunk[: MAX_TOKENS * 4]

            print(f"Sending chunk {i+1} to the API...")
            start_time = time.time()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an assistant that formats text into logical paragraphs without altering the content.",
                    },
                    {
                        "role": "user",
                        "content": f"Format the following text into coherent paragraphs, maintaining the original content:\n\n{chunk}",
                    },
                ],
                max_tokens=MAX_TOKENS,
                temperature=0,
            )
            end_time = time.time()
            print(f"Chunk {i+1} processed in {end_time - start_time:.2f} seconds")

            processed_text += response.choices[0].message.content + "\n\n"

            start = end - OVERLAP

        print("Text processing completed.")
        return processed_text.strip()
    except Exception as e:
        print(f"Error processing the text: {str(e)}")
        return text


# Define valid formats
valid_formats = ["json", "text", "srt", "verbose_json", "vtt"]

# Get the output format from command line arguments or use 'text' by default
output_format = (
    sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in valid_formats else "text"
)


def is_youtube_url(url):
    """
    Check if the given URL is a valid YouTube URL.

    :param url: URL to check
    :return: True if it's a YouTube URL, False otherwise
    """
    pattern = r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/"
    return re.match(pattern, url) is not None


# Ask the user for the local audio file path or YouTube URL
input_source = input(
    "Please enter the path to the local audio file or the YouTube video URL: "
)

# Determine if it's a YouTube URL or a local file
if is_youtube_url(input_source):
    try:
        print("Step 1: Obtaining audio from YouTube...")
        # yt-dlp configuration
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": "%(id)s.%(ext)s",  # Changed to use the video ID
        }

        # Download the audio from the YouTube video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(input_source, download=True)
            video_id = info["id"]

        file_path = f"{video_id}.mp3"  # Use the video ID for the file name
        print(f"Audio downloaded: {file_path}")

        # Check if the file has been downloaded correctly
        if not os.path.exists(file_path):
            print(f"Error: The file {file_path} has not been downloaded correctly.")
            sys.exit(1)
    except Exception as e:
        print(f"Error downloading audio from YouTube: {str(e)}")
        sys.exit(1)
else:
    file_path = input_source
    if not os.path.exists(file_path):
        print(
            f"The file {file_path} does not exist. Please verify the path and try again."
        )
        sys.exit(1)
    print("Step 1: Audio file located.")

# Process the audio file
print("Step 2: Transcribing audio...")
result = transcribe_audio(file_path, output_format)
print("Transcription completed.")

# Generate the output file name
if (
    input_source.startswith(("http://", "https://", "www."))
    and "youtube.com" in input_source
):
    base_name = video_id
else:
    base_name = os.path.splitext(os.path.basename(file_path))[0]
extension = "json" if output_format in ["json", "verbose_json"] else output_format
output_file_name = f"{base_name}.{extension}"

# Save the transcription to the file
print("Step 3: Formatting and saving transcription...")
write_mode = "w" if output_format in ["text", "srt", "vtt"] else "wb"

try:
    with open(
        output_file_name,
        write_mode,
        encoding="utf-8" if output_format in ["text", "srt", "vtt"] else None,
    ) as output_file:
        if output_format in ["text", "srt", "vtt"]:
            if output_format == "text":
                print("Starting text processing...")
                result = process_text(result)
                print("Text processing completed.")
            print(f"Writing result to {output_file_name}...")
            output_file.write(result)
        else:
            # For JSON formats, we use the to_dict() method
            import json

            print("Converting result to JSON...")
            json_data = result.to_dict()
            if output_format == "json":
                print("Processing text in JSON...")
                json_data["text"] = process_text(json_data["text"])
            print(f"Writing JSON to {output_file_name}...")
            json.dump(json_data, output_file, ensure_ascii=False, indent=2)

    print(f"The transcription has been saved to the file: {output_file_name}")
    print("Step 3 completed: Transcription formatted and saved.")

except Exception as e:
    print(f"Error during step 3: {str(e)}")

# If audio was downloaded from YouTube, delete the temporary file
if (
    input_source.startswith(("http://", "https://", "www."))
    and "youtube.com" in input_source
):
    os.remove(file_path)
    print("Temporary audio file deleted.")
