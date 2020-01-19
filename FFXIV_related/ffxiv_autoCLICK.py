#! python3
# ffxiv_autoCLICK.py
# Program that automates the process of crafting multiple items via clicking
# macro boxes in specified locations.
'''
'''

# Import modules
import os, pyautogui, keyboard, queue, ctypes, screeninfo, time, sys, random, cv2, argparse, textwrap
from PIL import Image
import numpy as np
from mss import mss

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
        return time + random.uniform(0, 0.2)

def mouse_press(button):
        if button.lower() not in ['left', 'right', 'middle']:
                print('mouse_press: button not recognised; coding error')
                quit()
        mouse_down(button.lower())
        sleepTime=variableTime(0.10)
        time.sleep(sleepTime)
        mouse_up(button.lower())

def mouse_click(button, pause=0.20):
        if button.lower() not in ['left', 'right', 'middle']:
                print('mouse_press: button not recognised; coding error')
                quit()
        mouse_down(button.lower(), pause)
        time.sleep(pause)
        mouse_up(button.lower(), pause)

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

# Main pre-programmed automation functions
def craft(skillbar_coords, wait_times, num_iterations, template_directory):
        # Hard-coded values and offsets
        SYNTHESIZE_X_OFFSET = 50
        SYNTHESIZE_Y_OFFSET = 15
        COLLECTIBLE_X_OFFSET = 120
        COLLECTIBLE_Y_OFFSET = 220
        WAIT_TIME = 2
        # Monitor dimensions
        monitor = screeninfo.get_monitors()[0]
        # Sanity check inputs
        assert len(skillbar_coords) == len(wait_times)
        # Run loop
        for i in range(num_iterations):
                for x in range(len(skillbar_coords)):
                        q = start_key_logger()
                        # Click the synthesise button and give character time to set up
                        if x == 0:
                                times_failed = 0
                                while True:
                                        if times_failed == 10:
                                                print('Consistently failed to find synthesise button; program exiting now.')
                                                quit()
                                        screenshot_grayscale = take_screenshot()
                                        synthesize_x_coord, synthesize_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'synthesize_button.png'))
                                        if synthesize_x_coord == False:
                                                print('Synthesize button not visible; waiting ' + str(WAIT_TIME) + ' seconds...')
                                                time.sleep(WAIT_TIME)
                                                times_failed += 1
                                                continue
                                        break
                                mouse_move([int(synthesize_x_coord+int(SYNTHESIZE_X_OFFSET / (1920 / monitor.width))), int(synthesize_y_coord+int(SYNTHESIZE_Y_OFFSET / (1080 / monitor.height)))])
                                mouse_press('left')
                                sleepTime=variableTime(1.5) 
                                time.sleep(sleepTime)
                                q = restart_keylogger_for_specialcommand('CTRL_esc')
                        # Verify that character is set up (this is a latency contingency)
                        times_failed = 0
                        while True:
                                if times_failed == 10:
                                        print('Consistently failed to find crafting window; program exiting now.')
                                        quit()
                                screenshot_grayscale = take_screenshot()
                                craftwindow_x_coord, craftwindow_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'crafting_window_bottom.png'))
                                if craftwindow_x_coord == False:
                                        print('Crafting window button not visible; waiting ' + str(WAIT_TIME) + ' seconds...')
                                        time.sleep(WAIT_TIME)
                                        times_failed += 1
                                        continue
                                break
                        # Click macro button and wait
                        mouse_move(skillbar_coords[x])
                        mouse_press('left')
                        sleepTime=variableTime(wait_times[x])
                        time.sleep(sleepTime)
                        q = restart_keylogger_for_specialcommand('CTRL_esc')
                # Collectible contingency
                screenshot_grayscale = take_screenshot()
                collectwindow_x_coord, collectwindow_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'collectible_screen.png'))
                if collectwindow_x_coord != False:
                        mouse_move([int(collectwindow_x_coord+int(COLLECTIBLE_X_OFFSET / (1920 / monitor.width))), int(collectwindow_y_coord+int(COLLECTIBLE_Y_OFFSET / (1080 / monitor.height)))])
                        mouse_press('left')
                        sleepTime=variableTime(2.0)
                        time.sleep(sleepTime)

