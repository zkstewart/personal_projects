# -*- coding: utf-8 -*-
"""
Created on Sat Mar  7 17:08:53 2020

@author: Zachary Stewart
"""

import argparse

class WordCode:
        def __init__(self, word):
                self.word = word
        
        def convert(self, code_type):
                output = []
                for letter in self.word:
                        char_code = CharacterCode(letter).convert(code_type)
                        if code_type == 'bin':
                                output.append('0' + str(char_code)[2:].upper()) # Binary characters have a 0 prefix to make them 8 bits
                        elif code_type == 'dec':
                                output.append(str(char_code).upper()) # Decimals don't have a format string pefix
                        elif code_type == 'oct' and len(char_code) < 5:
                                output.append('0' + str(char_code)[2:].upper()) # Octal characters are represented in 3 digits
                        else:
                                output.append(str(char_code)[2:].upper()) # This strips the Python format string
                return output

class CharacterCode:
        def __init__(self, character):
                if len(character) != 1:
                        raise ValueError(character + ' is not a string of length 1')
                self.character = character
        
        def convert(self, code_type):
                ACCEPTED_CODES = ['bin', 'oct', 'dec', 'hex']
                assert code_type in ACCEPTED_CODES
                # Convert character code to decimal
                dec_code = ord(self.character)
                # Convert decimal to relevant output type
                if code_type == 'hex':
                        return hex(dec_code)
                elif code_type == 'oct':
                        return oct(dec_code)
                elif code_type == 'bin':
                        return bin(dec_code)
                elif code_type == 'dec':
                        return dec_code

def main():
        def validate_args(args):
                # Validate that arguments were provided
                for key, value in vars(args).items():
                        if value == None and key != 'output':
                                raise Exception(key + ' arg was not provided; fix and try again.')
        
        usage = '''%(prog)s will convert letter(s) into their binary representations
        in the specified number system.
        '''
        p = argparse.ArgumentParser(description=usage)
        p.add_argument('-w', dest='word',
                       help='''
                       Provide a word (or a single letter) to convert to a 
                       ''')
        p.add_argument('-b', dest='base_number', choices=['bin','oct','dec','hex'],
                       help='''
                       Specify the base number to represent the binary code in
                       ''')
        
        args = p.parse_args()
        validate_args(args)
        
        # Convert word to character codes using WordCode class
        word_obj = WordCode(args.word)
        word_code = word_obj.convert(args.base_number)
        print(' '.join(word_code))

if __name__ == '__main__':
        main()
