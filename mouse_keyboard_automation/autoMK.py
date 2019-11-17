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
import pyautogui, pygetwindow, keyboard, mouse, queue, ctypes, screeninfo, time, pickle, tkinter

# Hard-coded parameter setup
pyautogui.PAUSE = 1  # this will enforce a static 1sec wait between each action ## Find better way to handle this later
pyautogui.FAILSAFE = True  # during waits, move mouse to top left corner to end

# Define functions
## KEYLOGGER-RELATED
def startKeyLogger():
        q = queue.Queue()
        keyboard.start_recording(q)
        return q

def readKeyLogger(q):  # this function just listifies q "as-is" in the same format as how 'keyboard' returns its queue.Queue value
        q2 = list(q.queue)
        return q2

def stopKeyLogger():
        q = keyboard.stop_recording()
        return q

def keyLoggerToString(q, skipSpecial):  # q should be a queue.Queue object from 'keyboard' module
        # Verify that skipSpecial value is sensible
        if not type(skipSpecial) == bool:
                raise Exception((
                                'skipSpecial value provided to keyLoggerToString '
                                ' is not boolean. Fix required at the code level.'
                                ' i.e., tell Zac something is wrong.'))
        specialKeys = ['shift', 'caps lock', 'esc', 'left windows', 'alt', 'ctrl',
                       'right alt', 'right ctrl', 'insert', 'delete', 'home', 'end',
                       'page up', 'page down', 'up', 'down', 'left', 'right', 'f1',
                       'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11',
                       'f12', 'print screen', 'scroll lock', 'pause', 'num lock']
        s = ''
        for k in q:  # q contains individual key values ('k') which contain methods from 'keyboard'
                # Handle special keys and events
                if k.event_type == 'up':  # key 'up' events don't inform us what value is actually typed
                        continue
                elif skipSpecial == True and k.name in specialKeys:
                        continue
                elif skipSpecial == False and k.name in specialKeys:
                        s += '_' + k.name.upper() + '_'
                elif k.name == 'space':
                        s += ' '
                elif k.name == 'enter':
                        s += '\n'
                elif k.name == 'tab':
                        s += '\t'
                elif k.name == 'backspace':
                        s = s[:-1]
                # Record other keys to string value
                else:
                        s += k.name
        return s

## PYAUTOGUI-RELATED
def validateCoord(coord):
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

def validateWindow(windowTitle):
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

def mouseFullTrack():
        # Tell user how to end this function
        print('Press middle mouse button to end tracking and save this set of actions to file.')
        # Record mouse events and return list object
        mq = mouse.record(button='middle')
        return mq

def keyboardFullTrack():
        # Tell user how to end this function
        print('Press middle mouse button to end tracking and save this set of actions to file.')
        # Record keyboard events and return list object
        kq = keyboard.record(until='escape')
        return kq
        
def mouseCoordTrack():
        # Tell user how to end this function
        print('Press CTRL+C to stop mouse coordinate tracking function.')
        print('Press Esc to pause and resume coordinate tracking.')
        # Enact main loop
        paused = False
        while True:
                try:
                        q = startKeyLogger()
                        x, y = pyautogui.position()
                        if paused == False:
                                print('X: ' + str(x).rjust(4) + ' Y: ' + str(y).rjust(4), end = '\r')
                        # Detect space key presses for pausing/resuming tracking function
                        q = stopKeyLogger()
                        s = keyLoggerToString(q, False)
                        if '_ESC_' in s:
                                if paused == False:
                                        paused = True
                                else:
                                        paused = False
                except KeyboardInterrupt:
                        print('')
                        print('Mouse coordinate tracking stop.')
                        break
                except:
                        print('')
                        print('Unknown error; mouse coordinate tracking will resume.')

