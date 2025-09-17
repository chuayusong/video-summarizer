# Screen and Audio Summarizer

This is a command-line application that records your screen and audio, then generates a summary of the content. It uses Optical Character Recognition (OCR) to extract text from the screen and a speech-to-text engine to transcribe the audio.

## Dependencies

This application relies on several external command-line tools. Please ensure they are installed on your system.

### System Dependencies

On a Debian/Ubuntu-based system, you can install them with the following command:

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

### Basic Usage

To record your screen and audio for 10 seconds and then generate a summary:

```bash
# Note: In a headless environment or from a script, you may need to run
# the application inside a virtual framebuffer like Xvfb.
xvfb-run python3 app.py --duration 10
```

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
