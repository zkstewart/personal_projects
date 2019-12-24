#! python3
# autoMK.py
# Framework for automating mouse and keyboard actions. Windows only.
# Made by Zachary Stewart; intended as a gift to Jordan Stewart.
'''

'''

# Import modules
import pyautogui, keyboard, mouse, queue, ctypes, screeninfo, time, re, os, pickle, copy
from tkinter import scrolledtext
from tkinter import filedialog
from tkinter import messagebox
from tkinter import *
from tkinter.ttk import Combobox
from functools import partial
from datetime import date

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

def validate_keyboard(keys, presses=None, interval=None, kill_program=False):
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
                        if kill_program == True:
                                raise Exception((
                                                'Key value "{}" is not valid. Refer to'
                                                ' https://pyautogui.readthedocs.io/en/'
                                                'latest/keyboard.html#keyboard-keys'
                                                ' for a list of valid key identifiers'
                                                .format(key)))
                        else:
                                return False
        return True

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

def validate_coord(x_coord, y_coord, kill_program=False):
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
                if kill_program == True:
                        raise Exception((
                                        'The provided coordinate "X: {}, Y: {}" is not'
                                        ' a valid coordinate.\nFor debugging, available'
                                        ' monitor coordinates are listed below.\n{}'.format(x_coord, y_coord, debuggingText)))
                else:
                        return False

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
                                functions_list.append('time.sleep(0)')
                        else:
                                functions_list.append('key_up("' + key + '")')
                                functions_list.append('time.sleep(0)')
        return functions_list

def validate_positive_integer(number):
        try:
                assert '.' not in str(number)
                int(number)
        except:
                return False
        if int(number) <= 0:
                return False
        return True

