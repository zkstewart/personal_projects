#! python3
# ffxiv_mb_price_tabulate.py
# Script which automates the horribly tedious process of checking the marketboard
# for item prices. It works on the clipboard, so no command-line arguments are
# required.

# Import modules
import pyperclip, cv2, screeninfo, os, ctypes, pyautogui, time, mouse
import numpy as np
from PIL import Image
from mss import mss

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
        if len(matches[0]) == 0 or len(matches[0]) > 1:
                return False, False # Return two values to not break downstream expectations
        # Derive coordinates of template image
        y_coord, x_coord = matches[0][0], matches[1][0]
        return x_coord, y_coord

def screenshot_template_match_multiple(screenshot_grayscale, template_file, threshold=0.95):
        '''Some code borrowed from
        https://www.tautvidas.com/blog/2018/02/automating-basic-tasks-in-games-with-opencv-and-python/
        '''
        # Load template file for recognition
        template = cv2.imread(template_file, 0)
        # Run template matching
        res = cv2.matchTemplate(screenshot_grayscale, template, cv2.TM_CCOEFF_NORMED)
        matches = np.where(res >= threshold)
        # Validate that pattern matching was successful
        if len(matches[0]) == 0:
                return False, False # Return two values to not break downstream expectations
        # Derive coordinates of template image
        y_coords, x_coords = [], []
        for i in range(len(matches[0])):
                y_coords.append(matches[0][i])
                x_coords.append(matches[1][i])
        return x_coords, y_coords

def screenshot_number_automatic_capture(screenshot_grayscale, template_directory, file_suffix, threshold=0.95):
        digit_list = []
        for x in range(0, 10):
                x_coords, y_coords = screenshot_template_match_multiple(screenshot_grayscale, os.path.join(template_directory, str(x) + file_suffix), threshold)
                if x_coords != False:
                        for x_coord in x_coords:
                                digit_list.append([x_coord, x])
        if digit_list == []:
                return False
        digit_list.sort()
        output_digit = ''
        for digit_pair in digit_list:
                output_digit += str(digit_pair[1])
        return output_digit

def screenshot_server_automatic_capture(screenshot_grayscale, template_directory, file_suffix):
        KNOWN_SERVERS = ['Adamantoise', 'Cactaur', 'Faerie', 'Gilgamesh', 'Jenova', 'Midgardsormr', 'Sargatanas', 'Siren'] # This is sorted according to template files 1server.png, 2server.png, etc.,
        for x in range(1, 9):
                x_coords, y_coords = screenshot_template_match_multiple(screenshot_grayscale, os.path.join(template_directory, str(x) + file_suffix), 0.9)
                if x_coords != False:
                        return KNOWN_SERVERS[x-1] # Need to do this since our files start at 1, but list is indexed starting at 0
        return False

def wait_for_slow_response(template_file, threshold=0.95): # This function became necessary when running the program on a slow laptop
        while True:
                screenshot_grayscale = take_screenshot()
                x_coord, y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, template_file)
                if x_coord != False:
                        time.sleep(0.5)
                        continue
                break

