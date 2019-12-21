#! python3
# autoMK.py
# Framework for automating mouse and keyboard actions. Windows only.
# Made by Zachary Stewart; intended as a gift to Jordan Stewart.
'''

'''

# Import modules
import pyautogui, keyboard, mouse, queue, ctypes, screeninfo, time, re, os
from tkinter import scrolledtext
from tkinter import filedialog
#from tkinter import messagebox
from tkinter import *
#from tkinter.ttk import *

# Hard-coded parameter setup
WHEEL_DELTA = 120 # Taken from boppreh's _winmouse.py code, used as Windows OS default scroll distance
MOUSEEVENTF_WHEEL = 0x800 # Taken from boppreh's _winmouse.py code
user32 = ctypes.WinDLL('user32', use_last_error = True) # Taken from boppreh's _winmouse.py code

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
                if type(self.queue) == queue.Queue:
                        self.current_log = list(self.queue.queue)
                else:
                        self.current_log = list(self.queue)
        def block_until(self, break_key):
                self.is_logging = True
                self.queue = keyboard.record(until = break_key)
                self.is_logging = False

def key_down(key, pause_seconds=0):
        pyautogui.keyDown(key, pause=pause_seconds)

def key_up(key, pause_seconds=0):
        pyautogui.keyUp(key, pause=pause_seconds)

def key_type(keys_string, typing_seconds=1, pause_seconds=0):
        key_press_interval = typing_seconds / len(keys_string)
        pyautogui.typewrite(keys_string, interval=key_press_interval, pause=pause_seconds)

def key_press(keys_list, hold_seconds=0):
        for key in keys_list:
                key_down(key)
        time.sleep(hold_seconds)
        for key in reversed(keys_list):
                key_up(key)