def validate_syntax(syntax_file):
        def valid_commands():
                main_commands = ['mouse', 'key', 'wait']
                second_commands = {'mouse': ['click_left', 'click_right', 'scroll_down',
                                             'scroll_up', 'drag', 'move'],
                                  'key': ['press', 'type']}
                return main_commands, second_commands
        coord_format = re.compile(r'x\d{1,5}y\d{1,5}')
        duration_format = re.compile(r'duration\d{1,10}(\.\d{1,10})?$')
        with open(syntax_file, 'r') as file_in:
                for line in file_in: # File is parsed line-by-line, with each line being a function
                        if line.startswith('#'): # This allows lines to be commented out for testing purposes; very helpful!
                                   continue
                        sl = line.lower().rstrip('\r\n').split(' ')
                        # Validate minimum line length is met to prevent errors when calling sl by index later
                        if (sl[0] == 'mouse' or sl[0] == 'key') and len(sl) < 3:
                                return 'Syntax file has incomplete command "' + ' '.join(sl) + '".\nMake sure your file complies with syntax requirements and try again.'
                        # Validate first component of line
                        if not (sl[0] == 'mouse' or sl[0] == 'key' or sl[0].startswith('wait')):
                                return 'Syntax file has unrecognised command "' + sl[0] + '".\nMake sure your file complies with syntax requirements and try again.'
                        # Validate waits
                        if sl[0].startswith('wait'):
                                try:
                                        float(sl[0][4:])
                                except:
                                        return 'Wait command has unrecognised integer or foat "' + sl[0] + '".\nMake sure your file complies with syntax requirements and try again.'
                        # Validate second component of line
                        if sl[0] == 'mouse' and sl[1] not in valid_commands()[1]['mouse']:
                                return 'Syntax file has unrecognised command "' + sl[1] + '" after "mouse".\nMake sure your file complies with syntax requirements and try again.'
                        elif sl[0] == 'key' and sl[1] not in valid_commands()[1]['key']:
                                return 'Syntax file has unrecognised command "' + sl[1] + '" after "key".\nMake sure your file complies with syntax requirements and try again.'
                        # Validate third component of line
                        if sl[0] == 'mouse' and sl[1] in ['click_left', 'click_right', 'move']:
                                if not coord_format.match(sl[2]):
                                        return 'Syntax file has unrecognised coordinate "' + sl[2] + '" after "' + sl[1] + '".\nMake sure your file complies with syntax requirements and try again.'
                                else:
                                        x_coord, y_coord = list(map(int, sl[2].replace('x','').split('y')))
                                        validate_coord(x_coord, y_coord, kill_program = True)
                        elif sl[0] == 'mouse' and sl[1] in ['drag']:
                                if not coord_format.match(sl[2]) or not coord_format.match(sl[4]) or not sl[3] == 'to':
                                        return 'Syntax file has unrecognised coordinate "' + ' '.join(sl[2:5]) + '" after "' + sl[1] + '".\nMake sure your file complies with syntax requirements and try again.'
                                else:
                                        x_coord, y_coord = list(map(int, sl[2].replace('x','').split('y')))
                                        validate_coord(x_coord, y_coord, kill_program = True)
                                        x_coord, y_coord = list(map(int, sl[4].replace('x','').split('y')))
                                        validate_coord(x_coord, y_coord, kill_program = True)
                        elif sl[0] == 'mouse' and sl[1] in ['scroll_down', 'scroll_up']:
                                valid = validate_positive_integer(sl[2])
                                if not valid:
                                        return 'Syntax file has unrecognised integer "' + ' '.join(sl[2:5]) + '" after "' + sl[1] + '".\nIf unrecognised, it is either negative, equal to 0, or is not an integer (i.e., whole number).\nMake sure your file complies with syntax requirements and try again.' 
                        elif sl[0] == 'key':
                                if duration_format.match(sl[-1]):
                                        keys_for_validation = sl[2:-1]
                                else:
                                        keys_for_validation = sl[2:]
                                if sl[1] in ['press']: # We don't want to perform this validation step for key_type
                                        validate_keyboard(keys_for_validation, kill_program=True)
                        # Validate duration command if present & line length
                        if sl[0] == 'mouse' and sl[1] in ['click_left', 'click_right', 'move', 'scroll_up', 'scroll_down']:
                                if len(sl) > 4:
                                        return 'Syntax file has unrecognised command(s) "' + ' '.join(sl[4:]) + '" after "' + sl[1] + '".\nMake sure your file complies with syntax requirements and try again.'
                                elif len(sl) == 4:
                                        if not duration_format.match(sl[3]):
                                                return 'Syntax file has unrecognised duration "' + sl[3] + '" after "' + sl[1] + '".\nMake sure your file complies with syntax requirements and try again.'
                        elif sl[0] == 'mouse' and sl[1] in ['drag']:
                                if len(sl) > 6:
                                        return 'Syntax file has unrecognised command(s) "' + ' '.join(sl[6:]) + '" after "' + sl[1] + '".\nMake sure your file complies with syntax requirements and try again.'
                                elif len(sl) == 6:
                                        if not duration_format.match(sl[5]):
                                                return 'Syntax file has unrecognised duration "' + sl[5] + '" after "' + sl[1] + '".\nMake sure your file complies with syntax requirements and try again.'
                        elif sl[0] == 'wait':
                                if len(sl) > 1:
                                        return 'Syntax file has unrecognised command(s) "' + ' '.join(sl[1:]) + '" after "' + sl[0] + '".\nMake sure your file complies with syntax requirements and try again.'
                                if not duration_format.match(sl[5]):
                                        return 'Syntax file has unrecognised wait duration "' + sl[0][4:] + '".\nMake sure your file complies with syntax requirements and try again.'
        return True

def validate_function_list(function_list):
        valid_functions = ['time.sleep', 'mouse_move', 'mouse_up', 'mouse_down',
                           'mouse_scroll', 'key_up', 'key_down', 'key_type']
        for putative_function in function_list:
                split_func = putative_function.rstrip(')').split('(') # This will provide a list like ['mouse_move', '[400, 500]'] or ['key_press', '["ctrl", "m"], hold_seconds=7.8']
                # Handle key_type functions
                if type(putative_function) == list: # i.e., if this is a key_type function
                        keys, hold_seconds = split_func[1].split(', hold_seconds=')
                        if validate_keyboard(eval(keys)) == False: # keys is a string of a list currently; eval makes it a proper list
                                return False
                        try:
                                float(hold_seconds)
                        except:
                                return False
                # Handle all other functions
                if split_func[0] not in valid_functions:
                        return False
                elif split_func[0] == 'time.sleep':
                        try:
                                float(split_func[1])
                        except:
                                return False
                elif split_func[0] == 'mouse_move':
                        if validate_coord(eval(split_func[1])) == False: # split_func[1] is a string of a coord list e.g., '[400, 500']
                                return False
                elif split_func[0] == 'mouse_up' or split_func[0] == 'mouse_down':
                        if split_func[1] not in ['left', 'middle', 'right']:
                                return False
                elif split_func[0] == 'mouse_scroll':
                        if split_func[1] not in ['-1', '1']:
                                return False
                elif split_func[0] == 'key_up' or split_func[0] == 'key_down':
                        if validate_keyboard(split_func[1]) == False:
                                return False
        return True

