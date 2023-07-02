# Eddie the Smart Video Editor

## Introduction
Eddie the Smart Video Editor is a Python script that automates the process of editing videos based on specific codewords you say while recording the video. 

It takes a video file, converts it into an audio file, transcribes the audio to text using OpenAI's Whisper and identifies segments between specified codewords. It then cuts out these segments from the original video, removes any ‘silence’, and produces a new edited video file ready for the final touches. 

False recording starts are also okay! It only matches the last occurrence of the 'start' codeword when the next codeword is the 'end' codeword. 

### Features
- **Time Saver**: Save time on manually editing videos.
- **Transcription**: Utilizes OpenAI's Whisper A.I system for accurate transcription.
- **Subtitle Extraction**: Extracts subtitles along with timestamps.(can also export to csv).
- **Segment Detection**: Detects and marks segments based on user-specified keywords.
- **Smart Editing**: Edits the original video by cutting out marked segments.
- **Output**: Outputs a newly edited video file with silence removed.

### Prerequisites
- Python 3.6 or higher.
- Required external libraries: `openai`, `requests`.
- An API key from OpenAI for using the Whisper speech-to-text(free account is fine). [Get it here](https://openai.com/)
- Auto-Editor command line program installed. [Learn how to install](https://auto-editor.com/installing)

### Installation
1. Clone this repository or download the script.
2. Install the required libraries and tools using the `requirements.txt` file: pip install -r requirements.txt
3. Make sure Auto-Editor is installed and available in the system's PATH.

### Usage
1. Open the script and configure the required settings such as the input file, output path, and codewords(delimeters).
2. Run the script: main.py
3. The script will process the video and output an edited video file with autoplay.

### License
This project is licensed under the MIT License.

### Acknowledgments
- [OpenAI](https://openai.com/) for their Whisper ASR system.
- [Auto-Editor](https://auto-editor.com/) for providing the video editing command line tool – amazing tool!.

