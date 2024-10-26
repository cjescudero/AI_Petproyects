# YouTube and Audio Transcription Tool

This Python script provides a versatile tool for transcribing audio from both local files and YouTube videos using OpenAI's Whisper model. It offers additional text processing capabilities to format the transcribed text into coherent paragraphs.

## Features

- Transcribe local audio files
- Download and transcribe audio from YouTube videos
- Multiple output formats: text, JSON, SRT, VTT
- Text processing to format transcriptions into coherent paragraphs
- Automatic handling of large transcriptions by splitting into chunks

## Prerequisites

- Python 3.6+
- OpenAI API key
- Required Python packages (install via `pip install -r requirements.txt`):
  - openai
  - yt-dlp

## Setup

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Set your OpenAI API key as an environment variable:
   ```
   export OPENAI_API_KEY='your-api-key'
   ```

## Usage

Run the script with:
