import cv2
import numpy as np
import pytesseract
from PIL import Image
import time
import argparse
import subprocess
import os
import re


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


def record_screen(output_filename="output.mp4", duration=5, fps=10.0):
    """
    Records the screen for a given duration and saves it to a video file.
    Uses xwd and ImageMagick's convert for capturing frames in a headless environment.
    """
    print("Waiting 2 seconds for window to initialize...")
    time.sleep(2)

    screen_width, screen_height = get_screen_size()

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_filename, fourcc, fps, (screen_width, screen_height))

    print(f"Recording for {duration} seconds using xwd...")

    frame_files = []
    temp_dir = "temp_frames"
    os.makedirs(temp_dir, exist_ok=True)

    # --- Capture Phase ---
    print("Starting capture phase...")
    capture_start_time = time.time()
    frame_count = 0
    while (time.time() - capture_start_time) < duration:
        frame_start_time = time.time()

        temp_xwd = os.path.join(temp_dir, f"frame_{frame_count}.xwd")
        temp_png = os.path.join(temp_dir, f"frame_{frame_count}.png")

        try:
            subprocess.run(["xwd", "-root", "-out", temp_xwd], check=True, capture_output=True)
            subprocess.run(["convert", temp_xwd, temp_png], check=True, capture_output=True)
            if os.path.exists(temp_png):
                frame_files.append(temp_png)
            os.remove(temp_xwd)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error during frame capture: {e.stderr.decode()}")
            break

        frame_count += 1
        frame_time = time.time() - frame_start_time
        sleep_time = (1.0 / fps) - frame_time
        if sleep_time > 0:
            time.sleep(sleep_time)

    print("Capture phase complete. Starting video writing phase...")

    # --- Video Writing Phase ---
    for png_file in frame_files:
        frame = cv2.imread(png_file)
        if frame is not None:
            video_writer.write(frame)
        os.remove(png_file)

    print(f"Finished recording. Video saved to {output_filename}")
    video_writer.release()

    if os.path.exists(temp_dir):
        os.rmdir(temp_dir)


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


def main():
    """
    Main function to run the screen capture and summarization application via CLI.
    """
    parser = argparse.ArgumentParser(description="Screen Capture and Summarization Tool")
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
        default=5,
        help="Duration of the screen recording in seconds."
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

    args = parser.parse_args()

    print("Screen Capture and Summarization App")

    if args.mode == 'record' or args.mode == 'all':
        record_screen(output_filename=args.output, duration=args.duration)

    if args.mode == 'summarize' or args.mode == 'all':
        video_to_process = args.input if args.mode == 'summarize' else args.output

        if not video_to_process:
            print("Error: --input is required for 'summarize' mode.")
            return

        extracted_text_set = extract_text_from_video(video_to_process)
        summary = summarize_text(extracted_text_set)

        print("\n--- Summary ---")
        print(summary)
        print("---------------")


if __name__ == "__main__":
    main()
