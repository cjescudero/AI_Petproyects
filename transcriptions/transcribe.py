import sys
from openai import OpenAI
import os
from datetime import datetime
import yt_dlp
import re
import time
from pydub import AudioSegment
import math

# Configure the OpenAI client
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("Error: OpenAI API key is not configured.")
    print("Please set the OPENAI_API_KEY environment variable with your API key.")
    print("You can do this by running the following command in your terminal:")
    print("export OPENAI_API_KEY='your-api-key'")
    sys.exit(1)

client = OpenAI(api_key=api_key)


def detect_language(audio_file):
    """
    Detecta el idioma del audio utilizando el modelo Whisper de OpenAI.

    :param audio_file: Archivo de audio a analizar
    :return: Código de idioma detectado
    """
    try:
        with open(audio_file, "rb") as file:
            response = client.audio.transcriptions.create(
                model="whisper-1", file=file, response_format="json"
            )
        return response.language
    except Exception as e:
        print(f"Error detecting language: {str(e)}")
        return "es"  # Devuelve español por defecto en caso de error


def transcribe_audio(file_path, output_format, language="es"):
    """
    Transcribe an audio file using OpenAI's Whisper model.
    Divide files larger than 25 MB into smaller segments if necessary.

    :param file_path: Path to the audio file
    :param output_format: Desired output format for the transcription
    :param language: Código de idioma para la transcripción (por defecto "es" para español)
    :return: Transcription result
    """
    try:
        # Detectar el idioma si no se especifica
        if language == "es":
            detected_language = detect_language(file_path)
            print(f"Detected language: {detected_language}")
            language = detected_language

        # Cargar el archivo de audio
        audio = AudioSegment.from_file(file_path)

        # Tamaño máximo del segmento en bytes (25 MB)
        max_segment_size = 25 * 1024 * 1024

        # Duración del segmento en milisegundos
        segment_duration = math.floor(
            (max_segment_size / len(audio.raw_data)) * len(audio)
        )

        transcription = ""

        # Calcular el número total de segmentos
        total_segments = math.ceil(len(audio) / segment_duration)

        # Dividir el audio en segmentos si es necesario
        for i, chunk in enumerate(audio[::segment_duration]):
            print(f"Transcribing segment {i+1} of {total_segments}...")
            chunk_file = f"temp_chunk_{i}.mp3"
            chunk.export(chunk_file, format="mp3")

            with open(chunk_file, "rb") as audio_file:
                segment_transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text",
                    language=language,  # Usar el idioma detectado
                )

            transcription += segment_transcription + " "

            # Eliminar el archivo temporal
            os.remove(chunk_file)

        # Convertir al formato de salida deseado si es necesario
        if output_format != "text":
            # Aquí deberías implementar la lógica para convertir el texto a otros formatos
            pass

        return transcription.strip()
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
).strip()

# Eliminar las comillas si están presentes
input_source = input_source.strip('"').strip("'")

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
    file_path = os.path.expanduser(input_source)
    print(f"Expanded path: {file_path}")
    if not os.path.exists(file_path):
        print(f"Error: The file {file_path} does not exist.")
        print("Please verify the path and try again.")
        print(f"Current directory: {os.getcwd()}")
        print("Files in the current directory:")
        for file in os.listdir():
            print(f"  - {file}")
        sys.exit(1)
    print("Step 1: Audio file located.")

# Process the audio file
print("Step 2: Transcribing audio...")
result = transcribe_audio(file_path, output_format)
print("Transcription completed.")

# Generate the output file name
if is_youtube_url(input_source):
    base_name = video_id
else:
    # Para archivos locales, usar la ruta completa del archivo de audio
    base_name = os.path.splitext(file_path)[0]

# Definir la extensión basada en el formato de salida
extension = output_format if output_format != "verbose_json" else "json"

output_file_name = f"{base_name}.{extension}"

# Guardar la transcripción en el archivo
print("Step 3: Formatting and saving the transcription...")
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
