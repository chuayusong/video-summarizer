import cv2
import numpy as np
import pytesseract
from PIL import Image
import time
import argparse
import subprocess
import os
import re
import urllib.request
import zipfile
import json


def get_screen_size():
    """
    Parses the output of xdpyinfo to get the screen dimensions.
    """
    try:
        result = subprocess.run(['xdpyinfo'], capture_output=True, text=True, check=True)
        match = re.search(r'dimensions:\s+(\d+)x(\d+)', result.stdout)
        if match:
            width = int(match.group(1))
            height = int(match.group(2))
            return width, height
    except (subprocess.CalledProcessError, FileNotFoundError, AttributeError):
        print("Warning: xdpyinfo not found or failed. Falling back to 1024x768.")
        return 1024, 768


def record_media(output_filename="output.mp4", duration=5, record_audio=True):
    """
    Records screen and audio for a given duration using ffmpeg.
    """
    screen_width, screen_height = get_screen_size()
    display = os.environ.get('DISPLAY')
    if not display:
        print("Error: DISPLAY environment variable not set.")
        return

    print(f"Recording for {duration} seconds using ffmpeg...")

    command = [
        'ffmpeg',
        '-y',  # Overwrite output file if it exists
        '-f', 'x11grab',
        '-video_size', f'{screen_width}x{screen_height}',
        '-i', display,
    ]

    if record_audio:
        command.extend([
            '-f', 'alsa',
            '-i', 'hw:0',  # Default audio device
            '-acodec', 'aac', # Audio codec
            '-strict', 'experimental'
        ])

    command.extend([
        '-t', str(duration),
        '-vcodec', 'libx264', # Video codec
        output_filename
    ])

    try:
        print(f"Running ffmpeg command: {' '.join(command)}")
        # In a real app, you might want to hide the output unless there's an error
        subprocess.run(command, check=True)
        print(f"Finished recording. Media saved to {output_filename}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error during ffmpeg recording: {e}")
        print("Please ensure 'ffmpeg' is installed and audio/video devices are available.")


def extract_text_from_video(video_path="output.mp4"):
    """
    Extracts text from a video file using OCR, processing one frame per second.
    Returns a set of unique text snippets found in the video.
    """
    print(f"Extracting text from {video_path}...")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video.")
        return set()

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        print("Warning: Video FPS is 0. Defaulting to 30 FPS for frame extraction.")
        fps = 30

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    unique_text = set()

    for i in range(0, frame_count, int(fps)):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if ret:
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            text = pytesseract.image_to_string(gray_frame)
            if text.strip():
                unique_text.add(text.strip())

    cap.release()
    print("Text extraction complete.")
    return unique_text


def summarize_text(text_set):
    """
    Summarizes the extracted text.
    """
    print("Summarizing text...")
    if not text_set:
        return "No text to summarize."

    summary = "\n---\n".join(text_set)
    return summary


import wave
from vosk import Model, KaldiRecognizer, SetLogLevel

MODEL_DIR = "vosk-model-small-en-us-0.15"
MODEL_URL = f"https://alphacephei.com/vosk/models/{MODEL_DIR}.zip"

def download_model():
    """
    Downloads and extracts the Vosk model if not already present.
    """
    if os.path.exists(MODEL_DIR):
        print("Vosk model already downloaded.")
        return

    print(f"Downloading Vosk model from {MODEL_URL}...")
    model_zip = f"{MODEL_DIR}.zip"

    try:
        urllib.request.urlretrieve(MODEL_URL, model_zip)
        print("Model downloaded. Extracting...")
        with zipfile.ZipFile(model_zip, 'r') as zip_ref:
            zip_ref.extractall(".")
        os.remove(model_zip)
        print("Model extracted successfully.")
    except Exception as e:
        print(f"Error downloading or extracting model: {e}")


def transcribe_audio_from_video(video_path):
    """
    Extracts audio from a video file, saves it as a WAV, and transcribes it.
    """
    print("Starting audio transcription...")
    audio_wav = "temp_audio.wav"
    transcribed_text = ""

    # 1. Extract audio to WAV using ffmpeg
    try:
        command = [
            'ffmpeg', '-y', '-i', video_path, '-vn',
            '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
            audio_wav
        ]
        print(f"Extracting audio with command: {' '.join(command)}")
        subprocess.run(command, check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error extracting audio: {e}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"STDERR: {e.stderr.decode()}")
        return "Audio extraction failed."

    # 2. Transcribe the WAV file
    if not os.path.exists(MODEL_DIR):
        return "Vosk model not found. Please run with --download-model flag."

    try:
        model = Model(MODEL_DIR)
        wf = wave.open(audio_wav, "rb")
        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)

        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            rec.AcceptWaveform(data)

        result = json.loads(rec.FinalResult())
        transcribed_text = result.get('text', '')
        print("Transcription complete.")

    except Exception as e:
        print(f"Error during transcription: {e}")
        transcribed_text = "Transcription failed."
    finally:
        if os.path.exists(audio_wav):
            os.remove(audio_wav)

    return transcribed_text


def main():
    """
    Main function to run the screen capture and summarization application via CLI.
    """
    parser = argparse.ArgumentParser(description="Screen and Audio Capture and Summarization Tool")
    parser.add_argument(
        '--mode',
        type=str,
        choices=['record', 'summarize', 'all'],
        default='all',
        help="The mode to run the application in."
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=10,
        help="Duration of the recording in seconds."
    )
    parser.add_argument(
        '--output',
        type=str,
        default='output.mp4',
        help="Filename for the output video."
    )
    parser.add_argument(
        '--input',
        type=str,
        help="Input video file to summarize. Required if mode is 'summarize'."
    )
    parser.add_argument(
        '--no-audio',
        action='store_false',
        dest='record_audio',
        help="Flag to disable audio recording."
    )
    parser.add_argument(
        '--download-model',
        action='store_true',
        help="Download the Vosk speech recognition model and exit."
    )

    args = parser.parse_args()

    if args.download_model:
        download_model()
        return

    print("Screen Capture and Summarization App")

    if args.mode == 'record' or args.mode == 'all':
        record_media(output_filename=args.output, duration=args.duration, record_audio=args.record_audio)

    if args.mode == 'summarize' or args.mode == 'all':
        video_to_process = args.input if args.mode == 'summarize' else args.output

        if not os.path.exists(video_to_process):
             print(f"Error: Input file '{video_to_process}' not found. Cannot summarize.")
             return

        # --- Get Summaries ---
        ocr_text_set = extract_text_from_video(video_to_process)
        ocr_summary = summarize_text(ocr_text_set)
        audio_summary = transcribe_audio_from_video(video_to_process)

        # --- Combine and Print Final Summary ---
        final_summary = (
            "\n--- OCR Summary ---\n"
            f"{ocr_summary}\n"
            "-------------------\n\n"
            "--- Audio Summary ---\n"
            f"{audio_summary}\n"
            "---------------------"
        )

        print("\n--- Combined Summary ---")
        print(final_summary)
        print("----------------------")


if __name__ == "__main__":
    # Suppress Vosk logging
    SetLogLevel(-1)
    main()
