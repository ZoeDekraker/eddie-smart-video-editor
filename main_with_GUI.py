import re
from datetime import datetime
import csv
import openai
import requests
import subprocess
import tkinter as tk
from tkinter import filedialog

def video_to_audio(in_video_path, audio_path):
    convert_com =  f'auto-editor {in_video_path} --edit none --no_open --output {audio_path} '
    try:
        # Execute the command
        subprocess.run(convert_com, shell=True, check=True)
        print("successfully created audio file")
    except subprocess.CalledProcessError as e:
        # Handle the exception if the command returns a non-zero exit status
        print(f"An error occurred while executing the command: {e}")


def get_subtitles_whisper(audio_path, subtitle_format='vtt', **kwargs): 
    # error getting subs with openai direct.(?)
    url = 'https://api.openai.com/v1/audio/transcriptions'
    openai.api_key = "sk-API KEY HERE" # <----- API KEY HERE/env
    headers = {
        'Authorization': f'Bearer {openai.api_key}',
    }
    data = {
        'model': 'whisper-1',
        'response_format': subtitle_format,
        'language': 'en',
    }
    data.update(kwargs)
    files = {
        'file': (audio_path, open(audio_path, 'rb'))
    }
    response = requests.post(url, headers=headers, data=data, files=files)
    big_subtitles = response.text
    print('Voice to Text translation done')
    return big_subtitles


def write_subtitles_to_file(big_subtitles, project_name):
    vtt_filename = project_name + '.vtt'
    with open(vtt_filename, 'w') as f:
        f.write(big_subtitles)
    print('Done writing subs to file', vtt_filename)
    return vtt_filename


