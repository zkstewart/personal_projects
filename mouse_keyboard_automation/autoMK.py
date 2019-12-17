#! python3
# autoMK.py
# Framework for automating mouse and keyboard actions. Windows only.
# Made by Zachary Stewart; intended as a gift to Jordan Stewart.
'''

'''

# Import modules
import pyautogui, pygetwindow, keyboard, mouse, queue, ctypes, screeninfo, time

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
                self.current_log = list(self.queue)
        def block_until(self, break_key):
                self.is_logging = True
                self.queue = keyboard.record(until = break_key)
                self.is_logging = False

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

def shrink_typing_functions(functions_list):
        def derive_function_type(function):
                if function.startswith('mouse'):
                        return 'mouse'
                elif function.startswith('time'):
                        return 'time'
                elif function.startswith('key'):
                        return 'key'
        # Setup
        new_functions_list = []
        previous_function = None
        previous_function_type = None
        ctrlkey_pressed = False
        shiftkey_pressed = False
        altkey_pressed = False
        # Main function loop
        for function in functions_list:
                function_type = derive_function_type(function)
                # Handle hotkey presses
                if function_type == 'key':
                        key_pressed, key_direction = function.split('"')[1], function.split('(')[0].split('_')[1]
                        if (key_pressed == 'ctrl' or key_pressed == 'shift' or key_pressed == 'alt') and key_direction == 'down':
                                if key_pressed == 'ctrl':
                                        ctrlkey_pressed = True
                                elif key_pressed == 'shift':
                                        shiftkey_pressed = True
                                elif key_pressed == 'alt':
                                        altkey_pressed = True
                        elif (key_pressed == 'ctrl' or key_pressed == 'shift' or key_pressed == 'alt') and key_direction == 'up':
                                if key_pressed == 'ctrl':
                                        ctrlkey_pressed = False
                                elif key_pressed == 'shift':
                                        shiftkey_pressed = False
                                elif key_pressed == 'alt':
                                        altkey_pressed = False
                # Handle new key chains
                if previous_function_type != 'key' and function_type == 'key':
                        key_pressed, key_direction = function.split('"')[1], function.split('(')[0].split('_')[1]
                        # Handle hotkeys
                        if (key_pressed == 'ctrl' or key_pressed == 'shift' or key_pressed == 'alt') and key_direction == 'down':
                                hotkey_pressed = key_pressed
                                process_key_chain(hotkey_chain) #TBD
                                hotkey_chain = [function]
                                sleep_chain = []
                        # Handle normal keys
                        elif key_direction == 'down':
                                process_key_chain(hotkey_chain) #TBD
                                typing_chain = [function]
                                sleep_chain = []
                # Handle stops inbetween a key chain
                elif previous_function_type == 'key' and function_type == 'time':
                        sleep_chain.append(function) # This is mostly ignored e.g., we don't count it as a previous_function
                # Handle key chain continuation
                elif previous_function_type == 'key' and function_type == 'time':
                        key_pressed, key_direction = function.split('"')[1], function.split('(')[0].split('_')[1]
                        # Handle hotkeys
                        if (key_pressed == 'ctrl' or key_pressed == 'shift' or key_pressed == 'alt') and key_direction == 'down':
                                hotkey_chain.append(function)
                        # Handle normal keys
                        elif key_direction == 'down':
                                typing_chain.append(function)
                
                
                if function.startswith('mouse'):
                        new_functions_list.append(function)
                
                previous_function = function
                previous_function_type = function_type
                
        pass

def convert_syntax_to_functions(syntax_file):
        # TBD
        pass

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
                eval(function)

## Mouse controls
def mouse_move(coord):
        '''We use ctypes instead of pyautogui since ctypes supports moving the
        mouse across multiple monitors.'''
        ctypes.windll.user32.SetCursorPos(coord[0], coord[1])

def mouse_down(button, seconds=0):
        pyautogui.mouseDown(button=button, pause=seconds)

def mouse_up(button, seconds=0):
        pyautogui.mouseUp(button=button, pause=seconds)

def mouse_scroll(delta): # Delta should be 1.0 or -1.0
        code = MOUSEEVENTF_WHEEL
        user32.mouse_event(code, 0, 0, int(delta * WHEEL_DELTA), 0)

## Keyboard controls
def key_down(key, pause_seconds=0):
        pyautogui.keyDown(key, pause=pause_seconds)

def key_up(key, pause_seconds=0):
        pyautogui.keyUp(key, pause=pause_seconds)

def key_sequentialpress(keys_string, typing_seconds=1, pause_seconds=0):
        key_press_interval = typing_seconds / len(keys_string)
        pyautogui.typewrite(keys_string, interval=key_press_interval, pause_seconds=0)

def key_multiplepress(keys_list, pause_seconds=0):
        pyautogui.hotkey(*keys_list)

