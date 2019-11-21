#! python3
# ffxiv_gc_helper.py
# Code to assist in the process of completing Grand Company delivery missions.
# By analysing a screenshot of the supply items, this program will produce a
# list of the reagents needed to craft the items suggested.

'''
Functions to implement;
1) Computer vision reading of the item names and quantities
2) FFXIV crafting database web queries to obtain the reagents required for crafting
3) FFXIV vendor information web queries to determine where reagents may be bought

Optional implements;
1) Box-by-box scanning of retainer and main character inventories to maintain
a database of these items and their locations for easier determination of
what items are actually required to be bought

2) Crafting completion lists for levels
http://forum.square-enix.com/ffxiv/threads/354596-Crafting-Log-Lists-on-Garland-Tools
'''

# Import modules
import os, json, pytesseract, cv2, screeninfo, keyboard, queue, time, win32clipboard, pyperclip, sys
import numpy as np
from urllib.request import Request, urlopen
from PIL import Image
from mss import mss
from prettytable import PrettyTable
from io import BytesIO

# Web query functions
def xivapi_string_search(item_name, api_private_key):
        url_string = "https://xivapi.com/search?string=" + item_name + "&private_key=" + api_private_key
        request = urlopen(Request(url_string, headers = {'User-Agent': 'Mozilla/5.0'})).read()
        json_data = json.loads(request)
        return json_data

def xivapi_json_from_url_suffix(url_suffix, api_private_key):
        '''The url suffix is provided by the API; it is just the combination of
        item type and ID e.g., "/Recipe/38" but for simplification we might as 
        well just use the url the API gives us rather than make it ourselves.'''
        url_string = "http://xivapi.com" + url_suffix + "?private_key=" + api_private_key
        request = urlopen(Request(url_string, headers = {'User-Agent': 'Mozilla/5.0'})).read()
        json_data = json.loads(request)
        return json_data

def xivapi_json_result_identify(json_data, item_name, item_type):
        best_matches = []
        close_matches = []
        for item in json_data['Results']:
                json_item_name = url_utf8_encode(item['Name']) # Our item_name is url encoded, so this needs to also be encoded
                if json_item_name.lower() == item_name.lower() and item['UrlType'].lower() == item_type.lower():
                        best_matches.append(item)
                elif json_item_name.lower() == item_name.lower() and item['UrlType'].lower() != item_type.lower():
                        close_matches.append(item)
                elif json_item_name.lower() != item_name.lower() and item['UrlType'].lower() == item_type.lower():
                        close_matches.append(item)
        # Return good queries
        if len(best_matches) == 1:
                return best_matches[0]
        # Return redundant queries
        elif len(close_matches) > 0:
                return close_matches
        # Return failed queries
        else:
                return False

def xivapi_automated_query(item_name, api_private_key, item_type='recipe'):
        search_json = xivapi_string_search(item_name, api_private_key)
        search_hit = xivapi_json_result_identify(search_json, item_name, item_type)
        # Return False if query failed to find results
        if search_hit == False:
                return False
        # If search was ambiguous, allow user to determine correct choice in cmd prompt
        elif type(search_hit) == list:
                # Prevent excessively large queries from being displayed at all
                if len(search_hit) > 20:
                        print('Search returned more than 20 hits; displaying all hits may be excessive.')
                        print('You should refine your search further by checking this url in your browser first.')
                        print('(This is what I\'m looking at, and I\'m confused :S)')
                        print('https://xivapi.com/search?string=' + item_name)
                        return False
                # Handle normal-sized queries
                print('Search returned multiple possible options.')
                print('Enter a digit corresponding to the "1"st, "2"nd, "3"rd... etc., result that '
                      'is correct, or enter "n" if no results suit to perform the search again.')
                for i in range(len(search_hit)):
                        print(str(i+1) + ': Name="' + search_hit[i]['Name'] + '";Type="' + search_hit[i]['UrlType'] + '"')
                while True:
                        user_input = input()
                        if user_input.isdigit():
                                if 0 < int(user_input) <= len(search_hit):
                                        print('Item selected successfully.')
                                        search_hit = search_hit[int(user_input)-1]
                                        break
                                else:
                                        print('A digit was entered but it was less than 1 or greater than the number '
                                              'of possible options. Try again.')
                        elif user_input.lower() == 'n':
                                return False
                        else:
                                print('Input not recognised; should be a digit or "n" (no quotations).')
        # Identify item values
        item_json = xivapi_json_from_url_suffix(search_hit['Url'], api_private_key)
        return item_json

