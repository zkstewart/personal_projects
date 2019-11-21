#! python3
# ffxiv_mb_price_tabulate.py
# TBD: Script introduction

'''
LIST OF REQUIREMENTS:
1) Introduce the user to the program's requirements
2) Recognise when the marketboard is opened
3) Detect the server that the user is on
        3.1) Detect if it is the home server
4) Retrieve a list of items from clipboard
5) Iteratively enter the item name into the search box
6) Detect nil matches and multiple matches -> skip
7) Click on the match
        7.1) Detect if no items found
        7.2) Detect "Please wait and try your search again" -> reclick
8) Screenshot board
        8.1) Detect the number of hits
                8.1.1) If <=10, capture all details and continue
                8.1.2) If >10, scroll down in lots of 10 scrollwheel units or until last hit is reached and capture all details, continue
9) Concatenate screenshot images into a single board
# TBD from here
'''

# Import modules
import pyperclip, pytesseract, cv2, screeninfo, os, ctypes, pyautogui, time
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
        screenshot_image = mss().grab(grab_coords)
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

def extrapolate_from_topleftcoords(x_coord, y_coord, x_offset, y_offset):
        # Extrapolate the coordinates of the region which will contain item names
        '''Some attempt is made to scale this extrapolation to the user's
        monitor size; testing was performed on a standard 1080p monitor'''
        monitor = screeninfo.get_monitors()[0]
        x_topleft = int(x_coord + (x_offset / (1920 / monitor.width)))
        y_topleft = int(y_coord + (y_offset / (1080 / monitor.height)))
        return x_topleft, y_topleft

def temp_file_prefix_gen(prefix, suffix):
        ongoingCount = 1
        while True:
                if not os.path.isfile(prefix + suffix):
                        return prefix + suffix
                elif os.path.isfile(prefix + str(ongoingCount) + suffix):
                        ongoingCount += 1
                else:
                        return prefix + str(ongoingCount) + suffix

def screenshot_preprocess_for_ocr(screenshot_grayscale, screenshot_width, screenshot_height, monitor_object, RESIZE_RATIO, temp_dir):
        '''monitor_object relates to the object generated by e.g., screeninfo.get_monitors()[0]'''
        temp_filename = temp_file_prefix_gen(os.path.join(temp_dir, 'temp'), '.png')
        cv2.imwrite(temp_filename, screenshot_grayscale)
        screenshot_temp_image = Image.open(temp_filename)
        resized_screenshot_image = screenshot_temp_image.resize((int(screenshot_width * RESIZE_RATIO), int(screenshot_height * RESIZE_RATIO)), Image.ANTIALIAS)
        resized_screenshot_image.save(temp_filename, 'PNG')
        return temp_filename

def cv2_tesseract_OCR_glowingtext(image_file):
        image = cv2.imread(image_file)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)[1]
        # Produce temporary file
        filename = temp_file_prefix_gen(os.path.join(os.path.dirname(image_file), 'temp'), '.png')
        cv2.imwrite(filename, gray)
        # OCR of preprocessed image file
        ocr_text = pytesseract.image_to_string(Image.open(filename))
        # Delete temporary file & return
        os.unlink(filename)
        return ocr_text

def cv2_tesseract_OCR(image_file):
        '''Some code borrowed from 
        https://github.com/AnirudhMergu/TesseractOCR/blob/master/ocr_main.py
        '''
        # Load and preprocess image
        image = cv2.imread(image_file)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        # Produce temporary file
        filename = temp_file_prefix_gen(os.path.join(os.path.dirname(image_file), 'temp'), '.png')
        cv2.imwrite(filename, gray)
        # OCR of preprocessed image file
        ocr_text = pytesseract.image_to_string(Image.open(filename))
        # Delete temporary file & return
        os.unlink(filename)
        return ocr_text

def OCR_text_cleanup(ocr_text, step):
        # General cleanup
        while '\n\n' in ocr_text:
                ocr_text = ocr_text.replace('\n\n', '\n')
        # Step-specific cleanup
        if step == 'servername':
                KNOWN_SERVERS = ['adamantoise', 'cactaur', 'faerie', 'gilgamesh', 'jenova', 'midgardsormr', 'sargatanas', 'siren']
                for sname in KNOWN_SERVERS:
                        if sname in ocr_text.lower():
                                ocr_text = sname.lower()
        if step == 'hitsnumber':
                split_text = ocr_text.split(' ')
                if len(split_text) == 2 and split_text[1] == 'hits':
                        ocr_text = split_text[0]
                #else:
                #        print('Hits text not identifiable; can\'t scroll through list properly.')
                #        ocr_text = '1' # This is just a way to provide a signal to not bother scrolling
        return ocr_text

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
        pyautogui.scroll(units)