def validate_pickle(pickle_file):
        # Validation 1: Pickle module recognises file
        try:
                pickle_contents = pickle.load(open(pickle_file, "rb"))
        except:
                return ['Error: mk_pkl file incorrectly formatted', 'Recording file is not recognised as a true .mk_pkl formatted file.', None]
        # Validation 2: Pickle contents are a function list
        if type(pickle_contents) != list:
                return ['Error: mk_pkl file is not a recording pickle', 'Recording file is a pickle formatted file but was not created by autoMK.', None]
        validation_result = validate_function_list(pickle_contents)
        if validation_result == False:
                return ['Error: mk_pkl file is not a recording pickle', 'Recording file is a pickle formatted file but was not created by autoMK or has been corrupted.', None]
        else:
                return ['Success!', 'Recording file was loaded and validated successfully!', pickle_contents]

def convert_syntax_to_functions(syntax_file):
        duration_format = re.compile(r'duration\d{1,10}(\.\d{1,10})?$')
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
                                                functions_list.append('time.sleep(0)') # Every function needs a time.sleep buffer for FLOG_LOOPING
                                                most_recent_mouse_coord = x_coord, y_coord
                                                functions_list.append('mouse_down("left")')
                                                functions_list.append('time.sleep(' + str(duration) + ')')
                                                functions_list.append('mouse_up("left")')
                                                functions_list.append('time.sleep(0)')
                                        elif sl[1] == 'click_right':
                                                functions_list.append('mouse_move([' + str(x_coord) + ', ' + str(y_coord) + '])')
                                                functions_list.append('time.sleep(0)')
                                                most_recent_mouse_coord = x_coord, y_coord
                                                functions_list.append('mouse_down("right")')
                                                functions_list.append('time.sleep(' + str(duration) + ')')
                                                functions_list.append('mouse_up("right")')
                                                functions_list.append('time.sleep(0)')
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
                                                functions_list.append('time.sleep(0)')
                                elif sl[1] in ['type']:
                                        if sl[1] == 'type':
                                                functions_list.append(['key_type', sl_to_typeable_string(sl[2:]), duration])
                                                functions_list.append('time.sleep(0)')
                        # Wait functions
                        if sl[0].startswith('wait'):
                                duration = float(sl[0][4:])
                                functions_list.append('time.sleep(' + str(duration) + ')')
                                functions_list.append('time.sleep(0)') # FLOG_LOOPING even needs time.sleep to be buffered with time.sleep... bit silly but oh well
        return functions_list

def mouse_move_tween_to_functions(x_coord1, y_coord1, x_coord2, y_coord2, duration_seconds=1, steps_per_second=10):
        try:
                return coordinate_pairs_to_functions(coordinate_tween(x_coord1, y_coord1, x_coord2, y_coord2, duration_seconds, steps_per_second), duration_seconds)
        except ZeroDivisionError:
                return ['mouse_move([' + str(x_coord2) + ', ' + str(y_coord2) + '])']

def mouse_drag_syntax_to_functions(x_coord1, y_coord1, x_coord2, y_coord2, duration_seconds=1, steps_per_second=10):
        functions_list = ['mouse_move([' + str(x_coord1) + ', ' + str(y_coord1) + '])']
        functions_list.append('time.sleep(0)')
        functions_list.append('mouse_down("left")')
        functions_list.append('time.sleep(0)')
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
        functions_list.append('time.sleep(0)') # Adding this in here makes sure our FLOG_LOOPING structure has the proper time.sleep buffer in place
        for pair in coord_pairs:
                functions_list.append('time.sleep(' + str(seconds_per_step) + ')')
                functions_list.append('mouse_move([' + str(pair[0]) + ', ' + str(pair[1]) + '])')
        functions_list.append('time.sleep(0)') # As above, buffer time.sleep
        return functions_list

