import os
import winsound

if __name__ == "__main__":
    if os.name == 'nt':
        frequency = 2500
        # Set Duration To 1000 ms == 1 second
        duration = 1000
        winsound.Beep(frequency, duration)

        winsound.PlaySound("SystemExit", winsound.SND_ALIAS)

        winsound.PlaySound('../sound/completed.wav', winsound.SND_FILENAME)