def coord_fudger_from_image(x_coord_topleft, y_coord_topleft, image_file):
        image = cv2.imread(image_file, 0)
        height, width = image.shape
        x_coord_random, y_coord_random = coord_randomiser(x_coord_topleft, y_coord_topleft, x_coord_topleft+width, y_coord_topleft+height)
        return [int(x_coord_random), int(y_coord_random)] # This just prevents the mouse_move function from being upset that these values are not the exact type of integer it's expecting (I don't understand it).

def coord_fudger_from_dimensions(x_coord_topleft, y_coord_topleft, width, height):
        x_coord_random, y_coord_random = coord_randomiser(x_coord_topleft, y_coord_topleft, x_coord_topleft+width, y_coord_topleft+height)
        return [int(x_coord_random), int(y_coord_random)] # This just prevents the mouse_move function from being upset that these values are not the exact type of integer it's expecting (I don't understand it).

def coord_randomiser(x_coord_min, y_coord_min, x_coord_max, y_coord_max):
        return random.randrange(x_coord_min, x_coord_max), random.randrange(y_coord_min, y_coord_max)

def collect(template_directory):
        COLLECT_SLEEP_TIME = 2
        YES_SLEEP_TIME = 1
        def button_not_found_error(x_coord, button_name):
                if x_coord == False:
                        print(button_name + ' was not found on your hotbar! Change to botanist or miner now.')
                        return False
                else:
                        return True
        def auto_collect(screenshot_grayscale, collectwindow_x_coord, collectwindow_y_coord, template_directory):
                # Locate collect button
                collect_button_x_coord, collect_button_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'gathering', 'collect_button.png'))
                button_not_found_error(collect_button_x_coord, 'Collect button') # This shouldn't be necessary, but you never know
                # Figure out how much GP we have available
                gp = int(gp_number_find(template_directory))
                # Start rotation
                ## Cast impulsive appraisal
                score = cast_then_sleep('impulsive_appraisal', 0, impulsive_appraisal_x_coord, impulsive_appraisal_y_coord)
                ## Branching point: Respond to discerning eye proc
                proc = discerning_eye_procced(template_directory)
                if proc == True:
                        # Cast 2x instinctual appraisal
                        for i in range(2):
                                # Cast single mind if possible
                                if gp >= 400: # This ensures we hold onto at least 200gp if possible for an utmost caution or discerning eye later
                                        gp -= 200
                                        cast_then_sleep('single_mind', score, single_mind_x_coord, single_mind_y_coord)
                                # Cast instinctual appraisal
                                score = cast_then_sleep('instinctual_appraisal', score, instinctual_appraisal_x_coord, instinctual_appraisal_y_coord)
                        ## Branching point: Respond to collectability
                        top_path_collectability_branch(gp)
                else:
                        # Cast impulsive appraisal
                        score = cast_then_sleep('impulsive_appraisal', score, impulsive_appraisal_x_coord, impulsive_appraisal_y_coord)
                        ## Branching point: Respond to discerning eye proc
                        proc = discerning_eye_procced(template_directory)
                        if proc == True:
                                # Cast single mind if possible
                                if gp >= 400:
                                        gp -= 200
                                        cast_then_sleep('single_mind', score, single_mind_x_coord, single_mind_y_coord)
                                # Cast 1x instinctual appraisal
                                score = cast_then_sleep('instinctual_appraisal', score, instinctual_appraisal_x_coord, instinctual_appraisal_y_coord)
                                ## Branching point: Respond to collectability
                                top_path_collectability_branch(gp)
                        else:
                                # Cast impulsive appraisal
                                score = cast_then_sleep('impulsive_appraisal', score, impulsive_appraisal_x_coord, impulsive_appraisal_y_coord)
                                ## Branching point: Respond to discerning eye proc
                                proc = discerning_eye_procced(template_directory)
                                if proc == True:
                                        middle_branch_final(gp)
                                else:
                                        # Cast utmost caution if possible [This ordering is a bit different to the proper rotation but utmost caution > discerning eye in some cases to prevent gathering nil items when GP is sub 600 to start
                                        if gp >= 200:
                                                gp -= 200
                                                cast_then_sleep('utmost_caution', score, utmost_caution_x_coord, utmost_caution_y_coord)
                                        # Cast discerning eye if possible
                                        if gp >= 200:
                                                gp -= 200
                                                cast_then_sleep('discerning_eye', score, discerning_eye_x_coord, discerning_eye_y_coord)
                                        # Cast single mind if possible
                                        if gp >= 200:
                                                gp -= 200
                                                cast_then_sleep('single_mind', score, single_mind_x_coord, single_mind_y_coord)
                                        # Cast methodical appraisal
                                        score = cast_then_sleep('methodical_appraisal', score, methodical_appraisal_x_coord, methodical_appraisal_y_coord)
                                        # Collect
                                        collect_button_loop()
        def cast_then_sleep(skill_name, collectability, x_coord, y_coord):
                CAST_SLEEP_TIME = 2.0
                BUFF_SLEEP_TIME = 1.0
                NUM_OF_ALLOWED_FAILS = 3
                sleep_fails = 0
                if skill_name in ['utmost_caution', 'single_mind', 'discerning_eye']:
                        while True:
                                if sleep_fails == 0: # This system attempts to allow the program to re-cast skills that were pressed during a lag spike that were not recognised by the game
                                        mouse_move(coord_fudger_from_image(x_coord, y_coord, os.path.join(template_directory, 'gathering', skill_name + '.png')))
                                        mouse_press('left')
                                time.sleep(BUFF_SLEEP_TIME)
                                screenshot_grayscale = take_screenshot()
                                buff_x_coord, buff_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'gathering', skill_name + '_buff.png'))
                                if buff_x_coord == False and sleep_fails < NUM_OF_ALLOWED_FAILS: # Buff should be present when skill is complete
                                        sleep_fails += 1
                                elif buff_x_coord == False and sleep_fails == NUM_OF_ALLOWED_FAILS:
                                        sleep_fails = 0
                                else:
                                        break
                else:
                        while True:
                                if sleep_fails == 0: # This system attempts to allow the program to re-cast skills that were pressed during a lag spike that were not recognised by the game
                                        mouse_move(coord_fudger_from_image(x_coord, y_coord, os.path.join(template_directory, 'gathering', skill_name + '.png')))
                                        mouse_press('left')
                                time.sleep(CAST_SLEEP_TIME)
                                score = int(collect_score_find(template_directory))
                                if int(score) == collectability and sleep_fails < NUM_OF_ALLOWED_FAILS: # Collectability score should increase when skill is complete
                                        sleep_fails += 1
                                        continue
                                elif int(score) == collectability and sleep_fails == NUM_OF_ALLOWED_FAILS:
                                        sleep_fails = 0
                                else:
                                        return score
        def collect_button_loop():
                while True:
                        screenshot_grayscale = take_screenshot()
                        collect_button_x_coord, collect_button_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'gathering', 'collect_button.png'))
                        if collect_button_x_coord == False:
                                break
                        mouse_move(coord_fudger_from_image(collect_button_x_coord, collect_button_y_coord, os.path.join(template_directory, 'gathering', 'collect_button.png')))
                        mouse_press('left')
                        time.sleep(COLLECT_SLEEP_TIME)
                        yes_button_fails = 0
                        while True:
                                screenshot_grayscale = take_screenshot()
                                yes_button_x_coord, yes_button_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'gathering', 'yes_button.png'))
                                if yes_button_x_coord == False:
                                        collectwindow_x_coord, collectwindow_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'gathering', 'wear.png'))
                                        if collectwindow_x_coord == False:
                                                break
                                        else:
                                                time.sleep(YES_SLEEP_TIME)
                                                yes_button_fails += 1
                                                if yes_button_fails == 5:
                                                        break
                                                continue
                                mouse_move(coord_fudger_from_image(yes_button_x_coord, yes_button_y_coord, os.path.join(template_directory, 'gathering', 'yes_button.png')))
                                mouse_press('left')
                                break
        def top_path_collectability_branch(gp):
                score = int(collect_score_find(template_directory))
                if score >= 450:
                        # Collect
                        collect_button_loop()
                elif score > 390:
                        # Cast single mind if possible
                        if gp >= 200:
                                cast_then_sleep('single_mind', score, single_mind_x_coord, single_mind_y_coord)
                        # Cast stickler
                        score = cast_then_sleep('stickler', score, stickler_x_coord, stickler_y_coord)
                        # Collect
                        collect_button_loop()
                else:
                        middle_branch_final(gp)
        def middle_branch_final(gp):
                '''We enter this branch if we're in the top branch and are <390 collectability
                or if we're in the bottom path and hit a discerning eye proc on the last impulsive'''
                score = int(collect_score_find(template_directory))
                # Cast utmost caution if possible
                if gp >= 200:
                        gp -= 200
                        cast_then_sleep('utmost_caution', score, utmost_caution_x_coord, utmost_caution_y_coord)
                # Cast single mind if possible
                if gp >= 200:
                        cast_then_sleep('single_mind', score, single_mind_x_coord, single_mind_y_coord)
                # Cast methodical appraisal
                score = cast_then_sleep('methodical_appraisal', score, methodical_appraisal_x_coord, methodical_appraisal_y_coord)
                # Collect
                collect_button_loop()
        def auto_exchange(exchangewindow_x_coord, exchangewindow_y_coord, template_directory):
                EXCHANGE_TEXT_TO_ROWS_X_OFFSET = 20
                EXCHANGE_TEXT_TO_ROWS_Y_OFFSET = 97
                ITEM_REQUEST_TO_CLICK_TARGET_X_OFFSET = 13
                ITEM_REQUEST_TO_CLICK_TARGET_Y_OFFSET = 43
                CLICK_TARGET_TO_BOX_X_OFFSET = 15
                CLICK_TARGET_TO_BOX_Y_OFFSET = 30
                ITEM_REQUEST_TO_HANDOVER_X_OFFSET = 15
                ITEM_REQUEST_TO_HANDOVER_Y_OFFSET = 105
                ##
                ROWS_WIDTH = 810
                ROWS_HEIGHT = 24
                ITEM_REQUEST_WIDTH = 30
                ITEM_REQUEST_HEIGHT = 30
                BOX_SIDE = 20
                HANDOVER_WIDTH = 90
                HANDOVER_HEIGHT = 10
                ##
                ITEM_REQUEST_SLEEP = 0.2
                END_LOOP_SLEEP = 0.5
                # Monitor dimensions
                monitor = screeninfo.get_monitors()[0]
                # Scan through collectable exchange screen for items to turn in
                while True:
                        screenshot_grayscale = take_screenshot()
                        exchangewindow_x_coord, exchangewindow_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'gathering', 'collectables_exchange.png'))
                        if exchangewindow_x_coord == False:
                                break
                        # Cancel turnins if scrips are full
                        full_scrips_x_coord, full_scrips_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'gathering', 'full_scrips.png'))
                        if full_scrips_x_coord != False:
                                break
                        for i in range(0, 10): # 10 rows are displayed in a screen
                                row_screenshot_grayscale = take_screenshot((exchangewindow_x_coord+int(EXCHANGE_TEXT_TO_ROWS_X_OFFSET / (1920 / monitor.width)), exchangewindow_y_coord+int(EXCHANGE_TEXT_TO_ROWS_Y_OFFSET / (1080 / monitor.height))+int((abs(int(ROWS_HEIGHT / (1080 / monitor.height))))*i), abs(int(ROWS_WIDTH / (1920 / monitor.width))), int(int(ROWS_HEIGHT / (1080 / monitor.height)))))
                                # Check for rows that are not collected
                                noexchange_x_coord, noexchange_y_coord = screenshot_template_match_topleftcoords(row_screenshot_grayscale, os.path.join(template_directory, 'gathering', 'no_exchange.png'), threshold=0.95)
                                if noexchange_x_coord != False:
                                        continue
                                # If row can be turned in, click it
                                mouse_move(coord_fudger_from_dimensions(exchangewindow_x_coord+int(EXCHANGE_TEXT_TO_ROWS_X_OFFSET / (1920 / monitor.width)), exchangewindow_y_coord+int(EXCHANGE_TEXT_TO_ROWS_Y_OFFSET / (1080 / monitor.height))+int((abs(int(ROWS_HEIGHT / (1080 / monitor.height))))*i), abs(int(ROWS_WIDTH / (1920 / monitor.width))), int(int(ROWS_HEIGHT / (1080 / monitor.height)))))
                                mouse_click('left', 0.10)
                                # Wait for item request window to pop up
                                sleep_fails = 0
                                sleep_exit_condition = False
                                while True:
                                        screenshot_grayscale = take_screenshot()
                                        request_x_coord, request_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'gathering', 'item_request.png'))
                                        if request_x_coord != False:
                                                break
                                        sleep_fails += 1
                                        if sleep_fails == 10:
                                                sleep_exit_condition = True
                                                break
                                if sleep_exit_condition == True:
                                        break
                                # Right-click item to bring up turnin screen
                                turnin_coords = coord_fudger_from_dimensions(request_x_coord+int(ITEM_REQUEST_TO_CLICK_TARGET_X_OFFSET / (1920 / monitor.width)), request_y_coord+int(ITEM_REQUEST_TO_CLICK_TARGET_Y_OFFSET / (1080 / monitor.height)), int(ITEM_REQUEST_WIDTH / (1920 / monitor.width)), int(ITEM_REQUEST_HEIGHT / (1080 / monitor.height)))
                                mouse_move(turnin_coords) # We need to use the fudged coords below to derive our offsets
                                mouse_click('right', 0.10)
                                # Left-click item within turnin screen
                                mouse_move([int(turnin_coords[0]+int(CLICK_TARGET_TO_BOX_X_OFFSET / (1920 / monitor.width))), int(turnin_coords[1]+int(CLICK_TARGET_TO_BOX_Y_OFFSET / (1080 / monitor.height)))])
                                mouse_click('left', 0.10)
                                # Left-click hand over button
                                mouse_move([int(request_x_coord+int(ITEM_REQUEST_TO_HANDOVER_X_OFFSET / (1920 / monitor.width))), int(request_y_coord+int(ITEM_REQUEST_TO_HANDOVER_Y_OFFSET / (1080 / monitor.height)))])
                                mouse_click('left', 0.10)
                                # Move mouse out of the way for the next iteration
                                mouse_move(coord_fudger_from_dimensions(0, 0, 10, 10))
                                break # Breaking the loop here means we'll continue to turn in the same item until it runs out
                        # Exit condition
                        if i == 9: # i.e., if we scan through each row and find no rows to turnin
                                break
                                
        # Start up checking for relevant button locations
        while True:
                screenshot_grayscale = take_screenshot()
                discerning_eye_x_coord, discerning_eye_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'gathering', 'discerning_eye.png'))
                impulsive_appraisal_x_coord, impulsive_appraisal_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'gathering', 'impulsive_appraisal.png'))
                instinctual_appraisal_x_coord, instinctual_appraisal_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'gathering', 'instinctual_appraisal.png'))
                methodical_appraisal_x_coord, methodical_appraisal_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'gathering', 'methodical_appraisal.png'))
                single_mind_x_coord, single_mind_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'gathering', 'single_mind.png'))
                stickler_x_coord, stickler_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'gathering', 'stickler.png'))
                utmost_caution_x_coord, utmost_caution_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'gathering', 'utmost_caution.png'))
                # Validate that all buttons were found
                valid_button = button_not_found_error(discerning_eye_x_coord, 'Discerning Eye')
                if valid_button == False:
                        time.sleep(5)
                        continue
                valid_button = button_not_found_error(impulsive_appraisal_x_coord, 'Impulsive Appraisal')
                if valid_button == False:
                        time.sleep(5)
                        continue
                valid_button = button_not_found_error(instinctual_appraisal_x_coord, 'Instinctual Appraisal')
                if valid_button == False:
                        time.sleep(5)
                        continue
                valid_button = button_not_found_error(methodical_appraisal_x_coord, 'Methodical Appraisal')
                if valid_button == False:
                        time.sleep(5)
                        continue
                valid_button = button_not_found_error(single_mind_x_coord, 'Single Mind')
                if valid_button == False:
                        time.sleep(5)
                        continue
                valid_button = button_not_found_error(stickler_x_coord, 'Stickler')
                if valid_button == False:
                        time.sleep(5)
                        continue
                valid_button = button_not_found_error(utmost_caution_x_coord, 'Utmost Caution')
                if valid_button == False:
                        time.sleep(5)
                        continue
                break
        # Main operation loop
        while True:
                # Continual checking for actionable states
                while True:
                        screenshot_grayscale = take_screenshot()
                        # State 1: Collection
                        collectwindow_x_coord, collectwindow_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'gathering', '0_wear.png'))
                        if collectwindow_x_coord != False:
                                auto_collect(screenshot_grayscale, collectwindow_x_coord, collectwindow_y_coord, template_directory)
                        # State 2: Item turnin
                        exchangewindow_x_coord, exchangewindow_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'gathering', 'collectables_exchange.png'))
                        if exchangewindow_x_coord != False:
                                auto_exchange(exchangewindow_x_coord, exchangewindow_y_coord, template_directory)
                        # State 3: Aetherial reduction
                        ## This should involve template matching for the main reduction targets of aethersand in an inventory
                        time.sleep(1.0)

