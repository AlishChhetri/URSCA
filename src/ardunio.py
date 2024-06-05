import serial
import getch

# Initialize serial communication
ser = serial.Serial("/dev/ttyACM0", 9600)

# sudo chmod a+rw /dev/ttyACM0
key_map = {
    "s": "C",
    "d": "D",
    "f": "E",
    "g": "F",
    "h": "G",
    "j": "A",
    "k": "B",
    "l": "C",
    "e": "C#/Db",
    "r": "D#/Eb",
    "y": "F#/Gb",
    "u": "G#/Ab",
    "i": "A#/Bb",
}

while True:
    key = getch.getch()
    if key == "f":
        ser.write(b"f")
        print(f"Send word: {key_map.get(key, key).upper()}")
    elif key in key_map:
        word = key_map[key]
        ser.write(word.encode("utf-8"))
        print(f"Sent word: {word}")
    else:
        ser.write(key.encode("utf-8"))
        print(f"Received key: {key}")
