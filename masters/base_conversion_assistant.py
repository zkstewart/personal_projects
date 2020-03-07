# -*- coding: utf-8 -*-
"""
Created on Sat Mar  7 12:28:07 2020

@author: Zachary Stewart
"""

import argparse, pyperclip

class SimpleCalculator:
        def __init__(self, number1, operator, number2, is_decimal):
                if '.' in number1:
                        raise ValueError('Invalid input for class; number has decimal point')
                self.number1 = number1
                self.operator = operator
                self.number2 = number2
                self.is_decimal = is_decimal
        
        def calculate(self):
                result = []
                carry = 0
                for i in range(len(self.number1)-1, -1, -1):
                        letter = self.number1[i]
                        calc = eval(letter + self.operator + self.number2) + carry
                        if calc >= 10:
                                carry = 1
                                calc -= 10
                        else:
                                carry = 0
                        result.insert(0, str(calc))
                        if i == 0 and carry == 1:
                                result.insert(0, '1')
                if self.is_decimal:
                        result.insert(-len(self.number1), '.')
                result = ''.join(result)
                if result.startswith('.'):
                        result = '0' + result
                return result

class Conversion:
        def __init__(self, number, from_base, to_base):
                self.number = float(number)
                self.from_base = int(from_base)
                self.to_base = int(to_base)
                self.whole_equations = []
                self.fractional_equations = []
        
        def base_converter(self):
                ARBITRARY_CUTOFF = 50000
                ARBITRARY_DECIMAL_REPRESENT = 100
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
                        fractional = str(self.number).split('.')[1]
                        frac_equations_exist = False
                        if float(fractional) != 0.0:
                                frac_equations_exist = True
                                fractional_digits = ''
                                fractional_equations = []
                                while True:
                                        calc = SimpleCalculator(fractional, '*', '2', True).calculate()
                                        multiplication = '0.' + calc.split('.')[1]
                                        remainder = calc.split('.')[0]
                                        equation = fractional + ' * ' + str(self.to_base) + ' = ' + multiplication + '\t' + remainder
                                        fractional_equations.append(equation)
                                        fractional = calc.split('.')[1]
                                        fractional_digits += remainder
                                        if set(fractional) == {'0'}:
                                                break
                                        elif len(fractional_equations) > ARBITRARY_CUTOFF:
                                                print('This number probably produces an infinite binary fraction; aborting program run and truncating results.')
                                                break
                        # Join parts
                        if frac_equations_exist:
                                if len(fractional_equations) < ARBITRARY_CUTOFF:
                                        self.converted_number = ''.join(whole_digits) + '.' +  fractional_digits
                                else:
                                        self.converted_number = ''.join(whole_digits) + '.' +  fractional_digits[0: ARBITRARY_DECIMAL_REPRESENT] + ' ...'
                                        
                        else:
                                self.converted_number = ''.join(whole_digits)
                        self.whole_equations = whole_equations
                        if frac_equations_exist:
                                self.fractional_equations = fractional_equations[0: ARBITRARY_DECIMAL_REPRESENT]
        
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
        and the result as output. It will try to abort infinite calculations.
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