def validate_keyboard(keys, presses=None, interval=None):
        # Ensure that key is sensible  ## obtained from https://pyautogui.readthedocs.io/en/latest/keyboard.html#keyboard-keys
        validKeys = ['\t', '\n', '\r', ' ', '!', '"', '#', '$', '%', '&', "'", '(',  
        ')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7',
        '8', '9', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`',
        'a', 'b', 'c', 'd', 'e','f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
        'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~',
        'accept', 'add', 'alt', 'altleft', 'altright', 'apps', 'backspace',
        'browserback', 'browserfavorites', 'browserforward', 'browserhome',
        'browserrefresh', 'browsersearch', 'browserstop', 'capslock', 'clear',
        'convert', 'ctrl', 'ctrlleft', 'ctrlright', 'decimal', 'del', 'delete',
        'divide', 'down', 'end', 'enter', 'esc', 'escape', 'execute', 'f1', 'f10',
        'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17', 'f18', 'f19', 'f2', 'f20',
        'f21', 'f22', 'f23', 'f24', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9',
        'final', 'fn', 'hanguel', 'hangul', 'hanja', 'help', 'home', 'insert', 'junja',
        'kana', 'kanji', 'launchapp1', 'launchapp2', 'launchmail',
        'launchmediaselect', 'left', 'modechange', 'multiply', 'nexttrack',
        'nonconvert', 'num0', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6',
        'num7', 'num8', 'num9', 'numlock', 'pagedown', 'pageup', 'pause', 'pgdn',
        'pgup', 'playpause', 'prevtrack', 'print', 'printscreen', 'prntscrn',
        'prtsc', 'prtscr', 'return', 'right', 'scrolllock', 'select', 'separator',
        'shift', 'shiftleft', 'shiftright', 'sleep', 'space', 'stop', 'subtract', 'tab',
        'up', 'volumedown', 'volumemute', 'volumeup', 'win', 'winleft', 'winright', 'yen',
        'command', 'option', 'optionleft', 'optionright']
        if type(keys) == str:
                keys = [keys]
        for key in keys:
                if key.lower() not in validKeys:
                        raise Exception((
                                        'Key value "{}" is not valid. Refer to'
                                        ' https://pyautogui.readthedocs.io/en/'
                                        'latest/keyboard.html#keyboard-keys'
                                        ' for a list of valid key identifiers'
                                        .format(key)))

## Mouse-related functions
class Mouselogging:
        def __init__(self):
                self.queue = []
                self.current_log = None
                self.is_logging = False
                self.log_type = 'mouse'
        def start_logging(self):
                if self.is_logging == False:
                        mouse.hook(self.queue.append)
                self.is_logging = True
        def stop_logging(self):
                if self.is_logging == True:
                        mouse.unhook(self.queue.append)
                self.is_logging = False
        def empty_log(self):
                if self.is_logging == False:
                        self.queue = []
        def reset_log(self):
                if self.is_logging == True:
                        self.stop_logging()
                self.queue = []
                self.start_logging()
        def read_log(self):
                self.current_log = list(self.queue)
        def block_until(self, break_click):
                self.is_logging = True
                self.queue = mouse.record(button = break_click)
                self.is_logging = False

def mouse_move(coord):
        '''We use ctypes instead of pyautogui since ctypes supports moving the
        mouse across multiple monitors.'''
        ctypes.windll.user32.SetCursorPos(coord[0], coord[1])

def mouse_down(button, duration=0.0, pause_seconds=0):
        pyautogui.mouseDown(button=button, pause=pause_seconds)

def mouse_up(button, duration=0.0, pause_seconds=0):
        pyautogui.mouseUp(button=button, pause=pause_seconds)

def mouse_scroll(delta): # Delta should be 1.0 or -1.0
        code = MOUSEEVENTF_WHEEL
        user32.mouse_event(code, 0, 0, int(delta * WHEEL_DELTA), 0)

def validate_coord(x_coord, y_coord):
        '''This function will ensure that coordinates being provided are accurate
        w/r/t the user's screen setup to ensure that the program operates
        correctly.'''
        # Obtain monitor details from screeninfo
        monitors = screeninfo.get_monitors()
        # Derive the coordinates for each monitor
        mCoordRanges = []
        for m in monitors:
                xmin = m.x
                xmax = m.width + m.x - 1  # -1 to make it 0-based
                ymin = m.y
                ymax = m.height + m.y - 1
                mCoordRanges.append([xmin, xmax, ymin, ymax])
        # Figure out if the provided coordinates fit within an accepted range
        validated = False
        for mcRange in mCoordRanges:
                if x_coord in range(mcRange[0], mcRange[1]+1) and y_coord in range(mcRange[2], mcRange[3]+1):  # +1 since we're providing 0-based numbers to range
                        validated = True
                        break
        # Raise exception if coordinates were not validated
        if validated == False:
                debuggingText = ''
                for i in range(len(mCoordRanges)):
                        debuggingText += 'Monitor ' + str(i+1) + '=X:' + str(mCoordRanges[i][0]) + \
                        '->' + str(mCoordRanges[i][1]) + ', Y:' + str(mCoordRanges[i][2]) + '->' + \
                        str(mCoordRanges[i][3]) + '\n'
                raise Exception((
                                'The provided coordinate "X: {}, Y: {}" is not'
                                ' a valid coordinate.\nFor debugging, available'
                                ' monitor coordinates are listed below.\n{}'.format(x_coord, y_coord, debuggingText)))

## Log-handling functions
def merge_logs(log_object1, log_object2):
        log_time_pairs = []
        for log in log_object1.queue:
                log_time_pairs.append([log, log.time])
        for log in log_object2.queue:
                log_time_pairs.append([log, log.time])
        log_time_pairs.sort(key = lambda x: x[1])
        for i in range(len(log_time_pairs)):
                log_time_pairs[i] = log_time_pairs[i][0]
        return log_time_pairs

def shrink_moveevents(log_list): # Function will accept keylog, mouselog, or merged log queue/list objects
        new_log = []
        previous_event = None
        previous_added_move_event = None
        for event in log_list:
                if type(event) == mouse._mouse_event.MoveEvent:
                        previous_event = event
                        continue
                else:
                        if type(previous_event) == mouse._mouse_event.MoveEvent:
                                if previous_added_move_event == None:
                                        new_log.append(previous_event)
                                        previous_added_move_event = previous_event
                                elif previous_event.x != previous_added_move_event.x and previous_event.y != previous_added_move_event.y:
                                        new_log.append(previous_event)
                                        previous_added_move_event = previous_event
                        new_log.append(event)
        return new_log

def convert_log_to_functions(log_list, unpress_keys=True):
        functions_list = [] # This list will be filled with strings to use with eval() later
        currently_pressed = set()
        last_time = None
        def derive_wait_time(current_time, last_time):
                if last_time == None:
                        return 0, current_time
                wait_time = current_time - last_time
                return wait_time, current_time # When returned, the current_time value should be named last_time
        for event in log_list:
                if type(event) == mouse._mouse_event.MoveEvent:
                        functions_list.append('mouse_move([' + str(event.x) + ', ' + str(event.y) + '])')
                        wait_time, last_time = derive_wait_time(event.time, last_time)
                        functions_list.append('time.sleep(' + str(wait_time) + ')')
                elif type(event) == mouse._mouse_event.WheelEvent:
                        functions_list.append('mouse_scroll(' + str(event.delta) + ')')
                        wait_time, last_time = derive_wait_time(event.time, last_time)
                        functions_list.append('time.sleep(' + str(wait_time) + ')')
                elif type(event) == mouse._mouse_event.ButtonEvent:
                        if event.event_type == 'up':
                                functions_list.append('mouse_up("' + event.button + '")')
                                currently_pressed.discard(event.button)
                        elif event.event_type == 'down':
                                functions_list.append('mouse_down("' + event.button + '")')
                                currently_pressed.add(event.button)
                        wait_time, last_time = derive_wait_time(event.time, last_time)
                        functions_list.append('time.sleep(' + str(wait_time) + ')')
                elif type(event) == keyboard._keyboard_event.KeyboardEvent:
                        if event.event_type == 'up':
                                functions_list.append('key_up("' + event.name + '")')
                                currently_pressed.discard(event.name)
                        elif event.event_type == 'down':
                                functions_list.append('key_down("' + event.name + '")')
                                currently_pressed.add(event.name)
                        wait_time, last_time = derive_wait_time(event.time, last_time)
                        functions_list.append('time.sleep(' + str(wait_time) + ')')
        if unpress_keys == True:
                for key in currently_pressed:
                        if key in ['left', 'right', 'middle']:
                                functions_list.append('mouse_up("' + key + '")')
                        else:
                                functions_list.append('key_up("' + key + '")')
        return functions_list

def validate_syntax(syntax_file):
        def valid_commands():
                main_commands = ['mouse', 'key', 'wait']
                second_commands = {'mouse': ['click_left', 'click_right', 'scroll_down',
                                             'scroll_up', 'drag', 'move'],
                                  'key': ['press', 'type']}
                return main_commands, second_commands
        def validate_positive_integer(number):
                try:
                        assert '.' not in str(number)
                        int(number)
                except:
                        return False
                if int(number) <= 0:
                        return False
                return True
        coord_format = re.compile(r'x\d{1,5}y\d{1,5}')
        duration_format = re.compile(r'duration\d{1,10}(\.\d{1,10})?$')
        with open(syntax_file, 'r') as file_in:
                for line in file_in: # File is parsed line-by-line, with each line being a function
                        if line.startswith('#'): # This allows lines to be commented out for testing purposes; very helpful!
                                   continue
                        sl = line.lower().rstrip('\r\n').split(' ')
                        # Validate minimum line length is met to prevent errors when calling sl by index later
                        if (sl[0] == 'mouse' or sl[0] == 'key') and len(sl) < 3:
                                print('Syntax file has incomplete command "' + ' '.join(sl) + '"')
                                print('Make sure your file complies with syntax requirements and try again.')
                                quit()
                        # Validate first component of line
                        if not (sl[0] == 'mouse' or sl[0] == 'key' or sl[0].startswith('wait')):
                                print('Syntax file has unrecognised command "' + sl[0] + '"')
                                print('Make sure your file complies with syntax requirements and try again.')
                                quit()
                        # Validate waits
                        if sl[0].startswith('wait'):
                                try:
                                        float(sl[0][4:])
                                except:
                                        print('Wait command has unrecognised integer or foat "' + sl[0] + '"')
                                        print('Make sure your file complies with syntax requirements and try again.')
                                        quit()
                        # Validate second component of line
                        if sl[0] == 'mouse' and sl[1] not in valid_commands()[1]['mouse']:
                                print('Syntax file has unrecognised command "' + sl[1] + '" after "mouse"')
                                print('Make sure your file complies with syntax requirements and try again.')
                                quit()
                        elif sl[0] == 'key' and sl[1] not in valid_commands()[1]['key']:
                                print('Syntax file has unrecognised command "' + sl[1] + '" after "key"')
                                print('Make sure your file complies with syntax requirements and try again.')
                                quit()
                        # Validate third component of line
                        if sl[0] == 'mouse' and sl[1] in ['click_left', 'click_right', 'move']:
                                if not coord_format.match(sl[2]):
                                        print('Syntax file has unrecognised coordinate "' + sl[2] + '" after "' + sl[1] + '"')
                                        print('Make sure your file complies with syntax requirements and try again.')
                                        quit()
                                else:
                                        x_coord, y_coord = list(map(int, sl[2].replace('x','').split('y')))
                                        validate_coord(x_coord, y_coord)
                        elif sl[0] == 'mouse' and sl[1] in ['drag']:
                                if not coord_format.match(sl[2]) or not coord_format.match(sl[4]) or not sl[3] == 'to':
                                        print('Syntax file has unrecognised coordinate "' + ' '.join(sl[2:5]) + '" after "' + sl[1] + '"')
                                        print('Make sure your file complies with syntax requirements and try again.')
                                        quit()
                                else:
                                        x_coord, y_coord = list(map(int, sl[2].replace('x','').split('y')))
                                        validate_coord(x_coord, y_coord)
                                        x_coord, y_coord = list(map(int, sl[4].replace('x','').split('y')))
                                        validate_coord(x_coord, y_coord)
                        elif sl[0] == 'mouse' and sl[1] in ['scroll_down', 'scroll_up']:
                                valid = validate_positive_integer(sl[2])
                                if not valid:
                                        print('Syntax file has unrecognised integer "' + ' '.join(sl[2:5]) + '" after "' + sl[1] + '"')
                                        print('If unrecognised, it is either negative, equal to 0, or is not an integer (i.e., whole number).')
                                        print('Make sure your file complies with syntax requirements and try again.')
                                        quit()
                        elif sl[0] == 'key' and sl[1] in ['press']:
                                if duration_format.match(sl[-1]):
                                        keys_for_validation = sl[2:-1]
                                else:
                                        keys_for_validation = sl[2:]
                                validate_keyboard(keys_for_validation)
                        # Validate duration command if present & line length
                        if sl[0] == 'mouse' and sl[1] in ['click_left', 'click_right', 'move', 'scroll_up', 'scroll_down']:
                                if len(sl) > 4:
                                        print('Syntax file has unrecognised command(s) "' + ' '.join(sl[4:]) + '" after "' + sl[1] + '"')
                                        print('Make sure your file complies with syntax requirements and try again.')
                                        quit()
                                elif len(sl) == 4:
                                        if not duration_format.match(sl[3]):
                                                print('Syntax file has unrecognised duration "' + sl[3] + '" after "' + sl[1] + '"')
                                                print('Make sure your file complies with syntax requirements and try again.')
                                                quit()
                        elif sl[0] == 'mouse' and sl[1] in ['drag']:
                                if len(sl) > 6:
                                        print('Syntax file has unrecognised command(s) "' + ' '.join(sl[6:]) + '" after "' + sl[1] + '"')
                                        print('Make sure your file complies with syntax requirements and try again.')
                                        quit()
                                elif len(sl) == 6:
                                        if not duration_format.match(sl[5]):
                                                print('Syntax file has unrecognised duration "' + sl[5] + '" after "' + sl[1] + '"')
                                                print('Make sure your file complies with syntax requirements and try again.')
                                                quit()
                        elif sl[0] == 'wait':
                                if len(sl) > 1:
                                        print('Syntax file has unrecognised command(s) "' + ' '.join(sl[1:]) + '" after "' + sl[0] + '"')
                                        print('Make sure your file complies with syntax requirements and try again.')
                                        quit()
                                if not duration_format.match(sl[5]):
                                        print('Syntax file has unrecognised wait duration "' + sl[0][4:] + '"')
                                        print('Make sure your file complies with syntax requirements and try again.')
                                        quit()

def convert_syntax_to_functions(syntax_file):
        duration_format = re.compile(r'duration\d{1,10}(\.\d{1,10})?$')
        validate_syntax(syntax_file)
        functions_list = []
        most_recent_mouse_coord = None, None
        with open(syntax_file, 'r') as file_in:
                for line in file_in: # File is parsed line-by-line, with each line being a function
                        if line.startswith('#'): # This allows lines to be commented out for testing purposes; very helpful!
                                   continue
                        sl = line.lower().rstrip('\r\n').split(' ')
                        # Mouse functions
                        if sl[0] == 'mouse':
                                if sl[1] in ['click_left', 'click_right', 'move']:
                                        x_coord, y_coord = list(map(int, sl[2].replace('x','').split('y')))
                                        if len(sl) == 4: # i.e., if a duration# value is programmed
                                                duration = float(sl[3][8:])
                                        else:
                                                duration = 0.0
                                        if sl[1] == 'click_left':
                                                functions_list.append('mouse_move([' + str(x_coord) + ', ' + str(y_coord) + '])')
                                                most_recent_mouse_coord = x_coord, y_coord
                                                functions_list.append('mouse_down("left")')
                                                functions_list.append('time.sleep(' + str(duration) + ')')
                                                functions_list.append('mouse_up("left")')
                                        elif sl[1] == 'click_right':
                                                functions_list.append('mouse_move([' + str(x_coord) + ', ' + str(y_coord) + '])')
                                                most_recent_mouse_coord = x_coord, y_coord
                                                functions_list.append('mouse_down("right")')
                                                functions_list.append('time.sleep(' + str(duration) + ')')
                                                functions_list.append('mouse_up("right")')
                                        elif sl[1] == 'move':
                                                if most_recent_mouse_coord[0] == None:
                                                        curr_x, curr_y = pyautogui.position()
                                                else:
                                                        curr_x, curr_y = most_recent_mouse_coord
                                                        most_recent_mouse_coord = x_coord, y_coord
                                                functions_list += mouse_move_tween_to_functions(curr_x, curr_y, x_coord, y_coord, duration)
                                elif sl[1] in ['scroll_down', 'scroll_up']:
                                        scroll_units = int(sl[2])
                                        if len(sl) == 4:
                                                duration = float(sl[3][8:])
                                        else:
                                                duration = 0.0
                                        if sl[1] == 'scroll_down':
                                                direction = 'down'
                                        elif sl[1] == 'scroll_up':
                                                direction = 'up'
                                        functions_list += mouse_scroll_syntax_to_functions(scroll_units, direction, duration)
                                elif sl[1] in ['drag']:
                                        x_coord1, y_coord1 = list(map(int, sl[2].replace('x','').split('y')))
                                        x_coord2, y_coord2 = list(map(int, sl[4].replace('x','').split('y')))
                                        if len(sl) == 6:
                                                duration = float(sl[5][8:])
                                        else:
                                                duration = 0.0
                                        functions_list += mouse_drag_syntax_to_functions(x_coord1, y_coord1, x_coord2, y_coord2, duration)
                                        most_recent_mouse_coord = x_coord2, y_coord2
                        # Keyboard functions
                        if sl[0] == 'key':
                                if duration_format.match(sl[-1]):
                                        duration = float(sl[-1][8:])
                                        del sl[-1]
                                else:
                                        duration = 0.0
                                if sl[1] in ['press']:
                                        if sl[1] == 'press':
                                                functions_list.append('key_press(' + str(sl[2:]) + ', hold_seconds=' + str(duration) + ')')
                                elif sl[1] in ['type']:
                                        if sl[1] == 'type':
                                                functions_list.append(['key_type', sl_to_typeable_string(sl[2:]), duration])
                        # Wait functions
                        if sl[0].startswith('wait'):
                                duration = float(sl[0][4:])
                                functions_list.append('time.sleep(' + str(duration) + ')')
        return functions_list

def mouse_move_tween_to_functions(x_coord1, y_coord1, x_coord2, y_coord2, duration_seconds=1, steps_per_second=10):
        try:
                return coordinate_pairs_to_functions(coordinate_tween(x_coord1, y_coord1, x_coord2, y_coord2, duration_seconds, steps_per_second), duration_seconds)
        except ZeroDivisionError:
                return ['mouse_move([' + str(x_coord2) + ', ' + str(y_coord2) + '])']

def mouse_drag_syntax_to_functions(x_coord1, y_coord1, x_coord2, y_coord2, duration_seconds=1, steps_per_second=10):
        functions_list = ['mouse_move([' + str(x_coord1) + ', ' + str(y_coord1) + '])']
        functions_list.append('mouse_down("left")')
        try:
                functions_list += coordinate_pairs_to_functions(coordinate_tween(x_coord1, y_coord1, x_coord2, y_coord2, duration_seconds, steps_per_second), duration_seconds)
        except ZeroDivisionError:
                functions_list.append(['mouse_move([' + str(x_coord2) + ', ' + str(y_coord2) + '])'])
        functions_list.append('mouse_up("left")')
        return functions_list

def coordinate_tween(x_coord1, y_coord1, x_coord2, y_coord2, duration_seconds, steps_per_second):
        def tween_from_to(coord1, coord2, duration_seconds, steps_per_second):
                num_of_steps = int(round(duration_seconds * steps_per_second))
                from_to_distance = coord2 - coord1
                distance_per_step = from_to_distance / num_of_steps
                steps = []
                for i in range(num_of_steps):
                        if i == num_of_steps-1:
                                steps.append(int(coord2))
                        else:
                                steps.append(coord1 + int(round(distance_per_step * (i+1)))) # This is just to prevent any current unforeseen maths fuckery
                return steps
        x_steps = tween_from_to(x_coord1, x_coord2, duration_seconds, steps_per_second)
        y_steps = tween_from_to(y_coord1, y_coord2, duration_seconds, steps_per_second)
        coord_pairs = []
        for i in range(len(x_steps)):
                coord_pairs.append([x_steps[i], y_steps[i]])
        return coord_pairs

def coordinate_pairs_to_functions(coord_pairs, duration_seconds): # Function intended to receive output of coordinate_tween()
        num_of_steps = len(coord_pairs)
        seconds_per_step = duration_seconds / num_of_steps
        functions_list = []
        for pair in coord_pairs:
                functions_list.append('time.sleep(' + str(seconds_per_step) + ')')
                functions_list.append('mouse_move([' + str(pair[0]) + ', ' + str(pair[1]) + '])')
        return functions_list

def mouse_scroll_syntax_to_functions(num_of_scrolls, direction, duration_seconds):
        seconds_per_scroll = duration_seconds / (num_of_scrolls+1) # Add an extra time.sleep() function so we can have a wait before and after our first/last scrolls
        functions_list = []
        for i in range(num_of_scrolls):
                if i == 0:
                        functions_list.append('time.sleep(' + str(seconds_per_scroll) + ')')
                if direction == 'up':
                        functions_list.append('mouse_scroll(1)')
                elif direction == 'down':
                        functions_list.append('mouse_scroll(-1)')
                functions_list.append('time.sleep(' + str(seconds_per_scroll) + ')')
        return functions_list

def sl_to_typeable_string(string_list):
        # Convert special characters to typeable values
        for i in range(len(string_list)):
                if string_list[i] == '\\n':
                        string_list[i] = '\n'
                elif string_list[i] == '\\r\\n':
                        string_list[i] = '\r\n'
                elif string_list[i] == '\\t':
                        string_list[i] = '\t'
        # Join list items and return
        return ' '.join(string_list)

def check_log_for_value(log_object, value_name):
        log_object.read_log()
        for event in log_object.current_log:
                if log_object.log_type == 'keyboard':
                        if event.name == value_name:
                                return True
                elif log_object.log_type == 'mouse':
                        if type(event) == mouse._mouse_event.MoveEvent:
                                continue
                        elif type(event) == mouse._mouse_event.ButtonEvent: # valid value_names are 'left', 'right', 'middle'
                                if event.button == value_name:
                                        return True
                        elif type(event) == mouse._mouse_event.WheelEvent: # valid value_names are 'scroll_up' and 'scroll_down'
                                if (event.delta == 1.0 and value_name == 'scroll_up') or (event.delta == -1.0 and value_name == 'scroll_down'):
                                        return True
        return False

def play_functions_list(functions_list):
        for function in functions_list:
                if type(function) == str:
                        eval(function)
                elif type(function) == list:
                        if function[0] == 'key_type':
                                key_type(function[1], typing_seconds=function[2])

## Functions related to user interfacing
def key_to_pause_clicked(): # Top-frame; key_set_button
        # Start logging keyboard and mouse actions
        keylog = Keylogging()
        mouselog = Mouselogging()
        keylog.start_logging()
        mouselog.start_logging()
        # Check logs for button up events; when received, note the time of the event
        exit_time = None
        while True:
                if exit_time != None:
                        break
                time.sleep(0.1)
                keylog.read_log()
                mouselog.read_log()
                buttons_pressed = set()
                for key in keylog.current_log:
                        if key.event_type == 'down':
                                buttons_pressed.add(key.name)
                        elif key.event_type == 'up' and key.name in buttons_pressed: # This lets us ignore buttons that were pressed before we started checking for combos
                                exit_time = key.time
                                break
                for click in mouselog.current_log:
                        if type(click) == mouse._mouse_event.ButtonEvent:
                                if click.event_type == 'down':
                                        buttons_pressed.add(click.button)
                                elif click.event_type == 'up' and click.button in buttons_pressed:
                                        if exit_time == None:
                                                exit_time = click.time
                                        elif click.time < exit_time: # This is overkill 99.9% of cases, but since we sleep 0.1s it might handle quick, fat fingers
                                                exit_time = click.time
                                        break
        # Process logs to derive our combination
        global KEYS_TO_PAUSE
        KEYS_TO_PAUSE = set()
        for key in keylog.current_log:
                if key.event_type == 'down' and key.time < exit_time:
                        KEYS_TO_PAUSE.add(key.name)
        for click in mouselog.current_log:
                        if type(click) == mouse._mouse_event.ButtonEvent:
                                if click.event_type == 'down' and click.time < exit_time:
                                        KEYS_TO_PAUSE.add(click.button)
        # Call function to present text to user
        keys_to_pause_text(KEYS_TO_PAUSE)
        
def keys_to_pause_text(KEYS_TO_PAUSE): # Top-frame; key_set_button
        # Make KEYS_TO_PAUSE presentable as a string to the user
        keys_to_pause_list = []
        if 'ctrl' in KEYS_TO_PAUSE:
                keys_to_pause_list.append('ctrl') # Bring modifier keys to the front
        if 'shift' in KEYS_TO_PAUSE:
                keys_to_pause_list.append('shift')
        if 'alt' in KEYS_TO_PAUSE:
                keys_to_pause_list.append('alt')
        for key in KEYS_TO_PAUSE:
                if key not in ['ctrl', 'shift', 'alt']:
                        keys_to_pause_list.append(key)
        keys_to_pause_as_string = ' '.join(keys_to_pause_list)
        key_display_label.configure(text=keys_to_pause_as_string) # This value was defined as a global in key_to_pause_clicked

def coord_label_update(): # Top-frame; runs globally, connects to x_display_label, y_display_label 
        global PAUSE_COORDS
        global KEYS_TO_PAUSE
        if 'KEYS_TO_PAUSE' in globals():
                all_pressed = True
                for key in KEYS_TO_PAUSE:
                        if key in ['left', 'middle', 'right']:
                                if not mouse.is_pressed(key):
                                        all_pressed = False
                                        break
                        else:
                                if not keyboard.is_pressed(key):
                                        all_pressed = False
                                        break
                if all_pressed == True:
                        if PAUSE_COORDS == False:
                                PAUSE_COORDS = True
                        else:
                                PAUSE_COORDS = False
        if PAUSE_COORDS == False:
                x, y = pyautogui.position()
                x_display_label.configure(text=x)
                y_display_label.configure(text=y)
        x_display_label.after(100, coord_label_update) # Doesn't matter what we attach .after() to

def browse_for_file():
        global recording_location_entry
        file_location = filedialog.askopenfilename()
        recording_location_entry.delete(0, END)
        recording_location_entry.insert(END, file_location)

def gui_window():
        # Set variables which are global in scope
        global key_display_label # This value needs to be updated in keys_to_pause_text
        global PAUSE_COORDS # This value needs to be global to be reused in the coord_label_update loop
        PAUSE_COORDS = False
        global x_display_label # This value needs to be updated in the coord_label_update loop
        global y_display_label # As above
        global recording_location_entry # This value needs to be updated by browse_for_file
        # Set up Tkinter window object
        window = Tk() # Main GUI object
        window.title('autoMK') # Sets the title that displays on the top bar
        window.geometry('{}x{}'.format(600, 400)) # width, height
        # Create main frame container objects
        top_frame = Frame(window, width=350, height=200) # This will hold the coord widgets
        bottom_frame_record = Frame(window, width=350, height=300) # This will hold the recording widgets
        bottom_frame_playback = Frame(window, width=350, height=300) # This will hold the playback widgets
        # Layout of main frame containers
        #window.grid_rowconfigure(1, weight=1)
        #window.grid_columnconfigure(0, weight=1)
        top_frame.grid(row=0, sticky="nsew")
        bottom_frame_record.grid(row=1, sticky="nsew")
        # Create widgets for top frame
        pause_text_label = Label(top_frame, text='Key to pause coord:')
        key_display_label = Label(top_frame, text='', bg='white')
        key_set_button = Button(top_frame, text='Click to record key', command=key_to_pause_clicked)
        ##
        x_label = Label(top_frame, text='X')
        y_label = Label(top_frame, text='Y')
        ##
        x_display_label = Label(top_frame, text='', bg='white')
        y_display_label = Label(top_frame, text='', bg='white')
        # Layout of top frame widgets
        pause_text_label.grid(row=0, column=0)
        key_display_label.grid(row=0, column=1, rowspan=2)
        key_set_button.grid(row=0, column=3)
        ##
        x_label.grid(row=1, column=0)
        y_label.grid(row=1, column=2)
        ##
        x_display_label.grid(row=2, column=0)
        y_display_label.grid(row=2, column=2)
        # Create widgets for recording bottom frame
        load_text_label = Label(bottom_frame_record, text='Load previous recording:')
        recording_location_entry = Entry(bottom_frame_record, width=40)
        recording_location_entry.insert(END, os.getcwd())
        recording_browse_button = Button(bottom_frame_record, text='Browse', command=browse_for_file)
        # Layout of bottom frame widgets
        load_text_label.grid(row=3, column=0)
        recording_location_entry.grid(row=3, column=1)
        recording_browse_button.grid(row=3, column=2)
        # Call functions acting on global values
        key_set_button.after(100, coord_label_update()) # Makes use of KEYS_TO_PAUSE set by key_to_pause_clicked, and (x/y)_display_label and PAUSE_COORDS
        # Launch mainloop
        window.mainloop()

def main():
        '''TBD;
        0) Add failsafe mechanism to cancel program operation (e.g., press left ctrl + right ctrl)
        1) Produce a menu screen that allows the user to call specific functions and set global values e.g., speed-up factors
        2) Produce a config file syntax that allows users to provide simple instructions for mouse/keyboard automation that can be reconstituted appropriately
        3) Re-add coord tracking function to allow the user to make manual adjustments to the config file more simply
        4) Add extra functionality into the config file approach such as string strip/concatenation for values copied into clipboard?
        '''
        
        ## TESTING ZONE ##
        a = Keylogging()
        b = Mouselogging()
        a.start_logging()
        b.start_logging()
        #
        a.stop_logging()
        b.stop_logging()
        #
        c = merge_logs(a, b)
        d = shrink_moveevents(c)
        e = convert_log_to_functions(d)
        play_functions_list(e)

if __name__ == '__main__':
        #main()
        gui_window()
        #pass


#syntax_file = 'C:\\Bioinformatics\\GitHub\\personal_projects\\mouse_keyboard_automation\\syntax_test.txt'
#time.sleep(5)
#eg = convert_syntax_to_functions(syntax_file)
#play_functions_list(eg)