def find_correct_item_from_mb(item_name, item_search_x_coord, item_search_y_coord, template_directory, file_suffix):
        def test_for_misalignment(monitor, item_search_x_coord, item_search_y_coord, ALPHABET, ITEM_NAMES_X_OFFSET, ITEM_NAMES_Y_OFFSET, ITEM_NAMES_Y_OFFSET_MISALIGNED, NAME_WIDTH, NAME_HEIGHT):
                capitals = []
                itemname_screenshot_grayscale = take_screenshot((item_search_x_coord+int(ITEM_NAMES_X_OFFSET / (1920 / monitor.width)), item_search_y_coord+int(ITEM_NAMES_Y_OFFSET / (1080 / monitor.height))+int((abs(int(NAME_HEIGHT / (1080 / monitor.height))))*i), abs(int(NAME_WIDTH / (1920 / monitor.width))), int(int(NAME_HEIGHT / (1080 / monitor.height)))))
                for letter in ALPHABET:
                        x_coord, y_coord = screenshot_template_match_multiple(itemname_screenshot_grayscale, os.path.join(template_directory, letter + file_suffix))
                        if x_coord != False:
                                for occurrence in x_coord:
                                        capitals.append(letter)
                if capitals == []:
                        return True
                else:
                        return False
        # Hard-coded values
        ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        ITEM_NAMES_X_OFFSET = 345
        ITEM_NAMES_Y_OFFSET = 65
        ITEM_NAMES_Y_OFFSET_MISALIGNED = 85 # On the last screen if we scroll, it will always be a bit "misaligned"
        NAME_WIDTH = 345
        NAME_HEIGHT = 30
        ITEMS_PER_SCREEN = 16 # At 1080p XIV presents 16 items in a screen before scrolling becomes necessary to view more
        monitor = screeninfo.get_monitors()[0] # This is our main monitor's dimensions
        # Analyse item_name to figure out its capitals and presence of "of"
        words = item_name.split(' ')
        target_capitals = []
        for word in words:
                if word == 'of':
                        target_capitals.append(word)
                else:
                        target_capitals.append(word[0].upper())
        # Main loop
        matched_index = None
        end_of_items = False
        while True:
                # Scan through items and derive the number of capital letters and presence/absence of "of"
                for i in range(ITEMS_PER_SCREEN):
                        capitals = []
                        # Test for misalignment caused by being at the bottom of a scrolled item list
                        if i == 0:
                                misaligned = test_for_misalignment(monitor, item_search_x_coord, item_search_y_coord, ALPHABET, ITEM_NAMES_X_OFFSET, ITEM_NAMES_Y_OFFSET, ITEM_NAMES_Y_OFFSET_MISALIGNED, NAME_WIDTH, NAME_HEIGHT)
                        # Screenshot the correct portion of the screen dependent on whether misalignment is present
                        if misaligned == False:
                                itemname_screenshot_grayscale = take_screenshot((item_search_x_coord+int(ITEM_NAMES_X_OFFSET / (1920 / monitor.width)), item_search_y_coord+int(ITEM_NAMES_Y_OFFSET / (1080 / monitor.height))+int((abs(int(NAME_HEIGHT / (1080 / monitor.height))))*i), abs(int(NAME_WIDTH / (1920 / monitor.width))), int(int(NAME_HEIGHT / (1080 / monitor.height)))))
                        else:
                                itemname_screenshot_grayscale = take_screenshot((item_search_x_coord+int(ITEM_NAMES_X_OFFSET / (1920 / monitor.width)), item_search_y_coord+int(ITEM_NAMES_Y_OFFSET_MISALIGNED / (1080 / monitor.height))+int((abs(int(NAME_HEIGHT / (1080 / monitor.height))))*i), abs(int(NAME_WIDTH / (1920 / monitor.width))), int(int(NAME_HEIGHT / (1080 / monitor.height)))))
                        # Template match for capital letters
                        for letter in ALPHABET:
                                x_coord, y_coord = screenshot_template_match_multiple(itemname_screenshot_grayscale, os.path.join(template_directory, letter + file_suffix))
                                if x_coord != False:
                                        for occurrence in x_coord:
                                                capitals.append(letter)
                        # Template match for 'of' text
                        x_coord, y_coord = screenshot_template_match_multiple(itemname_screenshot_grayscale, os.path.join(template_directory, 'of' + file_suffix))
                        if x_coord != False:
                                for occurrence in x_coord:
                                        capitals.append('of')
                        # Assess whether we've hit our target name
                        if capitals == []:
                                end_of_items = True
                                break # We've run out of items to consider
                        nontarget_match = False
                        if len(capitals) != len(target_capitals):
                                nontarget_match = True
                        else:
                                for capital in capitals:
                                        if capitals.count(capital) != target_capitals.count(capital):
                                                nontarget_match = True
                                                break
                        if nontarget_match == False:
                                matched_index = i
                                break
                # Exit condition
                if matched_index != None or end_of_items == True:
                        break
                # We've checked all items on the screen and failed to trigger the exit condition; scroll down the item list
                mouseMove([0, 0]) # Get the mouse out of the way for screenshotting
                pre_scroll_screenshot = take_screenshot()
                mouseMove([int(item_search_x_coord+int(ITEM_NAMES_X_OFFSET / (1920 / monitor.width))), int(item_search_y_coord+int(ITEM_NAMES_Y_OFFSET / (1080 / monitor.height)))]) # Move the mouse into the item section to input scrolls
                for x in range(ITEMS_PER_SCREEN):
                        mouseScroll(1, 'down')
                        time.sleep(0.1)
                mouseMove([0, 0])
                post_scroll_screenshot = take_screenshot()     
                if not np.isin(False, pre_scroll_screenshot == post_scroll_screenshot):
                        end_of_items = True
                        break
        return matched_index

