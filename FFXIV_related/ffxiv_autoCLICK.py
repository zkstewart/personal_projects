#! python3
# autoMK.py
# Framework for automating mouse and keyboard actions. Windows only.
'''Functions list:
-Mouse coordinate helper
-Mouse scroll helper
-Mouse click, press, depress, move, drag, scroll
-Keyboard type, 
TBD:
-Window helper
'''

'''Current areas for modification / improvement:
        1-Add tweening functions to mouse movement [complicates syntax? unnecessary?]
        2-Add relative dragging
        3-Multiple point dragging [unnecessary? can be accomplished with mouse down->move->mouse up]
'''

# Import modules
import os, pyautogui, keyboard, queue, ctypes, screeninfo, time, sys, random, cv2
from PIL import Image
import numpy as np
from mss import mss

# Hard-coded parameter setup
WHEEL_DELTA = 120 # Taken from boppreh's _winmouse.py code, used as Windows OS default scroll distance
MOUSEEVENTF_WHEEL = 0x800 # Taken from boppreh's _winmouse.py code
user32 = ctypes.WinDLL('user32', use_last_error = True) # Taken from boppreh's _winmouse.py code

# Define functions
## Template-matching related
def take_screenshot(subsection_coords=None):
        '''subsection_coords specifies the range to screenshot; also, some code borrowed from
        https://www.tautvidas.com/blog/2018/02/automating-basic-tasks-in-games-with-opencv-and-python/
        Note that the width and height values that mss().grab() uses refers not to the
        actual coordinate value but merely the width FROM the left or height FROM
        the top coordinate.
        '''
        if subsection_coords == None:
                '''i.e., by default we capture the whole screen'''
                monitor = screeninfo.get_monitors()[0]
                grab_coords = {'left': monitor.x, 'top': monitor.y, 'width': monitor.width, 'height': monitor.height}
        else:
                grab_coords = {'left': subsection_coords[0], 'top': subsection_coords[1], 'width': subsection_coords[2], 'height': subsection_coords[3]}
        while True:
                try:
                        with mss() as sct:
                                screenshot_image = sct.grab(grab_coords)
                        break
                except:
                        time.sleep(1)
        img = Image.frombytes('RGB', screenshot_image.size, screenshot_image.rgb)
        img = np.array(img)
        img = img[:, :, ::-1]
        screenshot_grayscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return screenshot_grayscale

def screenshot_template_match_topleftcoords(screenshot_grayscale, template_file, threshold=0.9):
        '''Some code borrowed from
        https://www.tautvidas.com/blog/2018/02/automating-basic-tasks-in-games-with-opencv-and-python/
        '''
        # Load template file for recognition
        template = cv2.imread(template_file, 0)
        # Run template matching
        res = cv2.matchTemplate(screenshot_grayscale, template, cv2.TM_CCOEFF_NORMED)
        matches = np.where(res >= threshold)
        # Validate that pattern matching was successful
        if len(matches[0]) == 0: # Specific to autoCLICK we don't care if there are multiple matches, that seems to be normal for this template
                return False, False # Return two values to not break downstream expectations
        # Derive coordinates of template image
        y_coord, x_coord = matches[0][0], matches[1][0]
        return x_coord, y_coord

## Mouse controls
def mouse_move(coord):
        '''We use ctypes instead of pyautogui since ctypes supports moving the
        mouse across multiple monitors.'''
        ctypes.windll.user32.SetCursorPos(coord[0], coord[1])

def mouse_down(button, seconds=1):
        pyautogui.mouseDown(button=button, pause=seconds)

def mouse_up(button, seconds=1):
        pyautogui.mouseUp(button=button, pause=seconds)

def variableTime(time):
        return time + random.random()

## Keylogger-related
def start_key_logger():
        q = queue.Queue()
        keyboard.start_recording(q)
        return q

def stop_key_logger():
        q = keyboard.stop_recording()
        return q