def mouse_scroll_syntax_to_functions(num_of_scrolls, direction, duration_seconds):
        seconds_per_scroll = duration_seconds / (num_of_scrolls+1) # Add an extra time.sleep() function so we can have a wait before and after our first/last scrolls
        functions_list = ['time.sleep(0)']
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

## Functions related to user interfacing
def key_to_pause_clicked(label_to_update):
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
        keys_to_pause = set()
        for key in keylog.current_log:
                if key.event_type == 'down' and key.time < exit_time:
                        keys_to_pause.add(key.name)
        for click in mouselog.current_log:
                        if type(click) == mouse._mouse_event.ButtonEvent:
                                if click.event_type == 'down' and click.time < exit_time:
                                        keys_to_pause.add(click.button)
        # Call function to present text to user
        keys_to_pause_text(keys_to_pause, label_to_update)
        
def keys_to_pause_text(keys_to_pause, label_to_update):
        # Make keys_to_pause presentable as a string to the user
        keys_to_pause_list = []
        if 'ctrl' in keys_to_pause:
                keys_to_pause_list.append('ctrl') # Bring modifier keys to the front
        if 'shift' in keys_to_pause:
                keys_to_pause_list.append('shift')
        if 'alt' in keys_to_pause:
                keys_to_pause_list.append('alt')
        for key in keys_to_pause:
                if key not in ['ctrl', 'shift', 'alt']:
                        keys_to_pause_list.append(key)
        keys_to_pause_as_string = ' '.join(keys_to_pause_list)
        label_to_update.configure(text=keys_to_pause_as_string) # This value was defined as a global in key_to_pause_clicked

def derive_keys_from_label(label_to_get_string_from): 
        keys_to_pause_as_string = label_to_get_string_from['text']
        keys_to_pause = keys_to_pause_as_string.split(' ')
        return keys_to_pause

def derive_text_from_label(label_to_get_string_from):
        label_text = label_to_get_string_from['text']
        return label_text

def update_label_text(label_to_write_text_to, text):
        label_to_write_text_to['text'] = text

def check_if_keys_pressed(keys_list):
        all_pressed = True
        for key in keys_list:
                if key in ['left', 'middle', 'right']:
                        if not mouse.is_pressed(key):
                                all_pressed = False
                                break
                else:
                        if not keyboard.is_pressed(key):
                                all_pressed = False
                                break
        return all_pressed

def coord_label_update(label_to_get_string_from): # Top-frame; runs globally, connects to x_display_label, y_display_label 
        global PAUSE_COORDS # Making this global lets us reuse it on reiterations
        keys_to_pause = derive_keys_from_label(label_to_get_string_from)
        if keys_to_pause != ['']:
                all_pressed = check_if_keys_pressed(keys_to_pause)
                if all_pressed == True:
                        if PAUSE_COORDS == False:
                                PAUSE_COORDS = True
                        else:
                                PAUSE_COORDS = False
        if PAUSE_COORDS == False:
                x, y = pyautogui.position()
                x_display_label.configure(text=x)
                y_display_label.configure(text=y)
        x_display_label.after(100, coord_label_update, label_to_get_string_from) # Doesn't matter what we attach .after() to

def recording_start_stop(record_key_display_label, record_check_button, options_combo):
        global CURRENTLY_RECORDING
        global MLOG
        global KLOG
        global FLOG
        keys_to_record = derive_keys_from_label(record_key_display_label)
        stop_recording = False
        start_recording = False
        if record_check_button.state.get() == True or CURRENTLY_RECORDING == True: # This or system prevents record_check_button checking from preventing us stopping a current recording session
                if keys_to_record != ['']:
                        all_pressed = check_if_keys_pressed(keys_to_record)
                        if all_pressed == True:
                                if CURRENTLY_RECORDING == True:
                                        stop_recording = True
                                else:
                                        start_recording = True
        if start_recording == True:
                recording_option = options_combo.get()
                if recording_option == 'mouse' or recording_option == 'mouse+keyboard':
                        MLOG = Mouselogging()
                        MLOG.start_logging()
                if recording_option == 'keyboard' or recording_option == 'mouse+keyboard':
                        KLOG = Keylogging()
                        KLOG.start_logging()
                CURRENTLY_RECORDING = True
        elif stop_recording == True:
                # Gather our logs
                if 'MLOG' in globals(): # Could check the combobox, but it's possible that value has changed since we started recording
                        MLOG.stop_logging()
                        if 'KLOG' not in globals():
                                CLOG = MLOG
                if 'KLOG' in globals():
                        KLOG.stop_logging()
                        if 'MLOG' not in globals():
                                CLOG = KLOG
                if 'MLOG' in globals() and 'KLOG' in globals():
                        CLOG = merge_logs(KLOG, MLOG) # CLOG stands for combined log
                # Convert logs to functions
                FLOG = convert_log_to_functions(CLOG) # FLOG now stands for functions log
                CURRENTLY_RECORDING = False
        record_key_display_label.after(100, recording_start_stop, record_key_display_label, record_check_button, options_combo)