def discerning_eye_procced(template_directory):
        screenshot_grayscale = take_screenshot()
        discerning_eye_buff_x_coord, discerning_eye_buff_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'gathering', 'discerning_eye_buff.png'))
        if discerning_eye_buff_x_coord != False:
                return True
        else:
                return False

def gp_number_find(template_directory):
        GP_EXTRA_Y_HEIGHT = 10
        GP_TO_NUMBER_X_OFFSET = 53
        GP_TO_NUMBER_Y_OFFSET = 15
        GP_WIDTH = 60
        GP_HEIGHT = GP_EXTRA_Y_HEIGHT + GP_TO_NUMBER_Y_OFFSET
        # Monitor dimensions
        monitor = screeninfo.get_monitors()[0]
        # Locate GP text
        screenshot_grayscale = take_screenshot()
        gp_text_x_coord, gp_text_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'gathering', 'gp.png'))
        # Screenshot the GP number
        gp_screenshot_grayscale = take_screenshot((gp_text_x_coord+int(GP_TO_NUMBER_X_OFFSET / (1920 / monitor.width)), gp_text_y_coord-int(GP_EXTRA_Y_HEIGHT / (1080 / monitor.height)), abs(int(GP_WIDTH / (1920 / monitor.width))), int(GP_HEIGHT / (1080 / monitor.height))))
        # Template match to read number and return
        gp = screenshot_number_automatic_capture(gp_screenshot_grayscale, template_directory, '_gp.png')
        return gp

