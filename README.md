# Screen and Audio Summarizer

This is a cross-platform command-line application that records your screen and audio, then generates a summary of the content. It uses Optical Character Recognition (OCR) to extract text from the screen and a speech-to-text engine to transcribe the audio.

## Dependencies

This application relies on several external command-line tools. Please ensure they are installed on your system.

### System Dependencies (Linux)

On a Debian/Ubuntu-based system, you can install the required tools with the following command:

```bash
sudo apt-get update && sudo apt-get install -y \
    ffmpeg \
    tesseract-ocr \
    xvfb \
    xterm \
    x11-apps \
    imagemagick \
    alsa-utils
```

### System Dependencies (Windows)

**Experimental Support:** The implementation for Windows is experimental and has not been tested in a real Windows environment.

You will need to install the following tools:

1.  **FFmpeg:** Download and install FFmpeg for Windows from the [official website](https://ffmpeg.org/download.html) and ensure the `ffmpeg.exe` binary is in your system's PATH.
2.  **Tesseract OCR:** Download and install Tesseract from the [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) page. Ensure the `tesseract.exe` binary is in your system's PATH.

### Python Dependencies

The required Python libraries are listed in `requirements.txt`. You can install them using pip:

```bash
pip install -r requirements.txt
```

## Setup

Before you can run the application, you must download the speech recognition model. Run the following command:

```bash
python3 app.py --download-model
```

This will download and extract a small English language model (about 40MB) into the project directory.

## Usage

The application is controlled via command-line arguments.

### Basic Usage (Linux)

To record your screen and audio for 10 seconds and then generate a summary:

```bash
# Note: In a headless environment or from a script, you must run
# the application inside a virtual framebuffer like Xvfb.
xvfb-run python3 app.py --duration 10
```

### Basic Usage (Windows)

To record your screen and audio for 10 seconds:

```powershell
python3 app.py --duration 10
```

**Important:** The application defaults to using an audio device named "Stereo Mix" for recording system audio. This may not be correct for your system. To find the list of available audio devices, run the following `ffmpeg` command:

```powershell
ffmpeg -list_devices true -f dshow -i dummy
```

Look for the name of your microphone or system audio device in the output and provide it to the application (this currently requires modifying the `app.py` script directly).

### Command-Line Arguments

*   `--mode {record,summarize,all}`: The mode to run in.
    *   `record`: Only records video (and audio).
    *   `summarize`: Only summarizes an existing video file specified with `--input`.
    *   `all`: Records and then summarizes (default).
*   `--duration DURATION`: Duration of the recording in seconds (default: 10).
*   `--output FILENAME`: Filename for the output video (default: `output.mp4`).
*   `--input FILENAME`: Input video file to summarize. Required for `summarize` mode.
*   `--no-audio`: A flag to disable audio recording.
*   `--download-model`: Downloads the speech recognition model and exits.

### Examples

**Record a 30-second video named `my_session.mp4` with no audio:**

```bash
xvfb-run python3 app.py --mode record --duration 30 --output my_session.mp4 --no-audio
```

**Summarize an existing video file:**

```bash
python3 app.py --mode summarize --input my_session.mp4
```