## Mouse and keyboard automation functions
def mouseMove(coord):
        '''We use ctypes instead of pyautogui since ctypes supports moving the
        mouse across multiple monitors.'''
        ctypes.windll.user32.SetCursorPos(coord[0], coord[1])

def validateMouse(coord, button, clicks, interval, duration):
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
        # Validate that interval specified is sensible
        if interval == None:
                interval = 0.0
        elif not type(interval) == float:
                raise Exception((
                                'Interval value "{}" is not float.'.format(interval)))
        # Validate that duration specified is sensible
        if duration == None:
                duration = 0.0
        elif not type(duration) == float:
                raise Exception((
                                'Duration value "{}" is not float.'.format(duration)))
        # Return validated values
        return coord, button, clicks, interval, duration

def mousePress(coord, button, clicks, interval, duration):  # all values can be None for defaults
        coord, button, clicks, interval, duration = validateMouse(coord, button, clicks, interval, duration)
        if coord != None:
                mouseMove(coord)
        pyautogui.click(button=button, clicks=clicks, interval=interval, duration=duration)

def validateKeyboard(keys, presses, interval):
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
        # Ensure that interval is sensible
        if interval == None:
                interval = 0.0
        elif not type(interval) == float:
                raise Exception((
                                'Interval value "{}" is not float.'.format(interval)))
        return keys, presses, interval

def keyboardPressSequential(keys, presses, interval):  # keys is expected to be a list, rest can be None for defaults
        keys, presses, interval = validateKeyboard(keys, presses, interval)
        pyautogui.press(keys, presses=presses, interval=interval)

def keyboardPressHotkey(keys):  # keys is expected to be a list
        keys, presses, interval = validateKeyboard(keys, None, None)
        for key in keys:
                pyautogui.keyDown(key)
        for key in reversed(keys):
                pyautogui.keyUp(key)

def keyboardType(message, interval):
        # Ensure that interval is sensible
        if interval == None:
                interval = 0.0
        elif not type(interval) == float:
                raise Exception((
                                'Interval value "{}" is not float.'.format(interval)))
        pyautogui.typewrite(message, interval=interval)

def mouseScroll(units, direction):
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
        mouse.wheel(units)