## Validation
def validate_coord(coord):
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
                if coord[0] in range(mcRange[0], mcRange[1]+1) and coord[1] in range(mcRange[2], mcRange[3]+1):  # +1 since we're providing 0-based numbers to range
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
                                ' monitor coordinates are listed below.\n{}'.format(*coord, debuggingText)))

def validate_window(windowTitle):
        '''This function is necessary to ensure that a window with the name provided
        actually exists.'''
        # Locate all window titles
        titles = pygetwindow.getAllTitles()
        nocaseTitles = [title.lower() for title in titles]
        # Find an exact match for windowTitle in titles list
        outputTitle = None  # this remains as none if we don't find the window
        if windowTitle in titles:
                outputTitle = windowTitle  # nothing needs to change
        else:
                bestMatch = None
                for i in range(len(nocaseTitles)):
                        # Find a case-insensitive match
                        if windowTitle.lower() == nocaseTitles[i]:
                                outputTitle = titles[i]  # now windowTitle has correct captialisation
                                break
                        # Find a non-ambiguous, case-insensitive best match
                        elif windowTitle.lower() in nocaseTitles[i] and bestMatch == None:
                                bestMatch = windowTitle
                        elif windowTitle.lower() in nocaseTitles[i] and bestMatch != None:
                                bestMatch = False
        # Return validated window if found
        if outputTitle != None:
                return outputTitle
        elif bestMatch != None and bestMatch != False:
                return bestMatch
        # Raise exception if window was not found
        else:
                raise Exception((
                                'The provided window title "{}" cannot be found.'
                                '\nEnsure that this window is open or you have typed'
                                ' the window title correctly and try again.'
                                '\nFor debugging, existing window titles are listed below.'
                                '\n{}'.format(*[windowTitle,titles])))

def validate_mouse(coord=None, button=None, clicks=None, interval=None, duration=None):
        # Validate that coord specified is sensible
        if coord != None:
                fail = False
                if not type(coord) == list:
                        fail = True
                elif len(coord) != 2:
                        fail = True
                elif type(coord[0]) != int and type(coord[1]) != int:
                        fail = True
                if fail == True:
                        raise Exception((
                                'Coord value "{}" is not recognised. Fix'
                                ' required at the code level i.e., tell Zac'
                                ' something is wrong.'.format(coord)))
        # Validate that the mouse button specified is sensible
        buttons = ['left', 'right', 'middle']
        if button == None:
                button = 'left'
        elif button.lower() not in buttons:
                raise Exception((
                                'Mouse button "{}" is not recognised. This must be'
                                '"left", "right", or "middle".'.format(button)))
        # Validate that click type specified is sensible
        if clicks == None:
                clicks = 1
        elif not type(clicks) == int:
                raise Exception((
                                'Click value "{}" is not int.'.format(clicks)))
        elif clicks > 1:
                raise Exception((
                                'Click value "{}" is less than 1.'.format(clicks)))
        # Validate that interval specified is sensible
        if interval == None:
                interval = 0.0
        elif not type(interval) == float:
                raise Exception((
                                'Interval value "{}" is not float.'.format(interval)))
        elif interval > 0.0:
                raise Exception((
                                'Interval value "{}" is negative.'.format(interval)))
        # Validate that duration specified is sensible
        if duration == None:
                duration = 0.0
        elif not type(duration) == float:
                raise Exception((
                                'Duration value "{}" is not float.'.format(duration)))

def validate_scroll(units, direction):
        # Ensure that units value is sensible
        try:
                units = int(units)
        except:
                print(('Scroll units provided "{}" is not int. Specify a whole'
                       ' number, positive or negative, and try again.'
                       .format(units)))
                quit()
        # Ensure that direction is sensible
        directions = ['up', 'down']
        if direction.lower() not in directions:
                raise Exception(('Direction value provided "{}" is not "up" or'
                                 ' "down".'.format(direction)))
        units = abs(units)
        if direction.lower() == 'down':
                units = -units
        return units

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
        if type(keys) != list:
                raise Exception((
                                'Keys value provided to keyboardPress'
                                ' is not a list. Fix required at the code level.'
                                ' i.e., tell Zac something is wrong.'))
        for key in keys:
                if key.lower() not in validKeys:
                        raise Exception((
                                        'Key value "{}" is not valid. Refer to'
                                        ' https://pyautogui.readthedocs.io/en/'
                                        'latest/keyboard.html#keyboard-keys'
                                        ' for a list of valid key identifiers'
                                        .format(key)))
        # Ensure that presses is sensible
        if presses == None:
                presses = 1
        elif not type(presses) == int:
                raise Exception((
                                'Presses value "{}" is not int.'.format(presses)))
        elif presses > 1:
                raise Exception((
                                'Presses value "{}" is less than 1.'.format(presses)))
        # Ensure that interval is sensible
        if interval == None:
                interval = 0.0
        elif not type(interval) == float:
                raise Exception((
                                'Interval value "{}" is not float.'.format(interval)))
        elif interval > 0.0:
                raise Exception((
                                'Interval value "{}" is negative.'.format(interval)))

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
        pass
