import pygame
import serial
import time
import os

# Initialize Pygame mixer for sound playback
pygame.mixer.init()

key_map = {
    's': 'C',
    'd': 'D',
    'f': 'E',
    'g': 'F',
    'h': 'G',
    'j': 'A',
    'k': 'B',
    'l': 'L',
    'e': 'd',
    'r': 'e',
    'y': 'f',
    'u': 'g',
    'i': 'a',
}

# Map each key to its corresponding WAV file
sound_files = {
    'C': '261Hz-1000ms-C.wav',
    'D': '293Hz-1000ms-D.wav',
    'E': '329Hz-1000ms-E.wav',
    'F': '349Hz-1000ms-F.wav',
    'G': '391Hz-1000ms-G.wav',
    'A': '440Hz-1000ms-A.wav',
    'B': '493Hz-1000ms-B.wav',
    'L': '523Hz-1000ms-C.wav',  # Assuming 'L' corresponds to 'C'
    'd': '277Hz-1000ms-Db.wav',  # Assuming 'd' is C#
    'e': '311Hz-1000ms-Eb.wav',  # Assuming 'e' is D#
    'f': '369Hz-1000ms-Gb.wav',  # Assuming 'f' is F#
    'g': '415Hz-1000ms-Ab.wav',  # Assuming 'g' is G#
    'a': '466Hz-1000ms-Bb.wav',  # Assuming 'a' is A#
}

# Load sounds
sounds = {key: pygame.mixer.Sound(os.path.join('../tones', file)) for key, file in sound_files.items()}

def key_pressed(key, arduino):
    if key in key_map:
        print(f"{key} is being held down!")
        arduino.write(bytes(key_map[key], 'utf-8'))
        sound = sounds.get(key_map[key])
        if sound:
            sound.play()

def key_released(key, arduino):
    if key in key_map:
        print(f"{key} is released!")
        arduino.write(b'0')  # Sending '0' to turn off LED
        sound = sounds.get(key_map[key])
        if sound:
            sound.stop()

def key_held(keys_to_monitor, arduino):
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((100, 100))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                key_pressed(pygame.key.name(event.key), arduino)
            elif event.type == pygame.KEYUP:
                key_released(pygame.key.name(event.key), arduino)

        time.sleep(0.1)  # Adjust the delay as needed
        clock.tick(30)  # Adjust the frame rate as needed

if __name__ == "__main__":

    keys_to_monitor = list(key_map.keys())

    # Open serial connection to Arduino
    arduino_port = '/dev/ttyACM0'
    arduino_baudrate = 9600
    arduino = serial.Serial(arduino_port, arduino_baudrate, timeout=1)

    key_held(keys_to_monitor, arduino)