def collect_score_find(template_directory):
        WEAR_TO_SCORE_X_OFFSET = 355
        WEAR_TO_SCORE_Y_OFFSET = 10
        SCORE_WIDTH = 40
        SCORE_HEIGHT = 25
        # Monitor dimensions
        monitor = screeninfo.get_monitors()[0]
        # Locate wear text
        screenshot_grayscale = take_screenshot()
        wear_x_coord, wear_y_coord = screenshot_template_match_topleftcoords(screenshot_grayscale, os.path.join(template_directory, 'gathering', 'wear.png'))
        # Screenshot the score number
        score_screenshot_grayscale = take_screenshot((wear_x_coord+int(WEAR_TO_SCORE_X_OFFSET / (1920 / monitor.width)), wear_y_coord+int(WEAR_TO_SCORE_Y_OFFSET / (1080 / monitor.height)), abs(int(SCORE_WIDTH / (1920 / monitor.width))), int(SCORE_HEIGHT / (1080 / monitor.height))))
        # Template match to read number and return
        score = screenshot_number_automatic_capture(score_screenshot_grayscale, template_directory, '.png')
        return score

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
                x_coords, y_coords = screenshot_template_match_multiple(screenshot_grayscale, os.path.join(template_directory, 'gathering', str(x) + file_suffix), threshold)
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

