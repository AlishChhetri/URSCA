import pygame
import serial
import time
import os
import cv2
import numpy as np
from rich import print
from rich.console import Console
from rich.table import Table
from rich.text import Text


console = Console()

# Initialize Pygame mixer for sound playback
pygame.mixer.init()

# Map each key to its corresponding WAV file
sound_files = {
    "C": "261Hz-1000ms-C.wav",
    "C#": "277Hz-1000ms-Db.wav",
    "D": "293Hz-1000ms-D.wav",
    "D#": "311Hz-1000ms-Eb.wav",
    "E": "329Hz-1000ms-E.wav",
    "F": "349Hz-1000ms-F.wav",
    "F#": "369Hz-1000ms-Gb.wav",
    "G": "391Hz-1000ms-G.wav",
    "G#": "415Hz-1000ms-Ab.wav",
    "A": "440Hz-1000ms-A.wav",
    "A#": "466Hz-1000ms-Bb.wav",
    "B": "493Hz-1000ms-B.wav",
    "C2": "523Hz-1000ms-C.wav",  # Higher octave C
}

key_map = {
    "C": "C",
    "C#": "d",
    "D": "D",
    "D#": "e",
    "E": "E",
    "F": "F",
    "F#": "f",
    "G": "G",
    "G#": "g",
    "A": "A",
    "A#": "a",
    "B": "B",
    "C2": "L",
}

# Load sounds
sounds = {
    key: pygame.mixer.Sound(os.path.join("../tones", file))
    for key, file in sound_files.items()
}

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


def note_pressed(note, arduino):
    if note in key_map.values():
        print(f"{note} is being held down!")
        arduino.write(bytes(note, "utf-8"))
        sound = sounds.get(note)
        if sound:
            sound.play()


def note_released(note, arduino):
    if note in key_map.values():
        print(f"{note} is released!")
        arduino.write(b"0")  # Sending '0' to turn off LED
        sound = sounds.get(note)
        if sound:
            sound.stop()


def detect_shadows_and_play_notes(frame, detection_area, arduino, honey_pot):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Extract the detection area from the frame
    detection_region = gray[
        detection_area[1] : detection_area[3], detection_area[0] : detection_area[2]
    ]
    height, width = detection_region.shape
    cell_width = width // len(key_map)

    # Calculate the dynamic threshold based on the honey pot
    honey_pot_area = gray[honey_pot[1] : honey_pot[3], honey_pot[0] : honey_pot[2]]
    honey_pot_mean = np.mean(honey_pot_area)
    dynamic_threshold = honey_pot_mean * 0.5  # 50% of the mean value of the honey pot

    global honey_pot_warning_printed  # Declare the flag variable as global

    if honey_pot_mean < 63:
        if not honey_pot_warning_printed:
            console.print("Honey pot area is too dark! Please adjust the camera!")
            honey_pot_warning_printed = True
        return detection_region
    else:
        honey_pot_warning_printed = False

    # Create a table with a single row
    table = Table(show_header=False, show_lines=False)
    for _ in range(len(key_map)):
        table.add_column()

    # Update the color of the notes based on their state
    row = []
    for j, note in enumerate(key_map.values()):
        cell = detection_region[:, j * cell_width : (j + 1) * cell_width]
        mean_val = np.mean(cell)

        if honey_pot_mean < 63:
            color = "black"
        elif mean_val < dynamic_threshold:
            if not column_states[note]:
                column_states[note] = True
                arduino.write(bytes(note, "utf-8"))
                sound = sounds.get(note)
                if sound:
                    sound.play()
            color = "green"
        else:
            if column_states[note]:
                column_states[note] = False
                arduino.write(b"0")
                sound = sounds.get(note)
                if sound:
                    sound.stop()
            color = "red"

        row.append(Text(note, style=color))

    table.add_row(*row)

    # Clear the previous output and print the new table
    console.clear()
    console.print(table)

    # Draw the grid
    for j, note in enumerate(key_map.values()):
        cv2.rectangle(
            detection_region,
            (j * cell_width, 0),
            ((j + 1) * cell_width, height),
            (0, 0, 255),
            2,
        )
        cv2.putText(
            detection_region,
            note,
            (j * cell_width + 10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 255),
            1,
            cv2.LINE_AA,
        )

    return detection_region


def key_held(keys_to_monitor, arduino, detection_area, honey_pot):
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open video capture")
        return

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Draw detection area and honey pot
        cv2.rectangle(
            frame,
            (detection_area[0], detection_area[1]),
            (detection_area[2], detection_area[3]),
            (0, 255, 0),
            2,
        )
        cv2.rectangle(
            frame,
            (honey_pot[0], honey_pot[1]),
            (honey_pot[2], honey_pot[3]),
            (255, 0, 0),
            2,
        )

        processed_frame = detect_shadows_and_play_notes(
            frame, detection_area, arduino, honey_pot
        )

        # Show the full frame
        cv2.imshow("Full Frame with Detection and Honey Pot Areas", frame)
        # Zoomed in detection area
        cv2.imshow("Shadow Detection", processed_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    keys_to_monitor = list(key_map.keys())

    arduino_port = "/dev/ttyACM0"
    arduino_baudrate = 9600
    arduino = serial.Serial(arduino_port, arduino_baudrate, timeout=1)

    # Define detection area
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    frame_height, frame_width = frame.shape[:2]
    detection_area = (
        0,
        frame_height // 2,
        frame_width,
        frame_height // 2 + frame_height // 4,
    )

    # Define honey pot
    honey_pot = (0, 0, 50, 50)

    key_held(keys_to_monitor, arduino, detection_area, honey_pot)