def xivapi_recipe_data_extraction(item_json):
        ingredient_dict = {}
        for i in range(0, 999):
                # Terminate when no more ingredients exist
                if 'AmountIngredient' + str(i) not in item_json:
                        break
                # Skip irrelevant entries
                elif item_json['AmountIngredient' + str(i)] == 0:
                        '''XIVAPI seems to have entries for aetheric components even if
                        they aren't used in the crafting? Unsure, but can safely ignore'''
                        continue
                # Identify ingredient quantity and name
                ingredient_quantity = item_json['AmountIngredient' + str(i)]
                ingredient_name = item_json['ItemIngredient' + str(i)]['Name']
                # Store details in dictionary
                ingredient_dict[ingredient_name] = ingredient_quantity
        return ingredient_dict

def dict_merge(dict1, dict2):
        '''dict2 will be merged INTO dict1'''
        for k2, v2 in dict2.items():
                if k2 not in dict1:
                        dict1[k2] = v2
                else:
                        dict1[k2] += v2
        return dict1 

def shopping_cart_pretty_table(shopping_cart):
        '''Our "shopping_cart" refers to our ongoing dictionary of item name
        and quantity pairs.
        '''
        # Get ordered list of shopping cart ingredients
        cart_keys = list(shopping_cart.keys())
        cart_keys.sort()
        # Format a pretty list of items for printing
        t = PrettyTable(['Ingredient', 'Quantity'])
        for key in cart_keys:
                t.add_row([key, shopping_cart[key]])
        return t

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

def OCR_text_cleanup(ocr_text):
        while '\n\n' in ocr_text:
                ocr_text = ocr_text.replace('\n\n', '\n')
        return ocr_text

def OCR_mistake_correction(ocr_string):
        # Fix uncapitalised first letters
        '''In FFXIV the first letter of an item name is always capitalised;
        where the first letter is not uppercase we can thus be certain that an 
        OCR mistake has occurred
        '''
        if not ocr_string[0].isupper():
                if ocr_string[0] == 'l':
                        ocr_string = 'I' + ocr_string[1:]
        return ocr_string

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

def ffxiv_gc_box_coords(screenshot_grayscale, template_file, threshold=0.9):
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
        # Derive coordinates of grand company box template text
        y_coord, x_coord = matches[0][0], matches[1][0]
        # Extrapolate the coordinates of the region which will contain item names
        '''Some attempt is made to scale this extrapolation to the user's
        monitor size; testing was performed on a standard 1080p monitor'''
        monitor = screeninfo.get_monitors()[0]
        gc_x_topleft = int(x_coord + (50 / (1920 / monitor.width)))
        gc_y_topleft = int(y_coord + (110 / (1080 / monitor.height)))
        return gc_x_topleft, gc_y_topleft

def temp_file_prefix_gen(prefix, suffix):
        ongoingCount = 1
        while True:
                if not os.path.isfile(prefix + suffix):
                        return prefix + suffix
                elif os.path.isfile(prefix + str(ongoingCount) + suffix):
                        ongoingCount += 1
                else:
                        return prefix + str(ongoingCount) + suffix

def start_key_logger():
        q = queue.Queue()
        keyboard.start_recording(q)
        return q

def stop_key_logger():
        q = keyboard.stop_recording()
        return q

def key_logger_queue_to_string(q, skipSpecial):  # q should be a queue. Queue object from 'keyboard' module
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

def wait_on_keylogger_for_key_press(key):
        while True:
                q = start_key_logger()
                time.sleep(0.5)
                q = stop_key_logger()
                s = key_logger_queue_to_string(q, True)
                if key in s:
                        break

def url_utf8_encode(string):
        string = string.replace(' ', '%20').replace("'", '%27')
        return string

