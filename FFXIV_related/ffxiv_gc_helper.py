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
import os, urllib.request, json, pytesseract, cv2, screeninfo
import numpy as np
from PIL import Image
from mss import mss

# Identify the tesseract.exe file on Windows computers
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Web query functions
def xivapi_string_search(item_name):
        request = urllib.request.urlopen("https://xivapi.com/search?string=" + item_name).read()
        json_data = json.loads(request)
        return json_data

def xivapi_json_from_url_suffix(url_suffix):
        '''The url suffix is provided by the API; it is just the combination of
        item type and ID e.g., "/Recipe/38" but for simplification we might as 
        well just use the url the API gives us rather than make it ourselves.'''
        request = urllib.request.urlopen("http://xivapi.com" + url_suffix).read()
        json_data = json.loads(request)
        return json_data

def xivapi_json_result_identify(json_data, item_name, item_type):
        best_matches = []
        close_matches = []
        for item in json_data['Results']:
                if item['Name'].lower() == item_name.lower() and item['UrlType'].lower() == item_type.lower():
                        best_matches.append(item)
                elif item['Name'].lower() == item_name.lower() and item['UrlType'].lower() != item_type.lower():
                        close_matches.append(item)
                elif item['Name'].lower() != item_name.lower() and item['UrlType'].lower() == item_type.lower():
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

def xivapi_automated_query(item_name, item_type):
        search_json = xivapi_string_search(item_name)
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
        item_json = xivapi_json_from_url_suffix(search_hit['Url'])
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

def shopping_cart_pretty_list(shopping_cart):
        '''Our "shopping_cart" refers to our ongoing dictionary of item name
        and quantity pairs.
        '''
        # Get ordered list of shopping cart ingredients
        cart_keys = list(shopping_cart.keys())
        cart_keys.sort()
        # Determine our longest item name
        longest_name = ''
        for key, value in shopping_cart.items():
                if len(key) > len(longest_name):
                        longest_name = key
        # Determine our longest ingredient quantity
        longest_quantity = ''
        for key, value in shopping_cart.items():
                if len(str(value)) > len(longest_quantity):
                        longest_quantity = str(value)
        # Format a pretty list of items for printing
        output_list = ['## FFXIV Grand Company shopping cart ##']
        for key in cart_keys:
                output_list.append(key.ljust(len(longest_name)) + ' ' + str(shopping_cart[key]).rjust(len(longest_quantity)))
        return output_list

def cv2_tesseract_OCR(image_file):
        '''Some code borrowed from 
        https://github.com/AnirudhMergu/TesseractOCR/blob/master/ocr_main.py
        '''
        # Load and preprocess image
        image = cv2.imread(image_file)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        # Produce temporary file
        filename = os.path.join(os.path.dirname(image_file), temp_file_prefix_gen('temp') + '.png')
        cv2.imwrite(filename, gray)
        # OCR of preprocessed image file
        ocr_text = pytesseract.image_to_string(Image.open(filename))
        # Delete temporary file & return
        os.unlink(filename)
        return ocr_text

def xiv_OCR_text_cleanup(ocr_text):
        while '\n\n' in ocr_text:
                ocr_text = ocr_text.replace('\n\n', '\n')
        return ocr_text

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
                return False
        # Derive coordinates of grand company box template text
        y_coord, x_coord = matches[0][0], matches[1][0]
        # Extrapolate the coordinates of the region which will contain item names
        '''Some attempt is made to scale this extrapolation to the user's
        monitor size; testing was performed on a standard 1080p monitor'''
        monitor = screeninfo.get_monitors()[0]
        names_x_topleft = int(x_coord + (50 / (1920 / monitor.width)))
        names_y_topleft = int(y_coord + (110 / (1080 / monitor.height)))
        return names_x_topleft, names_y_topleft

def temp_file_prefix_gen(prefix):
        ongoingCount = 1
        while True:
                if not os.path.isfile(prefix):
                        return prefix
                elif os.path.isfile(prefix + str(ongoingCount)):
                        ongoingCount += 1
                else:
                        return prefix + str(ongoingCount)