def playback_start_stop(playback_container_label, playback_key_display_label, playback_check_button, playback_speed_entry):
        global FLOG
        # Validate playback_speed_entry value
        integer_validation_result = validate_positive_integer(playback_speed_entry.get())
        if integer_validation_result == False:
                messagebox.showinfo('Error: Playback speed is flawed', 'Playback speed must be a positive integer.')
                return None
        playback_container_label.speed_modifier = playback_speed_entry.get()
        # Main playback_start_stop function
        keys_to_playback = derive_keys_from_label(playback_key_display_label)
        stop_playback = False
        start_playback = False
        if playback_check_button.state.get() == True or playback_container_label.currently_playing == True: # This or system prevents playback_check_button checking from preventing us stopping a current playback session
                if keys_to_playback != ['']:
                        all_pressed = check_if_keys_pressed(keys_to_playback)
                        if all_pressed == True:
                                if playback_container_label.currently_playing == True:
                                        stop_playback = True
                                else:
                                        start_playback = True
        if start_playback == True:
                global FLOG_LOOPING
                FLOG_LOOPING = copy.deepcopy(FLOG) # This will be a list we constantly reorder, leaving the original FLOG intact for restarting playback
                playback_container_label.currently_playing = True
        if stop_playback == True:
                playback_container_label.currently_playing = False
        playback_key_display_label.after(100, playback_start_stop, playback_container_label, playback_key_display_label, playback_check_button, playback_speed_entry)

def playback(playback_container_label):
        global FLOG_LOOPING
        if playback_container_label.currently_playing == True: # As soon as this becomes False playback will stop automatically
                function = FLOG_LOOPING[0]
                if type(function) == str:
                        eval(function)
                        wait = int(round(float(FLOG_LOOPING[1].split('(')[1].rstrip(')')) * 1000)) # .after() reads times as miliseconds whereas FLOG/FLOG_LOOPING are in seconds; it also requires integer values
                elif type(function) == list:
                        if function[0] == 'key_type':
                                key_type(function[1], typing_seconds=function[2])
                                wait = int(round(FLOG_LOOPING[1][2]) * 1000) # .after() reads times as miliseconds whereas FLOG/FLOG_LOOPING are in seconds; it also requires integer values
                FLOG_LOOPING.append(FLOG_LOOPING.pop(0)) # Doing this rotates the first entry to the last position
                FLOG_LOOPING.append(FLOG_LOOPING.pop(0))
                playback_container_label.after(wait, playback, playback_container_label)
        else:
                playback_container_label.after(100, playback, playback_container_label)

def play_functions_list(functions_list):
        for function in functions_list:
                if type(function) == str:
                        eval(function)
                elif type(function) == list:
                        if function[0] == 'key_type':
                                key_type(function[1], typing_seconds=function[2])

def browse_for_file(entry_to_write_to):
        file_location = filedialog.askopenfilename()
        entry_to_write_to.delete(0, END)
        entry_to_write_to.insert(END, file_location)

def save_as_file(entry_to_write_to):
        file_location = filedialog.asksaveasfilename(defaultextension='.mk_pkl', initialdir=os.getcwd(), filetypes=[('autoMK pkl', '.mk_pkl')])
        if file_location is None: # asksaveasfile returns `None` if dialog closed with "cancel".
                return None
        entry_to_write_to.delete(0, END)
        entry_to_write_to.insert(END, file_location)