def preprogrammed_crafts(args, preprogrammed_list):
        # Define preprogrammed parameters
        preprogrammed_crafts_dict = {'instacraft': [[12], [10], 20]} # Format is [hotbar number, wait times, iterations]
        # Substitute unprovided arguments with preprogrammed ones
        if args.hotbar_number == None:
                args.hotbar_number = preprogrammed_crafts_dict[args.preprogrammed.lower()][0]
        if args.wait_time == None:
                args.wait_time = preprogrammed_crafts_dict[args.preprogrammed.lower()][1]
        if args.iterations == None:
                args.iterations = preprogrammed_crafts_dict[args.preprogrammed.lower()][2]
        return args

def main():
        def validate_args(args, preprogrammed_list):
                # Provide detailed help if specified
                if args.detailedHelp:
                        instacraft = 'instacraft = [-h: 12, -w: 10, -i: 20]'
                        printList = str(preprogrammed_list).replace("'", "")
                        printList = eval(printList)
                        for entry in printList:
                                entry = textwrap.dedent(entry)
                                entry = entry.strip('\n').replace('\n', ' ')
                                for line in textwrap.wrap(entry, width=50):
                                        print(line)
                                print('')
                        quit()
                # Default arguments to pre-programmed values if applicable
                if args.preprogrammed == None:
                        if args.hotbar_number == None:
                                print('-p and/or -h argument was not provided')
                                quit()
                        elif args.wait_time == None:
                                print('-p and/or -w argument was not provided')
                                quit()
                        elif args.iterations == None:
                                print('-p and/or -i argument was not provided')
                                quit()
                elif args.preprogrammed == 'collect':
                        return args
                else:
                        args = preprogrammed_crafts(args, preprogrammed_list)
                # Validate that arguments are sensible
                for num in args.hotbar_number:
                        if not 0 < num < 13:
                                print('-h argument must be a positive integer from 1-12')
                                quit()
                for num in args.wait_time:
                        if 0 > num:
                                print('-w argument must be a positive integer')
                                quit()
                if 0 > args.iterations:
                        print('-i argument must be a positive integer')
                        quit()
                # Substitute hotbar numbers with their respective coordinates as list
                for i in range(len(args.hotbar_number)):
                        args.hotbar_number[i] = skillbar4_coordinates()[args.hotbar_number[i]-1]
                return args
        # Hard-coded declarations of relevant file locations
        '''It will be ideal to somehow store this in a semi-permanent way within
        the code; need to learn how to do that first!
        '''
        template_directory = r'D:\Libraries\Documents\GitHub\personal_projects\FFXIV_related\template_images\autoclick'
        # Hard-coded declaration of pre-programmed craft arguments
        preprogrammed_list = ['instacraft', 'collect']
        
        ##### USER INPUT SECTION
        usage = """%(prog)s automates clicks for FFXIV crafting. It has been tuned
        to run on the author's PC - hotbar locations are hard-coded.
        Type -H for a full list of pre-programmed crafting automations.
        """
        p = argparse.ArgumentParser(description=usage)
        p.add_argument("-p", dest="preprogrammed", choices=preprogrammed_list,
                       help="""Specify a pre-programmed click automation; this argument
                       automatically sets any relevant arguments below, but you can
                       "overwrite" the default setting for the pre-programmed
                       automation by specifying these manually.""")
        p.add_argument("-n", dest="hotbar_number", nargs="+", type=int,
                       help="""Craft: Hotbar number (from 1 to 12); if the craft
                       requires more than 1 macro, specify multiple values
                       separated by a space.""")
        p.add_argument("-w", dest="wait_time", nargs="+", type=int,
                       help="""Craft: Number of seconds to wait for the macro to end
                       ; if the craft requires more than 1 macro, specify
                       multiple values separated by a space""")
        p.add_argument("-i", dest="iterations", type=int,
                       help="Craft: Number of items to craft")
        p.add_argument("-H", dest="detailedHelp", action='store_true',
                     help="Provide details of preprogrammed function")
        args = p.parse_args()
        args = validate_args(args, preprogrammed_list)
        
        # Single monitor mode
        if len(screeninfo.get_monitors()) == 1:
                single_monitor_mode = True
                SINGLE_MONITOR_DELAY = 10
        else:
                single_monitor_mode = False
        if single_monitor_mode == True:
                print('Single monitor mode is active; ' + str(SINGLE_MONITOR_DELAY) + ' second delay will be enacted now to allow for alt tabbing.')
                time.sleep(SINGLE_MONITOR_DELAY)
        
        # Call function
        if args.preprogrammed == None or args.preprogrammed == 'instacraft':
                craft(args.hotbar_number, args.wait_time, args.iterations, template_directory) # Hard-coded macro 3: instacraft
        elif args.preprogrammed == 'collect':
                collect(template_directory)
        

if __name__ == '__main__':
        main()