def xivapi_manual_data_entry(api_private_key):
        print('To use this program in MANUAL mode, copy the name of an object to your clipboard to retrieve details.')
        print('Specify the full item name, or alternatively use wildcard syntax to autocomplete or find multiple matches.')
        print('e.g., "Bronze spatha" and "Bronze sp*" are both valid searches (without quotations).')
        print('Shopping cart can be emptied by typing "clear"; program can be exited by typing "quit"; multiple items can be copied if separated vertically by newlines.')
        shopping_cart = {} # This serves as our ongoing list of ingredients
        while True:
                # User input loop
                while True:
                        print('Copy item name(s) then press ENTER, or type "quit" or "clear".')
                        text_entry = input()
                        item_names = pyperclip.paste()
                        # Program exit condition
                        if text_entry.lower() == 'quit':
                                sys.exit()
                        # Shopping cart clear
                        elif text_entry.lower() == 'clear':
                                shopping_cart = {}
                                continue
                        # Curate input
                        item_names = item_names.strip(' \r\n').replace('\r','').split('\n')
                        # Validate input
                        if item_names == ['']:
                                print('Name value must be specified.')
                                continue
                        # Loop exits here if conditions were met
                        break
                # Encode item name for proper searching
                for item_name in item_names:
                        item_name = url_utf8_encode(item_name)
                        # Obtain relevant database item as JSON
                        try:
                                item_json = xivapi_automated_query(item_name, api_private_key, 'recipe')
                        except Exception as e:
                                automated_query_exception_handler(item_name, e)
                                continue
                        if item_json == False:
                                print('XIVAPI query failed for "' + item_name + '"; ingredients will be skipped and program will continue.')
                                continue
                        # Extract materials from JSON
                        item_ingredient_dict = xivapi_recipe_data_extraction(item_json)
                        # Add materials into the shopping cart
                        shopping_cart = dict_merge(shopping_cart, item_ingredient_dict)
                # Format list of required materials and print for user inspection
                print(shopping_cart_pretty_table(shopping_cart))
                # Store in clipboard for good measure
                output_to_clipboard = ''
                for material in shopping_cart.keys():
                        output_to_clipboard += material + '\n'
                pyperclip.copy(output_to_clipboard)
                print('')

def screenshot_preprocess_for_ocr(monitor_object, x_topleft, y_topleft, x_topleft_offset, y_topleft_offset, RESIZE_RATIO, temp_dir):
        '''monitor_object relates to the object generated by e.g., screeninfo.get_monitors()[0]'''
        screenshot_item_names = take_screenshot((x_topleft, y_topleft, int(x_topleft_offset / (1920 / monitor_object.width)), int(y_topleft_offset / (1080 / monitor_object.height))))
        temp_filename = temp_file_prefix_gen(os.path.join(temp_dir, 'temp'), '.png')
        cv2.imwrite(temp_filename, screenshot_item_names)
        screenshot_temp_image = Image.open(temp_filename)
        resized_screenshot_image = screenshot_temp_image.resize(((int(250 / (1920 / monitor_object.width)) * RESIZE_RATIO), int(350 / (1080 / monitor_object.height)) * RESIZE_RATIO), Image.ANTIALIAS)
        resized_screenshot_image.save(temp_filename, 'PNG')
        return temp_filename

def xivapi_screenshot_to_OCR_pipeline(monitor_object, template_file, RESIZE_RATIO):
        # Obtain screenshot and check it for suitability
        screenshot_grayscale = take_screenshot()
        gc_x_topleft, gc_y_topleft = ffxiv_gc_box_coords(screenshot_grayscale, template_file, threshold=0.9)
        if gc_x_topleft == False:
                return False
        # Obtain a cropped screenshot of the item list & increase size
        temp_filename = screenshot_preprocess_for_ocr(monitor_object, gc_x_topleft, gc_y_topleft, 250, 350, RESIZE_RATIO, os.path.dirname(template_file))
        # Use OCR to extract text from the cropped, resized screenshot
        ocr_text = cv2_tesseract_OCR(temp_filename)
        ocr_text = OCR_text_cleanup(ocr_text)
        return temp_filename, ocr_text

