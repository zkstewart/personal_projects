# -*- coding: utf-8 -*-
"""
Created on Sat Mar  7 12:28:07 2020

@author: Zachary Stewart
"""

import argparse, pyperclip

class Conversion:
        def __init__(self, number, from_base, to_base):
                self.number = float(number)
                self.from_base = int(from_base)
                self.to_base = int(to_base)
                self.whole_equations = []
                self.fractional_equations = []
        
        def base_converter(self):
                # Decimal conversion
                if self.from_base == 10:
                        # Whole part
                        whole = int(self.number)
                        whole_digits = []
                        whole_equations = []
                        while True:
                                division = int(whole / self.to_base)
                                remainder = whole % self.to_base
                                equation = str(whole) + ' / ' + str(self.to_base) + ' = ' + str(division) + '\t' + str(remainder)
                                whole_equations.append(equation)
                                whole = division
                                whole_digits.insert(0, str(remainder))
                                if whole == 0:
                                        break
                        # Fractional part
                        fractional = self.number - int(self.number)
                        frac_equations_exist = False
                        fractional_length = len(str(self.number).split('.')[1])
                        if fractional != 0.0:
                                frac_equations_exist = True
                                fractional_digits = ''
                                fractional_equations = []
                                while True:
                                        remainder = int(fractional * self.to_base)
                                        multiplication = (fractional * self.to_base) - remainder
                                        equation = str(round(fractional, fractional_length)) + ' * ' + str(self.to_base) + ' = ' + str(round(multiplication, fractional_length)) + '\t' + str(remainder)
                                        fractional_equations.append(equation)
                                        fractional = multiplication
                                        fractional_digits += str(remainder)
                                        if fractional == 0.0:
                                                break
                        # Join parts
                        self.converted_number = ''.join(whole_digits) + '.' +  fractional_digits
                        self.whole_equations = whole_equations
                        if frac_equations_exist == True:
                                self.fractional_equations = fractional_equations
        
        def print_results(self):
                print(str(self.number) + ' = ' + str(self.converted_number) + ' (base ' + str(self.to_base) + ')\n')
                
                for i in range(len(self.whole_equations)):
                        if i == 0:
                                print('Division\tRemainder')
                        print(self.whole_equations[i])
                
                for i in range(len(self.fractional_equations)):
                        if i == 0:
                                print('Multiplication\tRemainder')
                        print(self.fractional_equations[i])
        
        def equations_to_clipboard(self):
                clipboard_list = []
                for i in range(len(self.whole_equations)):
                        if i == 0:
                                clipboard_list.append('Division\tRemainder')
                        clipboard_list.append(self.whole_equations[i])
                
                for i in range(len(self.fractional_equations)):
                        if i == 0:
                                clipboard_list.append('Multiplication\tRemainder')
                        clipboard_list.append(self.fractional_equations[i])
                pyperclip.copy('\n'.join(clipboard_list))

def main():
        def validate_args(args):
                # Validate that arguments were provided
                for key, value in vars(args).items():
                        if value == None and key != 'output':
                                raise Exception(key + ' arg was not provided; fix and try again.')
        
        usage = '''%(prog)s will (currently) convert decimal numbers to other
        base systems using the division method, producing formatted equations
        and the result as output.
        '''
        p = argparse.ArgumentParser(description=usage)
        p.add_argument('-n', dest='number', type=float,
                       help='''
                       Provide a number to convert to another base [assumed to be base10 currently]
                       ''')
        p.add_argument('-c', dest='conversion_base',
                       help='''
                       Specify the base to convert to [handles any base]
                       ''')
        args = p.parse_args()
        validate_args(args)
        
        # Convert number using Conversion class
        num = Conversion(args.number, 10, args.conversion_base) # Note that 10 is hard-coded; program only works with base10 currently
        num.base_converter()
        num.print_results()
        num.equations_to_clipboard()

if __name__ == '__main__':
        main()
                        