#! python3
# schematic_to_excel.py
# Converts a text file containing a condensed text format representing a nursecalle
# schematic into an expanded Excel sheet with rich formating.

import os, argparse, re, xlsxwriter

class Tests:
        def __init__(self, input_file):
                self.input_file = input_file
        
        def run_test_1(self):
                schema = Schematic(self.input_file).parse_file_to_table()
                'Not raising an exception constitutes a pass for this test'
                self.test_1_result = schema

class Validation:
        def __init__(self):
                pass
        
        def file_exists(file_location):
                if not os.path.isfile(file_location):
                        raise Exception('Input file does not exist; program closing.')
        
        def not_file_exists(file_location):
                if os.path.isfile(file_location):
                        raise Exception('Output file already exists; program closing.')
        
        def return_unique_name(name_prefix, name_suffix):
                ongoing_count = 1
                while True:
                        if not os.path.isfile(name_prefix + name_suffix):
                                return name_prefix + name_suffix
                        elif not os.path.isfile(name_prefix + str(ongoing_count) + name_suffix):
                                return name_prefix + str(ongoing_count) + name_suffix
                        else:
                                ongoing_count += 1

class Schematic:
        def __init__(self, schematic_file_location):
                Validation.file_exists(schematic_file_location)
                self.file_location = schematic_file_location
                self.table = {}
                self.excel = None
        
        def parse_file_to_table(self):
                # Create pattern matches
                sequential_pattern = re.compile(r'(.+?)\s(\d{1,10}\s-\s\d{1,10})\t(.*?D\d{1,10})$') # .*? allows multiple door codes
                individual_pattern = re.compile(r'(.+?)\t(.*?D\d{1,10})$')
                door_code_pattern = re.compile(r'(D\d{1,10},?)+')
                door_code_section2_pattern = re.compile(r'^(D\d{1,10})$') # , is not allowed in section 2 and must be whole line
                quad_pattern = re.compile(r'([^\t]+)\t([^\t]+)\t([^\t]+)\t(\d{1,10}|\.)$')
                # Parse file
                with open(self.file_location) as file_in:
                        # Break file up into sections
                        file_sections = [[], []] # Condensed schema has 2 sections
                        section_index = 0
                        for line in file_in:
                                l = line.strip(' \t\r\n')
                                if l == '':
                                        continue
                                if not l == '##':
                                        file_sections[section_index].append(l)
                                else:
                                        section_index += 1
                        if file_sections[1] == []:
                                raise Exception('Input file is not properly formatted; likely missing ## separating sections.')
                        # Interpret section 1
                        section1_subsections = {} # This will contain door codes associated to room names grouped by level name
                        recent_name = ''
                        for l in file_sections[0]:
                                # Create dictionary structure for formatting multiple sheets
                                if l.startswith('##'):
                                        recent_name = l.strip(' #')
                                        if recent_name not in section1_subsections:
                                                section1_subsections[recent_name] = []
                                        continue
                                # Handling of condensed sequential 'room' lines
                                sequential_hit = re.search(sequential_pattern, l)
                                individual_hit = re.search(individual_pattern, l) # individual_hit will match sequential_hit lines too
                                if sequential_hit != None: # By checking for sequential_hit first, we prevent the matching behaviour being a problem
                                        room_name, sequence, door_codes = sequential_hit.groups()
                                        # Validate door_codes
                                        if re.search(door_code_pattern, door_codes) == None:
                                                raise Exception('Door codes section of line "' + l + '" does not meet formatting expectations; fix the file.')
                                        door_codes = door_codes.split(',')
                                        # Validate sequence
                                        start, stop = map(int, sequence.split(' - ')) # This will always work because the pattern matches \d
                                        if not stop > start:
                                                raise Exception('Number range in line "' + l + '" is not sensible as the second number is not larger than the first; fix the file.')
                                        # Store individual results for sequence
                                        for number in range(start, stop+1): # +1 to correct for 0-based counting
                                                section1_subsections[recent_name].append([room_name + ' ' + str(number), door_codes])
                                # Handling of individual 'room' lines
                                elif individual_hit != None:
                                        room_name, door_codes = individual_hit.groups()
                                        # Validate door_codes
                                        if re.search(door_code_pattern, door_codes) == None:
                                                raise Exception('Door codes section of line "' + l + '" does not meet formatting expectations; fix the file.')
                                        door_codes = door_codes.split(',')
                                        # Store result
                                        section1_subsections[recent_name].append([room_name, door_codes])
                                else:
                                        raise Exception('Line "' + l + '" does not meet formatting expectations; fix the file.')
                        # Interpret section 2
                        section2_subsections = {} # This will contain device lists associated to door codes
                        recent_name = ''
                        for l in file_sections[1]:
                                # Validate that section 2 has a door code
                                door_hit = re.search(door_code_section2_pattern, l)
                                if door_hit != None:
                                        recent_name = door_hit.group()
                                        if recent_name not in section2_subsections:
                                                section2_subsections[recent_name] = []
                                        continue
                                if recent_name == '':
                                        raise Exception('Section two does not begin with an individual door code e.g., "D05"; fix the file.')
                                # Validate that section 2 quad lines are correctly formatted
                                quad_hit = re.search(quad_pattern, l)
                                if quad_hit == None:
                                        raise Exception('Section two does not have proper "id\tfull_name\tnumber" format for line "' + l + '"; fix the file.')
                                # Associate device:part:id:connection quad to its parent door code in our dictionary structure
                                quad = l.split('\t')
                                for i in range(len(quad)):
                                        if quad[i] == '.':
                                                quad[i] = ''
                                device, part, id_num, connection_num = quad # Break quad apart to show what each component represents
                                section2_subsections[recent_name].append([device, part, id_num, connection_num])
                # Combine sections into the parsed table output
                for level_name, room_device_pair_list in section1_subsections.items():
                        self.table[level_name] = {}
                        for room_device_pair in room_device_pair_list:
                                room_name, device_list = room_device_pair
                                for device in device_list:
                                        device_quad = section2_subsections[device]
                                        for device, part, id_num, connection_num in device_quad:
                                                if room_name not in self.table[level_name]:
                                                        self.table[level_name][room_name] = []
                                                'room_name is redundant below, but it makes a looping function later on easier to manage'
                                                self.table[level_name][room_name].append([room_name, device, part, id_num, connection_num])
        
        def table_to_tsv(self, output=None):
                self.tsv = []
                for level_name in self.table:
                        self.tsv.append(level_name)
                        self.tsv.append('Room\tDevice\tPart #\tDevice ID\tConnected to Device')
                        for room_name in self.table[level_name]:
                                for i in range(len(self.table[level_name][room_name])):
                                        if i == 0:
                                                self.tsv.append(room_name + '\t' + '\t'.join(self.table[level_name][room_name][i]))
                                        else:
                                                self.tsv.append('\t' + '\t'.join(self.table[level_name][room_name][i]))
                if output != None:
                        try:
                                Validation.not_file_exists(output)
                                with open(output, 'w') as file_out:
                                        file_out.write('\n'.join(self.tsv))
                        except:
                                print('Failed to produce tsv output due to file exists error; data only stored in attribute.')
        
        def table_to_excel(self, output=None):
                # Build workbook object after deriving output name
                if output != None:
                        try:
                                Validation.not_file_exists(output)
                                if not output.lower().endswith('.xlsx'):
                                        output += '.xlsx'
                        except:
                                print('Failed to produce Excel output due to file exists error; method call not completed')
                                return None
                else:
                        output = Validation.return_unique_name('Workbook', '.xlsx')
                        print('No output name provided to method; Excel file will be saved at "' + os.path.abspath(output) + '"')
                workbook = xlsxwriter.Workbook(output)
                # Add our formatting objects
                sheet_head_format = workbook.add_format({'bold': True,
                                                     'underline': True,
                                                     'font_size': 18,
                                                     'align': 'center',
                                                     'valign': 'vcenter',
                                                     'border': 1})
                column_head_format = workbook.add_format({'font_size': 10,
                                                          'font_name': 'Arial',
                                                          'bold': True,
                                                          'align': 'center',
                                                          'valign': 'bottom',
                                                          'border': 1,
                                                          'bg_color': '#BFBFBF',
                                                          'text_wrap': True})
                merge_format = workbook.add_format({'font_size': 10,
                                                    'font_name': 'Arial',
                                                    'align': 'center',
                                                    'valign': 'vcenter',
                                                    'left': 1,
                                                    'right': 1,
                                                    'bottom': 2})
                basic_row_format = workbook.add_format({'font_size': 10,
                                                        'font_name': 'Arial',
                                                        'border': 1})
                bottom_row_format = workbook.add_format({'font_size': 10,
                                                         'font_name': 'Arial',
                                                         'left': 1,
                                                          'right': 1,
                                                          'top': 1,
                                                          'bottom': 2})
                basic_device_format = workbook.add_format({'font_size': 10,
                                                           'font_name': 'Arial',
                                                           'border': 1,
                                                           'align': 'center'})
                bottom_device_format = workbook.add_format({'font_size': 10,
                                                            'font_name': 'Arial',
                                                            'align': 'center',
                                                            'left': 1,
                                                            'right': 1,
                                                            'top': 1,
                                                            'bottom': 2})
                # Hard-coded sheet text structure
                SHEET_HEAD_SUFFIX = ' Call Points Configuration'
                SHEET_HEAD_WORKSHEET_SUFFIX = ' Call Points'
                COLUMN_HEAD_TEXT = ['Room', 'Device', 'Part #', 'Node ID',
                                    'Port ID', 'Device ID', 'Connected to Device',
                                    'Installed', 'Tested', 'Comments']
                COLUMNS_TO_WRITE_TO = ['Room', 'Device', 'Part #', 'Device ID',
                                       'Connected to Device']
                COLUMN_WIDTH = [15, 16, 13, 5, 5, 6, 12, 8, 8, 19]
                COLUMN_HEAD_ROW_HEIGHT = 28
                # Create sheet(s)
                for sheet_name in self.table.keys():
                        worksheet = workbook.add_worksheet(sheet_name + SHEET_HEAD_WORKSHEET_SUFFIX)
                        # Write main header
                        worksheet.merge_range('A1:J1', sheet_name + SHEET_HEAD_SUFFIX, sheet_head_format)
                        # Write column header
                        worksheet.set_row(1, COLUMN_HEAD_ROW_HEIGHT)
                        for i in range(len(COLUMN_HEAD_TEXT)):
                                worksheet.write(1, i, COLUMN_HEAD_TEXT[i], column_head_format) # Row 1, col i
                                worksheet.set_column(i, i, COLUMN_WIDTH[i])
                        # Write sheet contents by iterating through table list
                        row_num = 2 # We've written the first two rows; this value is 0-indexed
                        for room_name, room_list in self.table[sheet_name].items():
                                # Write to cells where we have values to insert
                                for column in COLUMNS_TO_WRITE_TO:
                                        column_index = COLUMN_HEAD_TEXT.index(column) # This should make it easier to extend upon program in future
                                        room_list_index = COLUMNS_TO_WRITE_TO.index(column) # This is necessary for extracting values out of room_list below
                                        # Handle room cells
                                        if column == 'Room':
                                                if len(room_list) > 1:
                                                        'We need to -1 the below len() call since merge_range starts 0-indexed, but it runs up to and including the end'
                                                        worksheet.merge_range(row_num, column_index, row_num + len(room_list)-1, column_index, room_name, merge_format)
                                                else:
                                                        worksheet.write(row_num, column_index, room_name, merge_format)
                                        # Handle all other cells
                                        else:
                                                for list_num in range(len(room_list)): # list_num refers to row in our list
                                                        if list_num != len(room_list) - 1:
                                                                if column == 'Device ID' or column == 'Connected to Device':
                                                                        worksheet.write(row_num + list_num, column_index, room_list[list_num][room_list_index], basic_device_format)
                                                                else:
                                                                        worksheet.write(row_num + list_num, column_index, room_list[list_num][room_list_index], basic_row_format)
                                                        else:
                                                                if column == 'Device ID' or column == 'Connected to Device':
                                                                        worksheet.write(row_num + list_num, column_index, room_list[list_num][room_list_index], bottom_device_format)
                                                                else:
                                                                        worksheet.write(row_num + list_num, column_index, room_list[list_num][room_list_index], bottom_row_format)
                                # Format empty cells
                                for column in COLUMN_HEAD_TEXT:
                                        if column in COLUMNS_TO_WRITE_TO: # Skip columns covered by above code block
                                                continue
                                        column_index = COLUMN_HEAD_TEXT.index(column) # This should make it easier to extend upon program in future
                                        # Handle merged cells
                                        if column == 'Node ID' or column == 'Port ID':
                                                if len(room_list) > 1:
                                                        'We need to -1 the below len() call since merge_range starts 0-indexed, but it runs up to and including the end'
                                                        worksheet.merge_range(row_num, column_index, row_num + len(room_list)-1, column_index, '', merge_format)
                                                else:
                                                        worksheet.write(row_num, column_index, '', merge_format)
                                        # Handle all other cells
                                        else:
                                                for list_num in range(len(room_list)): # list_num refers to row in our list
                                                        if list_num != len(room_list) - 1:
                                                                if column == 'Installed' or column == 'Tested':
                                                                        worksheet.write(row_num + list_num, column_index, '', basic_device_format)
                                                                else:
                                                                        worksheet.write(row_num + list_num, column_index, '', basic_row_format)
                                                        else:
                                                                if column == 'Installed' or column == 'Tested':
                                                                        worksheet.write(row_num + list_num, column_index, '', bottom_device_format)
                                                                else:
                                                                        worksheet.write(row_num + list_num, column_index, '', bottom_row_format)
                                # Update our row number for the next iteration
                                row_num += len(room_list)
                workbook.close()