def validate_recording_file(entry_to_get_string_from):
        global FLOG
        recording_file = entry_to_get_string_from.get()
        # Validate file exists
        if not os.path.isfile(recording_file):
                messagebox.showinfo('Error: File doesn\'t exist', 'Recording file could not be located at the specified location.')
                return None
        # Validate file type
        ACCEPTED_FILE_TYPES = ['mk_pkl', 'mk_syn']
        if '.' not in recording_file:
                messagebox.showinfo('Error: File has no extension', 'Recording file does not have a file extension. It should end with .mk_pkl or .mk_syn.')
                return None
        recording_file_extension = recording_file.rsplit('.', maxsplit=1)[1]
        if recording_file_extension.lower() not in ACCEPTED_FILE_TYPES:
                messagebox.showinfo('Error: File extension unrecognised', 'Recording file has unknown file extension. It should end with .mk_pkl or .mk_syn.')
                return None
        # Validate .mk_syn files
        file_result = validate_syntax(recording_file)
        if type(file_result) == str:
                messagebox.showinfo('Error: mk_syn file incorrectly formatted', file_result)
                return None
        else:
                messagebox.showinfo('Success!', 'Recording file was loaded and validated successfully!')
                FLOG = convert_syntax_to_functions(recording_file) # FLOG stands for function log; value made by this function or recording_start_stop()
                return None
        # Validate .mk_pkl files
        message_title, message_body, pickle_contents = validate_pickle(recording_file)
        messagebox.showinfo(message_title, message_body)
        if message_title != 'Success!':
                return None
        else:
                FLOG = pickle_contents
                return None

def validate_save_file(entry_to_get_string_from):
        file_output_name = entry_to_get_string_from.get()
        # Validate file exists
        if os.path.isfile(file_output_name):
                messagebox.showinfo('Error: File already exists', 'Recording file cannot overwrite existing files.')
                return None
        # Validate file type
        ACCEPTED_FILE_TYPES = ['mk_pkl']
        if '.' not in file_output_name:
                messagebox.showinfo('Error: File has no extension', 'Recording file does not have a file extension. It should end with .mk_pkl or .mk_syn.')
                return None
        recording_file_extension = file_output_name.rsplit('.', maxsplit=1)[1]
        if recording_file_extension.lower() not in ACCEPTED_FILE_TYPES:
                messagebox.showinfo('Error: File extension unrecognised', 'Recording file has unknown file extension. It should end with .mk_pkl or .mk_syn.')
                return None
        # Let user know it's all good!
        messagebox.showinfo('Success!', 'Recording file was saved successfully!')
        global SAVED_FILE_NAME
        SAVED_FILE_NAME = file_output_name