# Main call
def main():
        # Hard-coded declarations of relevant file locations
        '''It will be ideal to somehow store this in a semi-permanent way within
        the code; need to learn how to do that first!
        '''
        template_directory = r'C:\Bioinformatics\GitHub\personal_projects\FFXIV_related\template_images\mb_price_tabulate'
        # Hard-coded declaration of 1080p template offset values
        ITEM_SEARCH_X_OFFSET = 100
        ITEM_SEARCH_Y_OFFSET = 70
        ITEM_CLICK_X_OFFSET = 365
        ITEM_CLICK_Y_OFFSET = 75
        SEARCHRESULT_TO_HITS_X_OFFSET = 585
        SEARCHRESULT_TO_HITS_Y_OFFSET = 362
        SEARCHRESULT_TO_LISTHQ_X_OFFSET = 0
        SEARCHRESULT_TO_LISTHQ_Y_OFFSET = 110
        SEARCHRESULT_TO_LISTPRICE_X_OFFSET = 100
        SEARCHRESULT_TO_LISTPRICE_Y_OFFSET = 110
        SEARCHRESULT_TO_LISTQTY_X_OFFSET = 200
        SEARCHRESULT_TO_LISTQTY_Y_OFFSET = 110
        SEARCHRESULT_TO_CLOSE_X_OFFSET = 660
        SEARCHRESULT_TO_CLOSE_Y_OFFSET = 10
        TOPRIGHT_OF_SCREEN_X_OFFSET = 1560
        # Hard-coded declaration of screenshot dimensions
        TOPRIGHT_OF_SCREEN_HEIGHT = 60
        HITS_WIDTH = 87 # was 57, can be 87 to get hits text as well
        HITS_HEIGHT = 18
        RESULTS_HEIGHT = 245
        PRICE_WIDTH = 88
        QTY_WIDTH = 57
        HQ_WIDTH = 40
        NAME_HEIGHT = 30
        # Obtain system-specific values
        monitor = screeninfo.get_monitors()[0] # This is our main monitor's dimensions
        # Single monitor mode
        if len(screeninfo.get_monitors()) == 1:
                single_monitor_mode = True
                SINGLE_MONITOR_DELAY = 5
        else:
                single_monitor_mode = False
        # Program start-up
        print('Welcome to the FFXIV Market Board Price Tabulator!')
        while True:
                print('Make your way over to a marketboard and bring up the item search box; configure the "partial match" setting as required for your needs.')
                print('Next, copy a list of items into your clipboard.')
                print('Finally, optionally specify the maximum number of hits to obtain for each item; by default we will capture them all which can be accomplished by simply pressing ENTER.')
                redo_inputs = False
                while True:
                        hits_input=input()
                        if hits_input != '':
                                try:
                                        hits_input = int(hits_input)
                                except:
                                        print('Unrecognised value provided; this should be an integer. Program will continue using default behaviour.')
                        else:
                                hits_input = 99
                        break
                if single_monitor_mode:
                        print('Single monitor mode is active; ' + str(SINGLE_MONITOR_DELAY) + ' second delay will be enacted now to allow for alt tabbing.')
                        time.sleep(SINGLE_MONITOR_DELAY)
                while True:
                        screenshot_grayscale = take_screenshot()
                        item_search_x_coord, item_search_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'mb_top_left.png'))
                        if item_search_x_coord == False:
                                print('Wasn\'t able to locate the marketboard item search box. Make sure it\'s open on your screen and try again by pressing ENTER.')
                                redo_inputs = True
                        break
                while True:
                        text=pyperclip.paste()
                        if text == '':
                                print('Nothing was in your clipboard! Copy your text and try again by pressing ENTER.')
                                redo_inputs = True
                        break
                if redo_inputs == True:
                        print('--RESTART--\n')
                        continue
                print('Alright, sit back and leave your mouse and keyboard alone for a short while.') # End of program start-up
                # Figure out what server the user is on
                while True:
                        servername_screenshot_grayscale = take_screenshot((int(TOPRIGHT_OF_SCREEN_X_OFFSET / (1920 / monitor.width)), 0, abs(int(int(1920-TOPRIGHT_OF_SCREEN_X_OFFSET) / (1920 / monitor.width))), int(TOPRIGHT_OF_SCREEN_HEIGHT / (1080 / monitor.height))))
                        server_name = screenshot_server_automatic_capture(servername_screenshot_grayscale, template_directory, 'server.png')
                        if server_name != False:
                                break
                        else:
                                print('Server name wasn\'t captured properly! Move the screen a bit then I\'ll try again.')
                                time.sleep(5)
                # Prepare clipboard text for iterative query
                item_names = text.rstrip('\r\n').replace('\r', '').split('\n')
                # Main iterative loop: item name query to marketboard
                item_details_dict = {}
                for item in item_names:
                        # Search item name
                        mousePress([int(item_search_x_coord+int(ITEM_SEARCH_X_OFFSET / (1920 / monitor.width))), int(item_search_y_coord+int(ITEM_SEARCH_Y_OFFSET / (1920 / monitor.width)))], 'left', 1, 0.0, 0.5)
                        keyboardPressHotkey(['ctrl', 'a'])
                        keyboardPressSequential(['backspace'], None, None)
                        keyboardType(item, None)
                        time.sleep(0.5) # Can be necessary for long names if stuff lags
                        keyboardPressSequential(['enter'], None, None)
                        time.sleep(1)
                        # Figure out if we have no results
                        wait_for_slow_response(os.path.join(template_directory, 'still_loading_blank.png'))
                        match_screenshot_grayscale = take_screenshot()
                        match_x_coord, match_y_coord = screenshot_template_match_topleftcoords(match_screenshot_grayscale, os.path.join(template_directory, 'nomatch.png'))
                        if match_x_coord != False:
                                print('There is no match for "' + item + '"... fix your inputs; program will ignore and continue.')
                                continue
                        # If we have multiple results, find the correct one
                        match_x_coord, match_y_coord = screenshot_template_match_topleftcoords(match_screenshot_grayscale, os.path.join(template_directory, '1matchonly_blank.png'))
                        if match_x_coord == False:
                                item_index = find_correct_item_from_mb(item, item_search_x_coord, item_search_y_coord, template_directory, '.png')
                                if item_index == None:
                                        print('Could not locate "' + item + '" for some reason... program will ignore and continue.')
                                        continue
                        else:
                                item_index = 0
                        # Click item
                        while True:
                                mousePress([int(item_search_x_coord+int(ITEM_CLICK_X_OFFSET / (1920 / monitor.width))), int(item_search_y_coord+int(ITEM_CLICK_Y_OFFSET / (1920 / monitor.width))+int((abs(int(NAME_HEIGHT / (1080 / monitor.height))))*item_index))], 'left', 2, 0.5, 0.5) ## TESTING
                                time.sleep(1)
                                # Detect "Please wait and try..." statements
                                wait_for_slow_response(os.path.join(template_directory, 'item_search_loading_blank.png'))
                                screenshot_grayscale = take_screenshot()
                                result_x_coord, result_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'result_top_left.png'))
                                wait_x_coord, wait_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'please_wait.png'))
                                if wait_x_coord != False:
                                        mousePress([int(result_x_coord+int(SEARCHRESULT_TO_CLOSE_X_OFFSET / (1920 / monitor.width))), int(result_y_coord+int(SEARCHRESULT_TO_CLOSE_Y_OFFSET / (1920 / monitor.width)))], 'left', 2, 0.5, 0.5)
                                        continue
                                break
                        # Search results box anchor point [most of the below screenshotting uses this as an "anchor" to project x and y direction from]
                        screenshot_grayscale = take_screenshot()
                        hit_x_coord, hit_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'result_top_left.png'))
                        # Detect the number of hits  
                        hit_screenshot_grayscale = take_screenshot((hit_x_coord+int(SEARCHRESULT_TO_HITS_X_OFFSET / (1920 / monitor.width)), hit_y_coord+int(SEARCHRESULT_TO_HITS_Y_OFFSET / (1080 / monitor.height)), abs(int(HITS_WIDTH / (1920 / monitor.width))), int(HITS_HEIGHT / (1080 / monitor.height))))                
                        hits = screenshot_number_automatic_capture(hit_screenshot_grayscale, template_directory, 'glow.png', 0.935)
                        if hits == False:
                                print('Hit number detection failed... Not sure what to do but continue.')
                                continue
                        hits = int(hits)
                        if hits == 0:
                                mousePress([int(result_x_coord+int(SEARCHRESULT_TO_CLOSE_X_OFFSET / (1920 / monitor.width))), int(result_y_coord+int(SEARCHRESULT_TO_CLOSE_Y_OFFSET / (1920 / monitor.width)))], 'left', 2, 0.5, 0.5)
                                continue
                        remaining_hits = hits
                        # Change hits value if a maximum was enforced
                        if hits > hits_input:
                                hits = hits_input
                                remaining_hits = hits
                        # Chop the current screen into sections for each item
                        for screen_num in range(((hits + 9) // 10)): # This rounds up to nearest 10/10(==1) which will correspond to the number of screens for us to scroll through
                                for i in range(10):
                                        if remaining_hits == 0:
                                                break
                                        # Skip redundant hits
                                        if screen_num != 0 and screen_num == ((hits + 9) // 10) - 1: # i.e., if it's not the first screen and it is the last screen
                                                if remaining_hits < 10:
                                                        if i < (10 - remaining_hits):
                                                                continue
                                        ## Qty Section
                                        qty_screenshot_grayscale = take_screenshot((hit_x_coord+int(SEARCHRESULT_TO_LISTQTY_X_OFFSET / (1920 / monitor.width)), hit_y_coord+int(SEARCHRESULT_TO_LISTQTY_Y_OFFSET / (1080 / monitor.height))+int((abs(int(RESULTS_HEIGHT / (1080 / monitor.height)))/10)*i), abs(int(QTY_WIDTH / (1920 / monitor.width))), int(int(RESULTS_HEIGHT / (1080 / monitor.height))/10)))
                                        qty = screenshot_number_automatic_capture(qty_screenshot_grayscale, template_directory, 'qty.png')
                                        if qty == '':
                                                print('Item quantity could not be derived properly; will skip and continue.')
                                                remaining_hits -= 1
                                                continue
                                        ## Price Section
                                        price_screenshot_grayscale = take_screenshot((hit_x_coord+int(SEARCHRESULT_TO_LISTPRICE_X_OFFSET / (1920 / monitor.width)), hit_y_coord+int(SEARCHRESULT_TO_LISTPRICE_Y_OFFSET / (1080 / monitor.height))+int((abs(int(RESULTS_HEIGHT / (1080 / monitor.height)))/10)*i), abs(int(PRICE_WIDTH / (1920 / monitor.width))), int(int(RESULTS_HEIGHT / (1080 / monitor.height))/10)))
                                        price = screenshot_number_automatic_capture(price_screenshot_grayscale, template_directory, 'gil.png')
                                        if price == False:
                                                print('Item price could not be derived properly; will skip and continue.')
                                                remaining_hits -= 1
                                                continue
                                        ## HQ Section
                                        hq_screenshot_grayscale = take_screenshot((hit_x_coord+int(SEARCHRESULT_TO_LISTHQ_X_OFFSET / (1920 / monitor.width)), hit_y_coord+int(SEARCHRESULT_TO_LISTHQ_Y_OFFSET / (1080 / monitor.height))+int((abs(int(RESULTS_HEIGHT / (1080 / monitor.height)))/10)*i), abs(int(HQ_WIDTH / (1920 / monitor.width))), int(int(RESULTS_HEIGHT / (1080 / monitor.height))/10)))
                                        hq_x_coord, hq_y_coord = screenshot_template_match_topleftcoords(hq_screenshot_grayscale, os.path.join(template_directory, 'hq_symbol.png'))
                                        if hq_x_coord != False:
                                                item_quality = 'HQ'
                                        else:
                                                item_quality = 'NQ'
                                        # Store details in dict
                                        if item not in item_details_dict:
                                                item_details_dict[item] = [[price, qty, item_quality]]
                                        else:
                                                item_details_dict[item].append([price, qty, item_quality])
                                        # Update loop condition to track when we've finished checking all the items
                                        remaining_hits -= 1
                                # Scroll down 10 units to next screen if relevant
                                if remaining_hits >= 1:
                                        mouseMove([int(result_x_coord+int((SEARCHRESULT_TO_LISTPRICE_X_OFFSET+10) / (1080 / monitor.height))), int(result_y_coord+int((SEARCHRESULT_TO_LISTPRICE_Y_OFFSET+10) / (1080 / monitor.height)))]) # +10 to give a little extra push
                                        for x in range(10):
                                                mouseScroll(1, 'down')
                                                time.sleep(0.1)
                                        mouseMove([int(result_x_coord), int(result_y_coord)]) # Need to move it again to make sure we don't obscure text with the popup item info
                                        time.sleep(0.5) # Prevent issues with the item info window not instantly disappearing
                        # Close item screen
                        mousePress([int(result_x_coord+int(SEARCHRESULT_TO_CLOSE_X_OFFSET / (1920 / monitor.width))), int(result_y_coord+int(SEARCHRESULT_TO_CLOSE_Y_OFFSET / (1920 / monitor.width)))], 'left', 2, 0.5, 0.5)
                        
                # Store result in clipboard paste-friendly format
                output_text = server_name + '\nItem_name\tPrice\tQuantity\tTotal\tQuality\n'
                for k, v in item_details_dict.items():
                        output_text += k
                        for item_details in v:
                                total = int(item_details[0]) * int(item_details[1])
                                quality = ''
                                if item_details[2] == 'HQ':
                                        quality = '*'
                                output_text += '\t' + '\t'.join([item_details[0], item_details[1], str(total), quality]) + '\n'
                pyperclip.copy(output_text)
                print('Alright, all done! I\'ve stored the result in your clipboard for pasting into an Excel document or something like that.\n')
        
if __name__ == '__main__':
        main()

## TO FIX: the (1910 / monitor.width) etc., sections are flawed; y should always be height, x is width