def main():
        def validate_args(args):
                # Validate that input file exists
                Validation.file_exists(args.input)
                # Validate that output file does not exist
                Validation.not_file_exists(args.output)
        
        usage = '''%(prog)s will convert condensed schematic text format into
        an expanded and richly formatted Excel sheet. Provide the arguments
        specified below.
        '''
        p = argparse.ArgumentParser(description=usage)
        p.add_argument('-i', dest='input', 
                       help='''
                       Specify schematic text file name.
                       ''')
        p.add_argument('-o', dest='output',
                       help='''
                       Specify the output Excel file name (recommended to use
                       .xlsx suffix so Excel recognises file).
                       ''')
        args = p.parse_args()
        args = validate_args(args)
        
        # Create Schematic object
        schema = Schematic(args.input)
        # Parse input file to generate table list
        schema.parse_file_to_table()
        # Convert table to basic tsv format
        schema.table_to_tsv()
        # Convert tsv to an xlsxwriter-formatted Excel object
        schema.table_to_excel()

def test():
        test_1_file = r'C:\Users\Zac\Desktop\Jordan_coding\PDF2Table\NC_modified.txt'
        test = Tests(test_1_file)
        test.run_test_1()
        
if __name__ == '__main__':
        testing = True # This is only accessible by modifying the code
        if testing == True:
                test()
        else:
                main()