def mouseScrollTrack():
        '''Function should enable the user to test the amount of scroll units
        they want to perform in a way that is relatively easy to figure out.'''
        # Tell user how to end this function
        print('Press CTRL+C to stop mouse scroll testing function.')
        print('Press Esc to perform a mouse scroll at the provided amount of units.')
        print('Press Down arrow to type in a new amount of units for testing.')
        print('Positive numbers scroll up, negative numbers scroll down.')
        # Enact main loop
        paused = False
        units = None
        while True:
                try:
                        if units == None or paused == True:
                                print('Type the amount of units to scroll below.')
                                while True:
                                        units = input()
                                        try:
                                                units = int(units)
                                                paused = False
                                                print('Scroll units: {}'.format(units))
                                                break
                                        except:
                                                print('Provided value is not int, try again.')
                        # Detect key presses for pausing/resuming/exiting
                        q = startKeyLogger()
                        time.sleep(0.5)
                        q = stopKeyLogger()
                        s = keyLoggerToString(q, False)
                        if '_ESC_' in s:
                                pyautogui.scroll(units)
                        elif '_DOWN_' in s:
                                paused = True
                except KeyboardInterrupt:
                        print('')
                        print('Scroll unit testing stop.')
                        break
                except:
                        print('')
                        print('Unknown error; scroll unit testing will resume.')

def mouseMove(coord):
        '''We use ctypes instead of pyautogui since ctypes supports moving the
        mouse across multiple monitors.'''
        ctypes.windll.user32.SetCursorPos(coord[0], coord[1])

def mousePress(coord, button, clicks, interval, duration):  # all values can be None for defaults
        coord, button, clicks, interval, duration = validateMouse(coord, button, clicks, interval, duration)
        if coord != None:
                mouseMove(coord)
        pyautogui.click(button=button, clicks=clicks, interval=interval, duration=duration)

def mouseDown(button):
        coord, button, clicks, interval, duration = validateMouse(None, button, None, None, None)
        pyautogui.mouseDown(button=button)

def mouseUp(button):
        coord, button, clicks, interval, duration = validateMouse(None, button, None, None, None)
        pyautogui.mouseUp(button=button)

def mouseDrag(coord1, coord2, button, duration):  # coords cannot be None
        if coord1 == None or coord2 == None:
                raise Exception((
                                'Coord1 and/or coord2 value i.e., "{} / {}" is None'
                                ' Coordinates must be specified for dragging'
                                ' behaviour'.format(button)))
        coord1, button, clicks, interval, duration = validateMouse(coord1, button, None, None, duration)
        coord2, button, clicks, interval, duration = validateMouse(coord2, button, None, None, duration)
        #pyautogui.dragTo(coord2[0], coord2[1], button=button, duration=duration) ## bugged on second monitor
        mouseMove(coord1)
        mouseDown(button)
        mouseMove(coord2)
        mouseUp(button)

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

def keyboardType(message, interval):
        # Ensure that interval is sensible
        if interval == None:
                interval = 0.0
        elif not type(interval) == float:
                raise Exception((
                                'Interval value "{}" is not float.'.format(interval)))
        pyautogui.typewrite(message, interval=interval)

def keyboardPress(keys, presses, interval):  # keys is expected to be a list, rest can be None for defaults
        keys, presses, interval = validateKeyboard(keys, presses, interval)
        pyautogui.press(keys, presses=presses, interval=interval)

def keyboardUp(keys):
        keys, presses, interval = validateKeyboard(keys, None, None)
        for key in keys:
                pyautogui.keyUp(keys)

def keyboardDown(keys):
        keys, presses, interval = validateKeyboard(keys, None, None)
        for key in keys:
                pyautogui.keyDown(keys)

def windowHandle():
        asdf

def main():
        print('ayy lmao')
        '''TBD;
        1) Produce a menu screen that allows the user to call specific functions
        2) Produce a config file syntax that allows users to provide simple instructions for mouse/keyboard automation that can be decoded appropriately
        +3) Produce a pyautogui function that can automate all kinds of mouse and keyboard actions
        4) Helper function to print currently available windows
        '''
        mouseCoordTrack()
        #mouseScrollTrack()

if __name__ == '__main__':
        main()