def key_logger_specialcommand_queue(q):  # q should be a queue. Queue object from 'keyboard' module
        specialKeys = ['shift', 'alt', 'ctrl']
        s = ''
        ctrldown = False
        shiftdown = False
        altdown = False
        for k in q:  # q contains individual key values ('k') which contain methods from 'keyboard'
                # Handle special keys and events
                if k.event_type == 'up':
                        if k.name == 'ctrl':
                                ctrldown = False
                        elif k.name == 'shift':
                                shiftdown = False
                        elif k.name == 'alt':
                                altdown = False
                        continue
                elif k.name in specialKeys:
                        if k.name == 'ctrl':
                                ctrldown = True
                        elif k.name == 'shift':
                                shiftdown = True
                        elif k.name == 'alt':
                                altdown = True
                        continue
                else:
                        if ctrldown == True:
                                s += 'CTRL_' + k.name.lower() + '_'
                        elif shiftdown == True:
                                s+= 'SHIFT_' + k.name.lower() + '_'
                        elif altdown == True:
                                s+= 'ALT_' + k.name.lower() + '_'
        return s

def restart_keylogger_for_specialcommand(string):
        q = stop_key_logger()
        s = key_logger_specialcommand_queue(q)
        if string in s:
                print('Ctrl-Esc command received; program will terminate')
                sys.exit()
        else:
                q = start_key_logger()
                return q

# Hard-coded definitions for screen locations
def skillbar4_coordinates():
        return [[710,780],[755,780],[800,780],[845,780],[890,780],[935,780],[980,780],[1025,780],[1070,780],[1115,780],[1160,780],[1205,780]]

# Hard-coded definitions for specific macros
def craft(skillbar_coords, wait_times, num_iterations, template_directory):
        # Hard-coded values and offsets
        SYNTHESIZE_X_OFFSET = 50
        SYNTHESIZE_Y_OFFSET = 15
        WAIT_TIME = 2
        # Monitor dimensions
        monitor = screeninfo.get_monitors()[0]
        # Sanity check inputs
        assert len(skillbar_coords) == len(wait_times)
        # Run loop
        for i in range(num_iterations):
                for x in range(len(skillbar_coords)):
                        q = start_key_logger()
                        if x == 0: # Click the synthesise button and give character time to set up
                                while True:
                                        screenshot_grayscale = take_screenshot()
                                        synthesize_x_coord, synthesize_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'synthesize_button.png'))
                                        if synthesize_x_coord == False:
                                                print('Synthesize button not visible; waiting ' + str(WAIT_TIME) + ' seconds...')
                                                time.sleep(WAIT_TIME)
                                                continue
                                        break
                                mouse_move([int(synthesize_x_coord+int(SYNTHESIZE_X_OFFSET / (1920 / monitor.width))), int(synthesize_y_coord+int(SYNTHESIZE_Y_OFFSET / (1080 / monitor.height)))])
                                mouse_down('left')
                                sleepTime=variableTime(0.2)
                                time.sleep(sleepTime)
                                mouse_up('left')
                                sleepTime=variableTime(1.5) 
                                time.sleep(sleepTime)
                                q = restart_keylogger_for_specialcommand('CTRL_esc')
                        # Click macro button and wait
                        mouse_move(skillbar_coords[x])
                        mouse_down('left')
                        sleepTime=variableTime(0.2)
                        time.sleep(sleepTime)
                        mouse_up('left')
                        sleepTime=variableTime(wait_times[x])
                        time.sleep(sleepTime)
                        q = restart_keylogger_for_specialcommand('CTRL_esc')

def main():
        # Hard-coded declarations of relevant file locations
        '''It will be ideal to somehow store this in a semi-permanent way within
        the code; need to learn how to do that first!
        '''
        template_directory = r'C:\Bioinformatics\GitHub\personal_projects\FFXIV_related\template_images\autoclick'
        # Single monitor mode
        if len(screeninfo.get_monitors()) == 1:
                single_monitor_mode = True
                SINGLE_MONITOR_DELAY = 10
        else:
                single_monitor_mode = False
        if single_monitor_mode:
                print('Single monitor mode is active; ' + str(SINGLE_MONITOR_DELAY) + ' second delay will be enacted now to allow for alt tabbing.')
                time.sleep(SINGLE_MONITOR_DELAY)
        #craft([skillbar4_coordinates()[0]], [41.5], 20, template_directory) # Hard-coded macro 1: 40dur 1800p 17.0k nf
        #craft([skillbar4_coordinates()[1]], [37], 20, template_directory) # Hard-coded macro 2: 40dur 1600p 15.0k nf
        craft([skillbar4_coordinates()[11]], [11], 22, template_directory) # Hard-coded macro 3: instacraft
        

if __name__ == '__main__':
        main()