def parse_vtt(vtt_filename):
    with open(vtt_filename, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        data = []
        current_timestamp = None
        current_text = ''
        # Regular expression to match the timestamp pattern
        timestamp_pattern = re.compile(r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}')
        # Iterate through each line in the file
        for line in lines:
            line = line.strip()
            # If the line matches the timestamp pattern, it indicates the start of a new section
            if timestamp_pattern.match(line):
                # If there is a current_timestamp, that means we have just finished reading a section
                # Save that section before starting the new one
                if current_timestamp:
                    data.append({'timestamp': current_timestamp, 'text': current_text.strip()})
                # Start the new section
                current_timestamp = line
                current_text = ''
            # Otherwise, it's text that belongs to the current section
            elif current_timestamp:
                current_text += ' ' + line

        # Add the last section if exists
        if current_timestamp:
            data.append({'timestamp': current_timestamp, 'text': current_text.strip()})
        return data


def time_str_to_timedelta(time_str):
    """Converts a time string (HH:MM:SS.sss) to a timedelta object."""
    return datetime.strptime(time_str, "%H:%M:%S.%f") - datetime(1900, 1, 1)


def timedelta_to_str(delta):
    """Converts a timedelta object to a time string (HH:MM:SS.sss)."""
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    # Adding milliseconds
    milliseconds = delta.microseconds // 1000
    return "{:02d}:{:02d}:{:02d}.{:03d}".format(hours, minutes, seconds, milliseconds)


def process_subtitles(subtitles):
    # Process each subtitle
    word_timestamps = []
    for sub in subtitles:
        # Split the timestamp string into start and end times
        start_time_str, end_time_str = sub["timestamp"].split(" --> ")
        # Convert time strings to timedelta objects
        start_time = time_str_to_timedelta(start_time_str)
        end_time = time_str_to_timedelta(end_time_str)
        # Split the text into words
        words = re.findall(r'\w+', sub["text"])
        # Calculate the time interval for each word
        time_interval = (end_time - start_time) / len(words)
        # Assign timestamps to each word
        for index, word in enumerate(words):
            current_time = start_time + time_interval * index
            if index < len(words) - 1:
                next_time = current_time + time_interval
            else:
                # For the last word in the section, set the end time to the actual end time of the section
                next_time = end_time
            word_timestamp = {
                "word": word.lower(),
                "start": timedelta_to_str(current_time),
                "end": timedelta_to_str(next_time)
            }
            word_timestamps.append(word_timestamp)
    print('Done processing subtitles')
    return word_timestamps


def write_singlewords(output_filename, word_timestamps):
    # Writing to csv file
    with open(output_filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['word', 'start', 'end'])
        # Writing the header
        writer.writeheader()
        # Writing data rows
        writer.writerows(word_timestamps)
    print('Done writing singlewords to file')


def find_keywords_in_singleword_subs(delimiter_1, delimiter_2, word_timestamps):
    # Find matching pairs of words and their timestamps
    timestamps_for_pairs = {}
    start_time = None
    # Iterate through the word_timestamps
    for entry in word_timestamps:
        if entry['word'] == delimiter_1:
            # If the word is delimiter_1, store the start time
            # This gets updated with the latest timestamp each time delimiter_1 is encountered
            start_time = entry['start']
        elif entry['word'] == delimiter_2 and start_time is not None:
            # If the word is delimiter_2 and we have a start time, store the pair
            end_time = entry['end']
            pair = (delimiter_1, delimiter_2)
            if pair not in timestamps_for_pairs:
                timestamps_for_pairs[pair] = []
            timestamps_for_pairs[pair].append({'start_time': start_time, 'end_time': end_time})
            # Reset start time for the next pair
            start_time = None
    print('Found the matching keywords')
    return timestamps_for_pairs


# Constructing the CLI command for 'auto-editor'
def time_str_to_seconds(time_str):
    """Converts a time string (HH:MM:SS.sss) to seconds with one decimal point."""
    delta = datetime.strptime(time_str, "%H:%M:%S.%f") - datetime(1900, 1, 1)
    total_seconds = delta.total_seconds()
    return f"{total_seconds:.1f}"


def get_cut_out_times(timestamps_for_pairs, delimiter_1, delimiter_2):
    # Constructing the CLI command for 'auto-editor'
    timestamps = timestamps_for_pairs.get((delimiter_1, delimiter_2), [])
    cut_out_ranges = []
    if timestamps:
        #cut_out_ranges = []
        # Convert start time to seconds and add start to the first range's start time
        start_time_in_seconds = time_str_to_seconds(timestamps[0]["start_time"])
        cut_out_ranges.append(f'start,{start_time_in_seconds}sec')
        # Add the rest of the range pairs
        for i in range(len(timestamps)):
            end_time_in_seconds = time_str_to_seconds(timestamps[i]["end_time"])
            if i + 1 < len(timestamps):
                start_time_in_seconds = time_str_to_seconds(timestamps[i + 1]["start_time"])
                cut_out_ranges.append(f'{end_time_in_seconds}sec,{start_time_in_seconds}sec')
            else:
                cut_out_ranges.append(f'{end_time_in_seconds}sec,end')
    print('Time stamps ready')
    return cut_out_ranges


def create_cli_command(in_video_path, cut_out_ranges, output_path):
    # Concatenate the ranges into a single string
    cut_out_string = ' '.join(cut_out_ranges)
    # Construct the full CLI command
    command = f'auto-editor {in_video_path} --margin 0.3sec --cut-out {cut_out_string} --output {output_path} '
    print('command ready', command)
    return command


def execute_shell_command(command):
    try:
        # Execute the command
        subprocess.run(command, shell=True, check=True)
        print("Video edited successfully")
    except subprocess.CalledProcessError as e:
        # Handle the exception if the command returns a non-zero exit status
        print(f"An error occurred while executing the command: {e}")


####--------------GUI functions-----------------####

def browse_video():
    video_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4")])
    print('video selected', video_path)
    video_entry.delete(0, tk.END)
    video_entry.insert(0, video_path)
    return video_path

def browse_output(): 
    output_path = filedialog.askdirectory()
    print('output folder selected', output_path)
    output_entry.delete(0, tk.END)
    output_entry.insert(0, output_path)

def start_processing():
    video_in = video_entry.get()
    in_video_path = video_in #+ ".mp4" 
    print('in video path', in_video_path)
    output_path_small = output_entry.get()
    project_name = project_entry.get()
    output_path = output_path_small + '//' + project_name
    delimiter_1 = delimiter1_entry.get().lower()
    delimiter_2 = delimiter2_entry.get().lower()
    audio_path = "temp_project_audio.mp3"  # can delete after

    video_to_audio(in_video_path, audio_path)
    big_subtitles = get_subtitles_whisper(audio_path, subtitle_format='vtt')
    vtt_filename = write_subtitles_to_file(big_subtitles, project_name)
    subtitles = parse_vtt(vtt_filename)
    word_timestamps = process_subtitles(subtitles)
    # OPTIONAL write transcript to single word timestamps csv file
    #write_singlewords(csv_output_filename, word_timestamps)
    timestamps_for_pairs = find_keywords_in_singleword_subs(delimiter_1, delimiter_2, word_timestamps)
    cut_out_ranges = get_cut_out_times(timestamps_for_pairs, delimiter_1, delimiter_2)
    command = create_cli_command(in_video_path, cut_out_ranges, output_path)
    execute_shell_command(command)

    cancel_processing() # close GUI window


def cancel_processing():
    window.destroy()


# -----------------------GUI------------------------# 
# Create the Tkinter window
window = tk.Tk()
window.title("Eddy - Smart Video Editor")
window.configure(padx=10, pady=10)

project_label = tk.Label(window, text="Project Name:")
project_label.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
project_entry = tk.Entry(window)
project_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)

delimiter1_label = tk.Label(window, text="Start Word")
delimiter1_label.grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
delimiter1_entry = tk.Entry(window)
delimiter1_entry.grid(row=4, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)


delimiter2_label = tk.Label(window, text="End Word")
delimiter2_label.grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)
delimiter2_entry = tk.Entry(window)
delimiter2_entry.grid(row=6, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)


video_label = tk.Label(window, text="Input Video:")
video_label.grid(row=8, column=0, padx=5, pady=5, sticky=tk.W)
video_entry = tk.Entry(window, width=35)
video_entry.grid(row=9, column=0, columnspan=2, padx=5, pady=5)
browse_button = tk.Button(window, text="Browse", command=browse_video)
browse_button.grid(row=9, column=2, padx=5, pady=5)

output_label = tk.Label(window, text="Output Folder:")
output_label.grid(row=10, column=0, padx=5, pady=5, sticky=tk.W)
output_entry = tk.Entry(window, width=35)
output_entry.grid(row=11, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
browse_button = tk.Button(window, text="Browse", command=browse_output)
browse_button.grid(row=11, column=2, padx=5, pady=5)

buttons_frame = tk.Frame(window, pady=5)
buttons_frame.grid(row=12, column=0, columnspan=3, padx=5, pady=10)
process_button = tk.Button(buttons_frame, text="Start Processing", command=start_processing)
process_button.pack(side=tk.LEFT, padx=5)
cancel_button = tk.Button(buttons_frame, text="Cancel", command=cancel_processing)
cancel_button.pack(side=tk.LEFT, padx=5)


# Run the application
window.mainloop()
