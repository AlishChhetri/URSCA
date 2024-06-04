import pygame
import serial
import time
import os
import cv2
import numpy as np

# Initialize Pygame mixer for sound playback
pygame.mixer.init()

# Map each key to its corresponding WAV file
sound_files = {
    'C': '261Hz-1000ms-C.wav',
    'C#': '277Hz-1000ms-Db.wav',
    'D': '293Hz-1000ms-D.wav',
    'D#': '311Hz-1000ms-Eb.wav',
    'E': '329Hz-1000ms-E.wav',
    'F': '349Hz-1000ms-F.wav',
    'F#': '369Hz-1000ms-Gb.wav',
    'G': '391Hz-1000ms-G.wav',
    'G#': '415Hz-1000ms-Ab.wav',
    'A': '440Hz-1000ms-A.wav',
    'A#': '466Hz-1000ms-Bb.wav',
    'B': '493Hz-1000ms-B.wav',
    'C2': '523Hz-1000ms-C.wav',  # Higher octave C
}

key_map = {
    'C': 'C',
    'C#': 'd',
    'D': 'D',
    'D#': 'e',
    'E': 'E',
    'F': 'F',
    'F#': 'f',
    'G': 'G',
    'G#': 'g',
    'A': 'A',
    'A#': 'a',
    'B': 'B',
    'C2': 'L',
}

# Load sounds
sounds = {key: pygame.mixer.Sound(os.path.join('../tones', file)) for key, file in sound_files.items()}

# Flag to track the state of each column
column_states = {note: False for note in key_map.values()}

def play_sound(note):
    sound = sounds.get(note)
    if sound:
        sound.play()

def stop_sound(note):
    sound = sounds.get(note)
    if sound:
        sound.stop()

def detect_shadows_and_play_notes(frame, grid_size, threshold, arduino):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    cell_width = width // len(key_map)

    for j, note in enumerate(key_map.values()):
        cell = gray[:, j * cell_width:(j + 1) * cell_width]
        mean_val = np.mean(cell)

        if mean_val < 63:  # Adjusted threshold condition
            column_states[note] = True
            play_sound(note)
            arduino.write(bytes(note, 'utf-8'))
        else:
            if column_states[note]:
                column_states[note] = False
                stop_sound(note)
                arduino.write(b'0')

        # Draw the grid
        cv2.rectangle(frame, (j * cell_width, 0), ((j + 1) * cell_width, height), (0, 0, 255), 2)
        cv2.putText(frame, note, (j * cell_width + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)

def key_held(keys_to_monitor, arduino, grid_size=(1, 13), threshold=50):
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open video capture")
        return

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        detect_shadows_and_play_notes(frame, grid_size, threshold, arduino)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Convert frame to grayscale

        cv2.imshow('Shadow Detection', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    keys_to_monitor = list(key_map.keys())

    arduino_port = '/dev/ttyACM0'
    arduino_baudrate = 9600
    arduino = serial.Serial(arduino_port, arduino_baudrate, timeout=1)

    key_held(keys_to_monitor, arduino)