def automated_query_exception_handler(item_name, e):
        if str(e) == 'HTTP Error 400: Bad Request':
                print(e)
                print('XIVAPI query failed')
                print('It is probable that the URL was not encoded properly (i.e., tell Zac what the item name is and he\'ll fix it)')
                print('Item name = "' + item_name + '"')
                print('Ingredients skipped and program will continue operation')
        if str(e) == 'HTTP Error 404: Not found':
                print(e)
                print('XIVAPI query failed')
                print('This item does not appear to be within the XIVAPI database. Not a lot I can do about that.')
                print('Item name = "' + item_name + '"')
                print('Ingredients skipped and program will continue operation')
        else:
                print(e)
                print('XIVAPI query failed')
                print('This exception is currently unhandled. Sorry. Tell Zac what the item name was and what the error messsage above was.')
                print('Item name = "' + item_name + '"')
                print('Ingredients skipped and program will continue operation')

def xivapi_auto_item_name_looping(name_list_1, name_list_2, iteration_number, api_private_key, recipe_type):
        failed = False
        item_json = False
        while True:
                # Encode item name for proper searching
                if failed == False:
                        item_name = url_utf8_encode(name_list_1[iteration_number])
                else:
                        item_name = url_utf8_encode(name_list_2[iteration_number])
                # Correct known OCR mistakes
                item_name = OCR_mistake_correction(item_name)
                try:
                        item_json = xivapi_automated_query(item_name, api_private_key, recipe_type)
                except Exception as e:
                        automated_query_exception_handler(item_name, e)
                if item_json == False and failed == False:
                        failed = True
                        continue
                break
        return item_json

def xivapi_automated_gc_ingredients(template_file, api_private_key):
        print('To use this program in AUTO mode, enter FFXIV and bring up the Grand Company Delivery Missions screen.')
        monitor = screeninfo.get_monitors()[0] # This is our main monitor's dimensions
        while True:
                shopping_cart = {} # This serves as our ongoing list of ingredients
                # Provisions loop will begin upon receiving the tilde key
                print('Press the tilde key (~) once you have brought up the Grand Company Delivery Missions *SUPPLY* screen unobscured by any other UI elements')
                wait_on_keylogger_for_key_press('~')
                while True:
                        '''We do a resize ratio of 6 and 8 as OCR sometimes works for one value but not the other'''
                        temp_supply_filename_6, ocr_supply_text_6 = xivapi_screenshot_to_OCR_pipeline(monitor, template_file, 6) # RESIZE_RATIO == 6
                        temp_supply_filename_8, ocr_supply_text_8 = xivapi_screenshot_to_OCR_pipeline(monitor, template_file, 8) # RESIZE_RATIO == 8
                        if ocr_supply_text_6 == False or ocr_supply_text_8 == False:
                                print('Grand Company Delivery Missions supply box was not identifiable on your screen.')
                                print('Make sure it is unobscured, and that your template is the correct size, then press tilde (~) to try again.')
                                wait_on_keylogger_for_key_press('~')
                                continue
                        supply_names_6 = ocr_supply_text_6.split('\n')
                        supply_names_8 = ocr_supply_text_8.split('\n')
                        if len(supply_names_6) != len(supply_names_8):
                                print('Grand Company Delivery Missions supply box was not captured correctly.')
                                print('Make sure it is unobscured, and that your template is the correct size, then press tilde (~) to try again.')
                                wait_on_keylogger_for_key_press('~')
                                continue
                        break
                # Supply loop will begin upon receiving the tilde key
                print('Press the tilde key (~) once you have brought up the Grand Company Delivery Missions *PROVISIONING* screen unobscured by any other UI elements')
                wait_on_keylogger_for_key_press('~')
                while True:
                        temp_provision_filename_6, ocr_provision_text_6 = xivapi_screenshot_to_OCR_pipeline(monitor, template_file, 6) # RESIZE_RATIO == 6
                        temp_provision_filename_8, ocr_provision_text_8 = xivapi_screenshot_to_OCR_pipeline(monitor, template_file, 8) # RESIZE_RATIO == 8
                        if ocr_provision_text_6 == False or ocr_provision_text_8 == False:
                                print('Grand Company Delivery Missions provisions box was not identifiable on your screen.')
                                print('Make sure it is unobscured, and that your template is the correct size, then press tilde (~) to try again.')
                                wait_on_keylogger_for_key_press('~')
                                continue
                        provision_names_6 = ocr_provision_text_6.split('\n')
                        provision_names_8 = ocr_provision_text_8.split('\n')
                        if len(provision_names_6) != len(provision_names_8):
                                print('Grand Company Delivery Missions provisions box was not captured correctly.')
                                print('Make sure it is unobscured, and that your template is the correct size, then press tilde (~) to try again.')
                                wait_on_keylogger_for_key_press('~')
                                continue
                        break
                # Clean up temp files
                for f in [temp_supply_filename_6, temp_supply_filename_8, temp_provision_filename_6, temp_provision_filename_8]:
                        os.unlink(f)
                # Loop through item names and build our shopping cart!
                supply_names = []
                for i in range(len(supply_names_6)):
                        item_json = xivapi_auto_item_name_looping(supply_names_6, supply_names_8, i, api_private_key, 'recipe')
                        if item_json == False:
                                print('XIVAPI query failed')
                                print('It is probable that this was caused by incorrect OCR capture of item name #' + str(i+1) + ' ("' + supply_names_6[i] + '"')
                                print('Ingredients skipped and program will continue operation')
                                continue
                        supply_names.append(item_json['Name'])
                        # Extract materials from JSON
                        item_ingredient_dict = xivapi_recipe_data_extraction(item_json)
                        # Add materials into the shopping cart
                        shopping_cart = dict_merge(shopping_cart, item_ingredient_dict)
                        # Associate materials to the item that they create
                        ### TBD
                # Check our provisioning values
                provision_names = []
                for i in range(len(provision_names_6)):
                        item_json = xivapi_auto_item_name_looping(provision_names_6, provision_names_8, i, api_private_key, 'item')
                        if item_json == False:
                                print('XIVAPI query failed')
                                print('It is probable that this was caused by incorrect OCR capture of provision name #' + str(i+1) + ' ("' + provision_names_6[i] + '"')
                                print('Ingredients skipped and program will continue operation')
                                continue
                        item_name = item_json['Name']
                        provision_names.append(item_name)
                        # Associate number of items based on i value
                        '''There are always 3 provisions, and the first 2 request 10x, with the final fishing request only being 1x'''
                        if i != 2:
                                item_ingredient_dict = {item_name: 10}
                        else:
                                item_ingredient_dict = {item_name: 1}
                        # Add materials into the shopping cart
                        shopping_cart = dict_merge(shopping_cart, item_ingredient_dict)
                # Format list of required materials and print for user inspection
                print(shopping_cart_pretty_table(shopping_cart))
                print('')
                print('Items requested:')
                print('\n'.join(supply_names))
                print('Provisions requested:')
                print('\n'.join(provision_names))
                print('')
                output_to_clipboard = '\n'.join(supply_names) + '\n' + '\n'.join(provision_names) + '\n#Materials'
                for material in shopping_cart.keys():
                        output_to_clipboard += '\n' + material
                pyperclip.copy(output_to_clipboard)
                print('All done! A list of items has been saved to your clipboard, too! Exclamation marks!!')

