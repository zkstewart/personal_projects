#! python3
# schematic_to_excel.py
# Converts a text file containing a condensed text format representing a nursecalle
# schematic into an expanded Excel sheet with rich formating.

import os, argparse, re, xlsxwriter

class Tests:
        def __init__(self, input_file):
                self.input_file = input_file
        
        def run_test_1(self):
                schema = Schematic(self.input_file).parse_file_to_text()
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

class Schematic:
        def __init__(self, schematic_file_location):
                Validation.file_exists(schematic_file_location)
                self.file_location = schematic_file_location
                self.table = {}
                self.excel = None
        
        def parse_file_to_text(self):
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
                                device, part, id_num, connection_num = l.split('\t')
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
                                                self.table[level_name][room_name].append([device, part, id_num, connection_num])
        
        def table_to_tsv(self):
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
        #schema = Schematic(args.input)
        schema = Schematic(r'C:\Users\Zac\Desktop\Jordan_coding\PDF2Table\NC_modified.txt')
        # Parse input file to generate table as list of text
        schema.parse_file_to_text()
        # Produce an xlsxwriter-formatted Excel object
        schema.table_to_tsv()
        pass

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