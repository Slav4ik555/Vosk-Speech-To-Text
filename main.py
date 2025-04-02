import sys
import queue
import json
import sounddevice as sd
import customtkinter
import threading
from customtkinter import filedialog
from tkinter import messagebox
from vosk import Model, KaldiRecognizer

#Настройка приложения
app = customtkinter.CTk()
app.geometry('500x500')
app.minsize(400, 250)
app.title('Vosk Speech-To-Text')
padx = 5 # X-axis padding
pady = 5 # Y-axis padding

# Global variables
#===================================================================================

audio_queue = queue.Queue()
is_recording = False

# Audio capture settings
samplerate = 16000  # Sampling rate
channels = 1        # Mono

#===================================================================================

# Function block
#===================================================================================

# Audio data callback
def audio_callback(indata, frames, time, status):
    if status:
        print(f"Error: {status}", file=sys.stderr)
    audio_queue.put(bytes(indata))

# Model directory selection function
def button_chose_folder_event():
    entry.delete(0,"end")
    model_directory = str(filedialog.askdirectory())
    entry.insert(0, model_directory)
    print(f"Selected directory: {model_directory}")

# Model stop function
def button_stop_recording_event():
    global is_recording
    is_recording = False
    button_stop_recording.configure(state="disabled", fg_color="gray")

# Model start function
def button_start_model_event():
    # Model loading
    model_path = entry.get()
    print(f"Starting model: {model_path}")
    try:
        model = Model(model_path)
        button_stop_recording.configure(state="normal", fg_color="red", hover_color="darkred")
    except Exception as e:
        messagebox.showerror("Error!",str(e))

    print("Model loaded successfully.")

    # Configure recognition
    recognizer = KaldiRecognizer(model, 16000)
    print("Recognition configured.")

    # Queue for audio streaming
    global audio_queue # Using global queue

    # Start recording and recognition in separate thread
    threading.Thread(target=recognize_speech, args=(recognizer,), daemon=True).start()

# Speech recognition function
def recognize_speech(recognizer):
    global is_recording
    global samplerate
    global channels

    is_recording = True

    try:
        print("Starting recording...")
        with sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype='int16',
                               channels=channels, callback=audio_callback):
            print("Start speaking...")

            while is_recording:
                # Get data from queue
                data = audio_queue.get()

                # Recognize text
                if recognizer.AcceptWaveform(data):
                    result = recognizer.Result()
                    print("Recognized text:", result)

                    # Convert result string to dictionary
                    result_dict = json.loads(result)

                    # Check if "text" field exists and is not empty
                    if result_dict.get("text"):
                        # Insert text at the end of textbox
                        textbox.insert("end", result_dict["text"] + " ")
                        textbox.see("end")  # Scroll textbox to bottom
                else:
                    partial_result = recognizer.PartialResult()
                    print("Partial text:", partial_result)
    except Exception as e:
        messagebox.showerror("Error!",str(e))
        
#===================================================================================

# Model selection button
button_chose_folder = customtkinter.CTkButton(app, text="Select model", command=button_chose_folder_event)
button_chose_folder.grid(row=0, column=0, padx=padx, pady=pady, sticky="nsew")

# Model directory entry field
entry = customtkinter.CTkEntry(app, placeholder_text="Enter model directory")
entry.grid(row=0, column=1, padx=padx, pady=pady, sticky="nsew")

# Model start button
button_start_model = customtkinter.CTkButton(app, text="Start model", command=button_start_model_event)
button_start_model.grid(row=1, column=0, columnspan=2, padx=padx, pady=pady, sticky="nsew")

# Stop recording button
button_stop_recording = customtkinter.CTkButton(app, text="Stop recording", command=button_stop_recording_event, state="disabled", fg_color="gray")
button_stop_recording.grid(row=2, column=0, columnspan=2, padx=padx, pady=pady, sticky="nsew")

# Text output box
textbox = customtkinter.CTkTextbox(app)
textbox.grid(row=3, column=0, columnspan=2, padx=padx, pady=pady, sticky="nsew")

# Grid configuration for responsive layout
app.grid_columnconfigure(1, weight=1)  # Second column expands
app.grid_rowconfigure(3, weight=1)  # Third row expands

# Main application loop
app.mainloop()