# Main call
def main():
        # Hard-coded declarations of relevant file locations
        '''It will be ideal to somehow store this in a semi-permanent way within
        the code; need to learn how to do that first!
        '''
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        template_directory = r'D:\Libraries\Documents\GitHub\personal_projects\FFXIV_related\template_images\mb_price_tabulate'
        temp_dir = r'D:\Libraries\Documents\GitHub\personal_projects\FFXIV_related\development_assistants\tmp_dir'
        # Hard-coded declaration of 1080p template offset values
        ITEM_SEARCH_X_OFFSET = 100
        ITEM_SEARCH_Y_OFFSET = 70
        SERVERTIME_TO_CONNECTSYM_X_OFFSET = -25
        SERVERTIME_TO_CONNECTSYM_Y_OFFSET = -7
        CONNECTSYM_X_OFFSET = -145
        CONNECTSYM_Y_OFFSET = 30
        ITEM_CLICK_X_OFFSET = 365
        ITEM_CLICK_Y_OFFSET = 75
        SEARCHITEM_TO_MATCH_X_OFFSET = 350
        SEARCHITEM_TO_MATCH_Y_OFFSET = 60
        SEARCHRESULT_TO_HITS_X_OFFSET = 585
        SEARCHRESULT_TO_HITS_Y_OFFSET = 362
        SEARCHRESULT_TO_LIST_X_OFFSET = 0
        SEARCHRESULT_TO_LIST_Y_OFFSET = 110
        SEARCHRESULT_TO_CLOSE_X_OFFSET = 660
        SEARCHRESULT_TO_CLOSE_Y_OFFSET = 10
        # Hard-coded declaration of screenshot dimensions
        SERVERNAME_WIDTH = abs(SERVERTIME_TO_CONNECTSYM_X_OFFSET + CONNECTSYM_X_OFFSET)
        SERVERNAME_HEIGHT = CONNECTSYM_Y_OFFSET
        MATCH_WIDTH = 345
        MATCH_HEIGHT = 501
        HITS_WIDTH = 87 # was 57, can be 87 to get hits text as well
        HITS_HEIGHT = 15
        RESULTS_WIDTH = 650
        RESULTS_HEIGHT = 245
        # Hard-coded declaration of program innate parameters
        RESIZE_RATIO = 8
        # Obtain system-specific values
        monitor = screeninfo.get_monitors()[0] # This is our main monitor's dimensions
        
        # Program start-up
        ## REQUIREMENT 1
        print('Welcome to the FFXIV Market Board Price Tabulator!')
        print('Make your way over to a marketboard and bring up the item search box; configure the "partial match" setting as required for your needs.')
        print('Press ENTER in this dialog box when this has been done.')
        while True:
                ## REQUIREMENT 2
                button=input()
                screenshot_grayscale = take_screenshot()
                item_search_x_coord, item_search_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'mb_top_left.png'))
                if item_search_x_coord == False:
                        print('Wasn\'t able to locate the marketboard item search box. Make sure it\'s open on your screen and try again by pressing ENTER.')
                        continue
                break
        print('Next, copy a list of items into your clipboard and then press ENTER.')
        while True:
                ## REQUIREMENT 4
                button=input()
                text=pyperclip.paste()
                if text == '':
                        print('Nothing was in your clipboard! Copy your text and try again by pressing ENTER.')
                        continue
                break
        print('Alright, sit back and leave your mouse and keyboard alone for a short while.') # End of program start-up
        # Figure out what server the user is on
        ## REQUIREMENT 3 [3.1 unmet]
        servertime_x_coord, servertime_search_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'time_corner1.png'))
        if servertime_x_coord == False:
                servertime_x_coord, servertime_search_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'time_corner2.png'))
                if servertime_x_coord == False:
                        servertime_x_coord, servertime_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'time_corner3.png'))
        
        servername_screenshot_grayscale = take_screenshot((servertime_x_coord-int(SERVERNAME_WIDTH / (1920 / monitor.width)), servertime_y_coord+int(SERVERTIME_TO_CONNECTSYM_Y_OFFSET / (1920 / monitor.width)), abs(int(SERVERNAME_WIDTH / (1920 / monitor.width))), int(SERVERNAME_HEIGHT / (1080 / monitor.height))))
        resized_servername_screenshot = screenshot_preprocess_for_ocr(servername_screenshot_grayscale, SERVERNAME_WIDTH, SERVERNAME_HEIGHT, monitor, RESIZE_RATIO, temp_dir)
        servername_text = cv2_tesseract_OCR(resized_servername_screenshot)
        servername_text = OCR_text_cleanup(servername_text, 'servername')
        # Prepare clipboard text for iterative query
        ## REQUIREMENT 4
        item_names = text.rstrip('\r\n').replace('\r', '').split('\n')
        # Main iterative loop: item name query to marketboard
        for item in item_names:
                # Search item name
                ## REQUIREMENT 5
                mousePress([int(item_search_x_coord+int(ITEM_SEARCH_X_OFFSET / (1920 / monitor.width))), int(item_search_y_coord+int(ITEM_SEARCH_Y_OFFSET / (1920 / monitor.width)))], 'left', 1, 0.0, 0.5)
                keyboardPressHotkey(['ctrl', 'a'])
                keyboardPressSequential(['backspace'], None, None)
                keyboardType(item, None)
                time.sleep(0.2) # Can be necessary for long names if stuff lags
                keyboardPressSequential(['enter'], None, None)
                # Figure out if we have no or multiple results; either is problematic
                match_screenshot_grayscale = take_screenshot((item_search_x_coord+int(SEARCHITEM_TO_MATCH_X_OFFSET / (1920 / monitor.width)), item_search_y_coord+int(SEARCHITEM_TO_MATCH_Y_OFFSET / (1920 / monitor.width)), abs(int(MATCH_WIDTH / (1920 / monitor.width))), int(MATCH_HEIGHT / (1080 / monitor.height))))
                resized_match_screenshot = screenshot_preprocess_for_ocr(match_screenshot_grayscale, int(MATCH_WIDTH / (1920 / monitor.width)), int(MATCH_HEIGHT / (1920 / monitor.width)), monitor, 20, temp_dir)
                match_text = cv2_tesseract_OCR(resized_match_screenshot)
                match_text = OCR_text_cleanup(match_text, 'match')
                matches = match_text.split('\n')
                ### REQUIREMENT 6
                if len(matches) > 1 or len(matches) == 0 or matches[0].lower().startswith('no matching items'):
                        print('There is not a single unique match for "' + item + '"... fix your inputs; program will ignore and continue.')
                        continue
                time.sleep(2) # As before, lag
                # Click item
                ### REQUIREMENT 7
                while True:
                        mousePress([int(item_search_x_coord+int(ITEM_CLICK_X_OFFSET / (1920 / monitor.width))), int(item_search_y_coord+int(ITEM_CLICK_Y_OFFSET / (1920 / monitor.width)))], 'left', 2, 0.5, 0.5)
                        time.sleep(2)
                        # Detect "Please wait and try..." statements
                        ### REQUIREMENT 7.2
                        screenshot_grayscale = take_screenshot()
                        result_x_coord, result_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'result_top_left.png'))
                        wait_x_coord, wait_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'please_wait.png'))
                        if wait_x_coord != False:
                                mousePress([int(result_x_coord+int(SEARCHRESULT_TO_CLOSE_X_OFFSET / (1920 / monitor.width))), int(result_y_coord+int(SEARCHRESULT_TO_CLOSE_Y_OFFSET / (1920 / monitor.width)))], 'left', 2, 0.5, 0.5)
                                continue
                        break
                # Detect the number of hits
                screenshot_grayscale = take_screenshot()
                hit_x_coord, hit_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'result_top_left.png'))
                hit_screenshot_grayscale = take_screenshot((hit_x_coord+int(SEARCHRESULT_TO_HITS_X_OFFSET / (1920 / monitor.width)), hit_y_coord+int(SEARCHRESULT_TO_HITS_Y_OFFSET / (1920 / monitor.width)), abs(int(HITS_WIDTH / (1920 / monitor.width))), int(HITS_HEIGHT / (1080 / monitor.height))))                
                for i in range(5, 20):
                        resized_hit_screenshot = screenshot_preprocess_for_ocr(hit_screenshot_grayscale, int(HITS_WIDTH / (1920 / monitor.width)), int(HITS_HEIGHT / (1920 / monitor.width)), monitor, 10, temp_dir)
                        hit_text = cv2_tesseract_OCR_glowingtext(resized_hit_screenshot)
                        hit_text = OCR_text_cleanup(hit_text, 'hitsnumber')
                        if hit_text.isdigit():
                                break
                if hit_text == '0':
                        print('"' + item + '" has no listings on ' + servername_text)
                        continue
                # Chop the current screen into 10 lines for each item
                
                ## TBD: Chop screenshot line-by-line and derive HQ/NQ, price/unit, and number of units
                #result_text = cv2_tesseract_OCR_glowingtext(resized_result_screenshot)
                
if __name__ == '__main__':
        #main()
        pass