def gui_window():
        # Set variables which are global in scope
        global PAUSE_COORDS # This value needs to be global to be reused in the coord_label_update loop
        PAUSE_COORDS = False # Note: it is possible to remove this as a global
        global x_display_label # This value needs to be updated in the coord_label_update loop
        global y_display_label # As above
        global CURRENTLY_RECORDING # This value needs to be updated by recording_start_stop()
        CURRENTLY_RECORDING = False # As above
        # Set up Tkinter window object
        window = Tk() # Main GUI object
        window.title('autoMK') # Sets the title that displays on the top bar
        window.geometry('{}x{}'.format(900, 400)) # width, height
        # Create main frame container objects
        top_frame = Frame(window, width=350, height=200) # This will hold the coord widgets
        bottom_frame_record = Frame(window, width=350, height=300) # This will hold the recording widgets
        bottom_frame_playback = Frame(window, width=350, height=300) # This will hold the playback widgets
        # Layout of main frame containers
        #window.grid_rowconfigure(1, weight=1)
        #window.grid_columnconfigure(0, weight=1)
        top_frame.grid(row=0, sticky="nsew")
        bottom_frame_record.grid(row=1, sticky="nsew")
        bottom_frame_playback.grid(row=2, sticky="nsew") # rewrite to overlap above frame soon
        # Create widgets for top frame
        pause_text_label = Label(top_frame, text='Key to pause coord:')
        key_display_label = Label(top_frame, text='', bg='white') # This label has the keys_to_pause value set as its ['text'] attribute; can be retrieved with derive_keys_from_label()
        key_set_button = Button(top_frame, text='Click to record key', command=partial(key_to_pause_clicked, key_display_label)) # Partial lets us pass arguments in command=
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
        recording_browse_button = Button(bottom_frame_record, text='Browse', command=partial(browse_for_file, recording_location_entry))
        recording_validate_button = Button(bottom_frame_record, text='Load', command=partial(validate_recording_file, recording_location_entry))
        ##
        generate_text_label = Label(bottom_frame_record, text='Generate new recording:')
        options_combo = Combobox(bottom_frame_record)
        options_combo['values'] = ('mouse', 'keyboard', 'mouse+keyboard')
        options_combo.current(2) # Sets the "default" value to mouse+keyboard, 0-indexed according to dict associated with widget
        ##
        record_pause_text_label = Label(bottom_frame_record, text='Key to start/stop recording:')
        record_key_display_label = Label(bottom_frame_record, text='', bg='white')
        record_key_set_button = Button(bottom_frame_record, text='Click to record key', command=partial(key_to_pause_clicked, record_key_display_label))
        record_check_button_state = BooleanVar()
        record_check_button = Checkbutton(bottom_frame_record, text='Activate button', var=record_check_button_state)
        record_check_button.state = record_check_button_state
        # Layout of bottom frame widgets
        load_text_label.grid(row=3, column=0)
        recording_location_entry.grid(row=3, column=1)
        recording_browse_button.grid(row=3, column=2)
        recording_validate_button.grid(row=3, column=3)
        ##
        generate_text_label.grid(row=4, column=0)
        options_combo.grid(row=4, column=1)
        ##
        record_pause_text_label.grid(row=5, column=0)
        record_key_display_label.grid(row=5, column=1)
        record_key_set_button.grid(row=5, column=2)
        record_check_button.grid(row=5, column=3)
        # Create widgets for playback bottom frame
        playback_text_label = Label(bottom_frame_playback, text='Key to start/stop playback:')
        playback_key_display_label = Label(bottom_frame_playback, text='', bg='white')
        playback_key_set_button = Button(bottom_frame_playback, text='Click to record key', command=partial(key_to_pause_clicked, playback_key_display_label))
        playback_check_button_state = BooleanVar()
        playback_check_button = Checkbutton(bottom_frame_playback, text='Activate button', var=playback_check_button_state)
        playback_check_button.state = playback_check_button_state
        ##
        playback_speed_label_prefix = Label(bottom_frame_playback, text='Playback speed modifier:')
        playback_speed_entry = Entry(bottom_frame_playback, width=3)
        playback_speed_entry.insert(END, 1)
        playback_speed_label_suffix = Label(bottom_frame_playback, text='x')
        ##
        save_recording_label = Label(bottom_frame_playback, text='Save recording:')
        save_recording_location_entry = Entry(bottom_frame_playback, width=40)
        save_recording_location_entry.insert(END, os.path.join(os.getcwd(), 'autoMK_' + '-'.join([str(date.today().day), str(date.today().month), str(date.today().year)]) + '.mk_pkl'))
        save_recording_browse_button = Button(bottom_frame_playback, text='Browse', command=partial(save_as_file, save_recording_location_entry))
        save_recording_validate_button = Button(bottom_frame_playback, text='Save', command=partial(validate_save_file, save_recording_location_entry))
        # Layout of playback bottom frame widgets
        playback_text_label.grid(row=6, column=0) # These will be rewritten to overlap the recording bottom frame soon
        playback_key_display_label.grid(row=6, column=1)
        playback_key_set_button.grid(row=6, column=2)
        playback_check_button.grid(row=6, column=3)
        ##
        playback_speed_label_prefix.grid(row=7, column=0)
        playback_speed_entry.grid(row=7, column=1)
        playback_speed_label_suffix.grid(row=7, column=2)
        ##
        save_recording_label.grid(row=8, column=0)
        save_recording_location_entry.grid(row=8, column=1)
        save_recording_browse_button.grid(row=8, column=2)
        save_recording_validate_button.grid(row=8, column=3)
        # Create label containers for ongoing functions
        playback_container_label = Label(window, text='')
        playback_container_label.currently_playing = False
        playback_container_label.after(100, playback_start_stop, playback_container_label, playback_key_display_label, playback_check_button, playback_speed_entry)
        playback_container_label.after(100, playback, playback_container_label) # playback and playback_start_stop interact with each other, with playback_start_stop setting values in playback which... start and stop playback
        # Call ongoing functions acting on global values
        key_display_label.after(100, coord_label_update, key_display_label) # Makes use of (x/y)_display_label and PAUSE_COORDS
        record_key_display_label.after(100, recording_start_stop, record_key_display_label, record_check_button, options_combo) ## TBD
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