# Main call
def main():
        # Hard-coded declarations of relevant file locations
        '''It will be ideal to somehow store this in a semi-permanent way within
        the code; need to learn how to do that first!
        '''
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        template_file = r'D:\Libraries\Documents\GitHub\personal_projects\FFXIV_related\template_images\gc_template.png'
        api_private_key = '7a9eb114d3cb4c588c3b8c980640a58b3e39573f461e4dc9b925716d28103d32'
        # Allow user to determine what mode the program will run in
        print('Welcome to the FFXIV Grand Company Delivery Mission helper!')
        print('This program will assist in the completion of these objectives or in the crafting of any list of items.')
        print('Specify whether you want AUTO mode or MANUAL mode.')
        print('(AUTO = automatic capture of the GCDM window and tabulation of necessary materials)')
        print('(MANUAL = manually enter item names to build an ongoing "shopping cart" of necessary materials)')
        while True:
                user_input = input()
                user_input = user_input.lower().strip(' \r\n')
                if user_input not in ['auto', 'manual']:
                        print('You must type either AUTO or MANUAL (case insensitive)')
                break
        if user_input == 'auto':
                xivapi_automated_gc_ingredients(template_file, api_private_key)
        elif user_input == 'manual':
                xivapi_manual_data_entry(api_private_key)

if __name__ == '__main__':
        main()
