#! python3
# mkCoordTracker.py
# Basic function to track coords as a helper script for developing other programs

# Import modules
import pyautogui, keyboard, queue

# Define functions
## Keyboard-related functions
class Keylogging:
        def __init__(self):
                self.queue = queue.Queue()
                self.current_log = None
                self.is_logging = False
                self.log_type = 'keyboard'
        def start_logging(self):
                if self.is_logging == False:
                        keyboard.start_recording(self.queue)
                self.is_logging = True
        def stop_logging(self):
                if self.is_logging == True:
                        self.queue = keyboard.stop_recording() # The returned .queue object is now a list rather than queue.Queue() object
                self.is_logging = False
        def empty_log(self):
                if self.is_logging == False:
                        self.queue = queue.Queue()
        def reset_log(self):
                if self.is_logging == True:
                        self.stop_logging()
                self.queue = queue.Queue()
                self.start_logging()
        def read_log(self):
                self.current_log = list(self.queue)
        def block_until(self, break_key):
                self.is_logging = True
                self.queue = keyboard.record(until = break_key)
                self.is_logging = False

def mouseCoordTrack():
        # Tell user how to end this function
        print('Press CTRL+C to stop mouse coordinate tracking function.')
        print('Press Esc to pause and resume coordinate tracking.')
        # Enact main loop
        paused = False
        keylog = Keylogging()
        while True:
                try:
                        keylog.start_logging()
                        x, y = pyautogui.position()
                        if paused == False:
                                print('X: ' + str(x).rjust(4) + ' Y: ' + str(y).rjust(4), end = '\r')
                        # Detect space key presses for pausing/resuming tracking function
                        keylog.stop_logging()
                        for key in keylog.queue:
                                if key.name == 'esc' and key.event_type == 'down':
                                        if paused == False:
                                                paused = True
                                        else:
                                                paused = False
                        keylog.reset_log()
                except KeyboardInterrupt:
                        print('')
                        print('Mouse coordinate tracking stop.')
                        break
                except:
                        print('')
                        print('Unknown error; mouse coordinate tracking will resume.')

def main():
        mouseCoordTrack()

if __name__ == '__main__':
        main()