def xivapi_manual_data_entry():
        print('To use this program in MANUAL mode, enter the name of an object to retrieve details.')
        print('Specify the full item name, or alternatively use wildcard syntax to autocomplete or find multiple matches.')
        print('e.g., "Bronze spatha" and "Bronze sp*" are both valid searches (without quotations).')
        print('Program can be exited by typing "quit"')
        shopping_cart = {} # This serves as our ongoing list of ingredients
        while True:
                # User input loop
                while True:
                        user_input = input()
                        # Program exit condition
                        if user_input.lower() == 'quit':
                                quit
                        # Curate input
                        user_input = user_input.strip(' \r\n')
                        # Validate input
                        if ';' not in user_input:
                                print('; character is required to separate name from type.')
                                continue
                        item_name, item_type = user_input.split(';')
                        if len(item_name) < 1 or len(item_type) < 1:
                                print('name and/or type value must be specified.')
                                continue
                        elif item_type.lower() not in ['item', 'recipe']:
                                print('object type must be "item" or "recipe".')
                                continue
                        # Loop exits here if conditions were met
                        break
                # Obtain relevant database item as JSON
                item_json = xivapi_automated_query(item_name, item_type)
                if item_json == False:
                        print('XIVAPI query failed; try again with new search terms or exit program with "quit"')
                        continue
                # Extract materials from JSON
                item_ingredient_dict = xivapi_recipe_data_extraction(item_json)
                # Add materials into the shopping cart
                shopping_cart = dict_merge(shopping_cart, item_ingredient_dict)
                # Format list of required materials and print for user inspection
                for line in shopping_cart_pretty_list(shopping_cart):
                        print(line)
                print('')
                print('Next item?')

def xivapi_automated_gc_ingredients():
        print('To use this program in AUTO mode, enter FFXIV and bring up the Grand Company Delivery Missions screen unobscured by any other UI elements')
        print('Once this has been performed, press the tilde key (~) to automatically')
        print('Program can be exited by typing "quit"')
        shopping_cart = {} # This serves as our ongoing list of ingredients
        while True:
                # User input loop
                while True:
                        user_input = input()
                        # Program exit condition
                        if user_input.lower() == 'quit':
                                quit
                        # Curate input
                        user_input = user_input.strip(' \r\n')
                        # Validate input
                        if ';' not in user_input:
                                print('; character is required to separate name from type.')
                                continue
                        item_name, item_type = user_input.split(';')
                        if len(item_name) < 1 or len(item_type) < 1:
                                print('name and/or type value must be specified.')
                                continue
                        elif item_type.lower() not in ['item', 'recipe']:
                                print('object type must be "item" or "recipe".')
                                continue
                        # Loop exits here if conditions were met
                        break
                # Obtain relevant database item as JSON
                item_json = xivapi_automated_query(item_name, item_type)
                if item_json == False:
                        print('XIVAPI query failed; try again with new search terms or exit program with "quit"')
                        continue
                # Extract materials from JSON
                item_ingredient_dict = xivapi_recipe_data_extraction(item_json)
                # Add materials into the shopping cart
                shopping_cart = dict_merge(shopping_cart, item_ingredient_dict)
                # Format list of required materials and print for user inspection
                for line in shopping_cart_pretty_list(shopping_cart):
                        print(line)
                print('')
                print('Next item?')
        
        
        
        x_topleft, y_topleft = ffxiv_gc_box_coords(take_screenshot(), template_file)
        eg = take_screenshot((x_topleft, y_topleft, int(250 / (1920 / monitor.width)), int(350 / (1080 / monitor.height))))
        cv2.imwrite(r'C:\Users\Zac\Desktop\FFXIV_coding\testing_crop.png', eg)
        cv2_tesseract_OCR(image_file)

# Main call
def main():
        ## Declare template image location OR store hard-coded?
        template_file = r'C:\Users\Zac\Desktop\FFXIV_coding\gc_template.png'
        xivapi_manual_data_entry()
        

if __name__ == '__main__':
        main()
