#! python3
# snake_game.py
# Python implementation of a snake game that can theoretically be ported
# to arduino/C++ for dot matrix display.
'''This will include three major functions

1: A self-contained snake game that can operate on any 2D size

2: A module to receive inputs from an analog stick controller and convert them 
to simply left/right/up/down controls

3: A module to output the snake game state to dot matrix display
'''

# Import modules
import random, time, copy

# Test scenarios (for debugging, can delete later)
def tests():
        ## COLLISION BEHAVIOUR TEST 1
        snake_game_state = \
        ['00100000',
         '00200000',
         '00100000',
         '00100000',
         '00100000',
         '00100000',
         '00100000',
         '00100000',
         '00100000']
        new_coord = [2,1]
        snake_coords = [[2,2],[2,3],[2,4],[2,5],[2,6],[2,7],[2,8],[2,0]]
        snake_row_counts = [1, 0, 1, 1, 1, 1, 1, 1, 1]
        extend_snake_next = False
        food_present = True
        snake_game_state, snake_coords, snake_row_counts, extend_snake_next, collision, food_present = snake_movement_handling(snake_game_state, new_coord, snake_coords, snake_row_counts, extend_snake_next)
        '''Outcome: snake moves up to eat the food, and the old tail position moves'''
        new_coord = [2,0]
        snake_game_state, snake_coords, snake_row_counts, extend_snake_next, collision, food_present = snake_movement_handling(snake_game_state, new_coord, snake_coords, snake_row_counts, extend_snake_next)
        '''Outcome: snake extends after eating the food (tail does not move) and is now forming a full column after head movement'''
        new_coord = [2,8]
        snake_game_state, snake_coords, snake_row_counts, extend_snake_next, collision, food_present = snake_movement_handling(snake_game_state, new_coord, snake_coords, snake_row_counts, extend_snake_next)
        '''Outcome: snake follows its own tail without eating it. Verdict: Success!'''
        ## EATING BEHAVIOUR TEST 1
        snake_game_state = \
        ['00000000',
         '00200000',
         '00100000',
         '00100000',
         '00100000',
         '00100000',
         '00100000',
         '00100000',
         '00100000']
        new_coord = [2,1]
        snake_coords = [[2,2],[2,3],[2,4],[2,5],[2,6],[2,7],[2,8]]
        snake_row_counts = [0, 0, 1, 1, 1, 1, 1, 1, 1]
        extend_snake_next = False
        food_present = True
        snake_game_state, snake_coords, snake_row_counts, extend_snake_next, collision, food_present = snake_movement_handling(snake_game_state, new_coord, snake_coords, snake_row_counts, extend_snake_next)
        '''Outcome: snake moves up to eat the food, and the old tail position moves'''
        snake_game_state = \
        ['00200000',
         '00100000',
         '00100000',
         '00100000',
         '00100000',
         '00100000',
         '00100000',
         '00100000',
         '00000000'] # Simulate the food being placed in front of the new head position
        new_coord = [2,0]
        snake_game_state, snake_coords, snake_row_counts, extend_snake_next, collision, food_present = snake_movement_handling(snake_game_state, new_coord, snake_coords, snake_row_counts, extend_snake_next)
        '''Outcome: snake moves up to eat the food, and the snake extends simultaneously (tail does not move)'''
        snake_game_state = \
        ['00100000',
         '00100000',
         '00100000',
         '00100000',
         '00100000',
         '00100000',
         '00100000',
         '00100000',
         '00200000'] # Simulate the food being placed beind the tail / at the soon-to-be new head position
        new_coord = [2,8]
        snake_game_state, snake_coords, snake_row_counts, extend_snake_next, collision, food_present = snake_movement_handling(snake_game_state, new_coord, snake_coords, snake_row_counts, extend_snake_next)
        '''Outcome: same as before, and now we have a full column occupied by the snake. Verdict: Success!'''
        ## MOVING RIGHT AND LEFT TEST 1
        snake_game_state = \
        ['00100000',
         '00000000',
         '00102000',
         '00100000',
         '00100000',
         '00100000',
         '00100000',
         '00100000',
         '00100000']
        new_coord = [3,2]
        snake_coords = [[2,2],[2,3],[2,4],[2,5],[2,6],[2,7],[2,8],[2,0]]
        snake_row_counts = [1, 0, 1, 1, 1, 1, 1, 1, 1]
        extend_snake_next = False
        food_present = True
        snake_game_state, snake_coords, snake_row_counts, extend_snake_next, collision, food_present = snake_movement_handling(snake_game_state, new_coord, snake_coords, snake_row_counts, extend_snake_next)
        '''Outcome: snake moves to the right, and the old tail position moves'''
        new_coord = [4,2]
        snake_game_state, snake_coords, snake_row_counts, extend_snake_next, collision, food_present = snake_movement_handling(snake_game_state, new_coord, snake_coords, snake_row_counts, extend_snake_next)
        '''Outcome: snake moves to the right and eats the food, and the old tail position moves'''
        new_coord = [5,2]
        snake_game_state, snake_coords, snake_row_counts, extend_snake_next, collision, food_present = snake_movement_handling(snake_game_state, new_coord, snake_coords, snake_row_counts, extend_snake_next)
        '''Outcome: snake extends in the right direction (tail does not move). Verdict: Success!'''
        ## EDGE WRAPPING TEST 1
        

# Game-essential functions
def find_centre_of_grid(x_size, y_size):
        '''Simple function to find the central (or most-central with left/down
        offset) position in a grid
        '''
        x_centre = int((x_size / 2) + 0.5) # Add 0.5 to round up for odd numbers, even numbers are already left offset
        y_centre = int(y_size / 2) + ((int(y_size / 2) - y_size / 2) != 0) # This rounds up, which results in down offset
        return [x_centre-1, y_centre-1] # We'll be using these numbers in a 0-indexed way

def determine_food_location(snake_game_state, snake_row_counts, x_size, y_size):
        # Figure out how many positions are not occupied by a snake
        grid_size = x_size * y_size
        snake_size = sum(snake_row_counts)
        available_spaces = grid_size - snake_size
        # Generate a random number within the range of available spaces
        food_num = random.sample(range(0, available_spaces), 1)[0]
        # Identify which row this number refers to
        cumulative_nonsnake_count = 0
        for i in range(len(snake_row_counts)):
                '''We work with a temp value since we need to see what our cumulative 
                count WOULD be by the end of the row, but we still need what it
                CURRENTLY is for the row scanning below'''
                temp_cumulative_nonsnake_count = cumulative_nonsnake_count + x_size - snake_row_counts[i]
                # Skip if we have not reached the row which we may put a food into
                if temp_cumulative_nonsnake_count < food_num:
                        cumulative_nonsnake_count += x_size - snake_row_counts[i]
                        continue
                # Skip if there is not a blank position in this row
                if snake_row_counts[i] == x_size:
                        continue
                '''If we reach here, this is the row to put the food into'''
                # Scan through row to find the position that will become food
                for position in range(x_size):
                        if cumulative_nonsnake_count < food_num:
                                if snake_game_state[i][position] == '0':
                                        cumulative_nonsnake_count += 1
                                continue
                        elif cumulative_nonsnake_count >= food_num:
                                if snake_game_state[i][position] == '0':
                                        snake_game_state[i] = snake_game_state[i][0:position] + '2' + snake_game_state[i][position+1:]
                                        return snake_game_state, [position, i] # [x, y] equivalent
        # Debugging
        return False

def coordinate_edge_wrap(coord_number, number_modifier, coord_maximum):
        '''coord_number will be either the x or y coordinate value
        number_modifier will be a +1 or -1 value
        coord_maximum refers to the corresponding x or y coordinate max value
        '''
        # Handle wrapping around top/left edge
        if coord_number == 0 and number_modifier == -1:
                return coord_maximum
        # Handle wrapping around bottom/right bottom edge
        elif coord_number == coord_maximum and number_modifier == 1:
                return 0
        # Handle non-wrapping numbers
        else:
                return coord_number + number_modifier

def snake_movement_handling(snake_game_state, new_coord, snake_coords, snake_row_counts, extend_snake_next):
        '''In all cases, our snake head always moves in the direction specified.
        
        In cases where it's a food space, we'll raise the extend_snake_next flag
        which will prevent us from deleting the tail on the NEXT time we enter
        this function. This gives us the "correct" snake game behaviour of the
        snake elongating after it eats the food, rather than extending to meet
        the food.
        
        In cases where it's a snake space, we'll raise the collision flag which
        will result in a later game over screen.
        '''
        # Produce flags for later behaviour handling
        collision = False
        temp_extend_snake_next = False
        food_present = True
        if snake_game_state[new_coord[1]][new_coord[0]] == '2':
                '''We need to use a temporary value since we don't want to overwrite
                the flag we received from outside this function. We need to raise
                flags now since we're going to change the snake_game_state and
                need to check for events before that happens.
                '''
                temp_extend_snake_next = True
                food_present = False
        elif snake_game_state[new_coord[1]][new_coord[0]] == '1':
                '''It doesn't count as a collision if it's the snake's previous
                tail and the tail isn't being extended on this turn
                '''
                if new_coord != snake_coords[-1] and extend_snake_next == False:
                        collision = True
        # Update game state
        '''We need to delete the tail before writing the head so that, in cases
        where the snake is chasing itself, the ordering does not result in us
        writing the new head/old tail position as a 0 incorrectly
        '''
        if extend_snake_next == False:
                snake_game_state[snake_coords[-1][1]] = snake_game_state[snake_coords[-1][1]][0:snake_coords[-1][0]] + '0' + snake_game_state[snake_coords[-1][1]][snake_coords[-1][0]+1:]
        snake_game_state[new_coord[1]] = snake_game_state[new_coord[1]][0:new_coord[0]] + '1' + snake_game_state[new_coord[1]][new_coord[0]+1:]
        # Update row counts list
        snake_row_counts[new_coord[1]] += 1
        if extend_snake_next == False:
                snake_row_counts[snake_coords[-1][1]] -= 1
        # Update snake coordinate list
        snake_coords.insert(0, new_coord)
        if extend_snake_next == False:
                snake_coords.pop()
        return snake_game_state, snake_coords, snake_row_counts, temp_extend_snake_next, collision, food_present

def snake_game_setup(x_size, y_size):
        # Generate a blank snake game state
        '''The snake game state is being saved as a grid where 0 = empty space,
        1 = snake is here, and 2 = food is here. Storing this as a list of strings
        makes it easy to take this game state and make it presentable on a 
        dot matrix display (which is the purpose of this coding projefct), but 
        it should also be simple to convert it to any other format.
        '''
        snake_game_state = ['0' * x_size] * y_size
        # Populate game state with snake beginning in central position
        snake_start_coord = find_centre_of_grid(x_size, y_size)
        snake_game_state[snake_start_coord[1]] = snake_game_state[snake_start_coord[1]][0:snake_start_coord[0]] + \
        '1' + snake_game_state[snake_start_coord[1]][snake_start_coord[0] + 1:]
        # Generate value to track snake body coordinates
        '''Tracking head position is necessary to determine where the next head
        position will be depending on the direction input, and tracking the last
        tail position is necessary for deleting this position whenever the snake
        moves. In order to track both, we need to track the whole snake body.
        '''
        snake_coords = [snake_start_coord]
        # Generate list to track the amount of values in a row that are snake positions
        '''This will help to reduce the complexity of randomly finding a position
        that is not currently occupied without needing to reroll random numbers
        or scan every row each time we want to place a food somewhere.
        '''
        snake_row_counts = [0] * y_size
        snake_row_counts[snake_start_coord[1]] += 1
        # Return our established snake game for iterative game looping
        return snake_game_state, snake_coords, snake_row_counts

def snake_game(controller_func, output_disp_func, x_size, y_size, game_update_speed):
        # Fresh game values
        food_present = False
        previous_direction = None
        extend_snake_next = False
        collision = False
        game_won = False
        restart = True
        # Core game loop
        while True:
                # Set up the snake game
                if restart == True:
                        snake_game_state, snake_coords, snake_row_counts = snake_game_setup(x_size, y_size)
                        snake_game_state, food_coord = determine_food_location(snake_game_state, snake_row_counts, x_size, y_size)
                        food_game_state, flicker_game_state = convert_state_for_display(snake_game_state, food_coord, 'normal')
                        food_present = True
                        restart = False
                # Display the current game state
                output_disp_func(food_game_state)
                # Retrieve controller inputs
                '''Game does not start until a direction is received'''
                if previous_direction == None:
                        controller_direction = controller_func(wait_for_controller=True)
                else:
                        controller_direction = controller_func(input_time_period=game_update_speed, wait_for_controller=False)
                # Determine the snake's direction based upon controller input
                if controller_direction == None:
                        current_direction = previous_direction
                else:
                        current_direction = controller_direction
                # Exclude incompatible direction inputs
                '''The snake cannot turn around upon itself'''
                if current_direction == 'up' and previous_direction == 'down':
                        current_direction = 'down'
                elif current_direction == 'down' and previous_direction == 'up':
                        current_direction = 'up'
                elif current_direction == 'left' and previous_direction == 'right':
                        current_direction = 'right'
                elif current_direction == 'right' and previous_direction == 'left':
                        current_direction = 'left'
                # Store our previous direction for the next loop
                previous_direction = current_direction
                # Based upon the direction of input, calculate the next head coordinate
                if current_direction == 'up':
                        new_coord = [snake_coords[0][0], coordinate_edge_wrap(snake_coords[0][1], -1, y_size)]
                elif current_direction == 'down':
                        new_coord = [snake_coords[0][0], coordinate_edge_wrap(snake_coords[0][1], 1, y_size)]
                elif current_direction == 'left':
                        new_coord = [coordinate_edge_wrap(snake_coords[0][0], -1, x_size), snake_coords[0][1]]
                elif current_direction == 'right':
                        new_coord = [coordinate_edge_wrap(snake_coords[0][0], 1, x_size), snake_coords[0][1]]
                # Check new snake head coordinate for collision or food conditions and update game conditions
                snake_game_state, snake_coords, snake_row_counts, extend_snake_next, collision, food_present = snake_movement_handling(snake_game_state, new_coord, snake_coords, snake_row_counts, extend_snake_next)
                # Game win condition
                '''If all positions are occupied by the snake, the user has won!
                '''
                if sum(snake_row_counts) == x_size * y_size:
                        game_won = True # yay!
                # Obtain game states for display
                '''Two game states are obtained which will be flickered between
                to provide information on game events i.e., collision or winning
                '''
                        # Mode 1; normal
                if collision == False and game_won == False:
                        food_game_state, flicker_game_state = convert_state_for_display(snake_game_state, food_coord, 'normal')
                        # Mode 2; collision
                elif collision == True:
                        '''The snake head will always be where the collision occurred.'''
                        food_game_state, flicker_game_state = convert_state_for_display(snake_game_state, food_coord, 'collision', snake_coords[0])
                        restart = True
                        # Mode 3; win
                elif game_won == True:
                        food_game_state, flicker_game_state = convert_state_for_display(snake_game_state, food_coord, 'win')
                # Flicker game state under collision or game win conditions
                if collision == True or game_won == True:
                        for count in range(3):
                                output_disp_func(food_game_state)
                                time.sleep(1)
                                output_disp_func(flicker_game_state)
                                time.sleep(0.5)
                # Flicker game state under normal conditions
                else:
                        output_disp_func(flicker_game_state)
                        time.sleep(0.5)
                # Identify food position if relevant before loop begins again
                if food_present == False:
                        snake_game_state, food_coord = determine_food_location(snake_game_state, snake_row_counts, x_size, y_size)
                        food_present = True

# Input/output-related functions
def controller_func():
        '''TBD: Function cannot be written without testing the actual input device...
        consider looking into how to connect it to receive in Windows/Python.
        https://stackoverflow.com/questions/24214643/python-to-automatically-select-serial-ports-for-arduino
        '''
        this_is_incomplete = True

def keyboard_controller_func(wait_for_controller, input_time_period=1):
        '''Imports are internal since this function is not designed to be ported
        to the final product. input_time_period is assumed to be provided in seconds.
        A default is indicated in this function so that it needn't be specified
        when wait_for_controller == True.
        '''
        import keyboard
        direction = None
        # Determine the time at which this loop will terminate
        start_time = time.time()
        if wait_for_controller == False:
                end_time = start_time + input_time_period
        else:
                end_time = None
        # Begin loop, checking for keyboard input
        while True:
                # Brief pause to prevent CPU burden
                time.sleep(0.125)
                # Exit condition
                if wait_for_controller == False:
                        if time.time() >= end_time:
                                break
                else:
                        if direction != None:
                                break
                # Check for key presses
                if keyboard.is_pressed('right'):
                        direction = 'right'
                elif keyboard.is_pressed('left'):
                        direction = 'left'
                elif keyboard.is_pressed('up'):
                        direction = 'up'
                elif keyboard.is_pressed('down'):
                        direction = 'down'
        return direction

def convert_state_for_display(snake_game_state, food_coord, conversion_mode, collision_coord=None):
        '''This function needs to render a game state where only 0's and 1's are
        present; thus, the food position needs to be turned from a 2 to a 1
        (1 means "light up this space/dot", 2 means "don't light this up").
        The rest of the state is handled according to certain "modes" depending
        on what event occured.
        
        Mode 1 = normal display; the snake will flicker on/off
        Mode 2 = collision display; the point of collision will flicker on/off
        Mode 3 = game win display; the entire board will flicker on/off
        '''
        # Ensure that inputs are sensible
        if conversion_mode == 'collision':
                assert collision_coord != None
        # Replace food (2) with 1 in snake_game_state
        '''I call it food_game_state since it's not the true game, it's a version
        of the game where the food is altered from its base conditions. In cases
        where the food was eaten on the turn that this will display, then the line
        two down won't have any impact on the actual game.
        '''
        food_game_state = copy.deepcopy(snake_game_state)
        food_game_state[food_coord[1]] = snake_game_state[food_coord[1]][0:food_coord[0]] + '1' + snake_game_state[food_coord[1]][food_coord[0]+1:]
        # Derive x_size and y_size naturally
        '''I think it's more intuitive to handle functions like this by just
        giving it the game state without worrying about providing it the x and y
        dimensions; we can derive this efficiently anyway.
        '''
        x_size = len(snake_game_state[0])
        y_size = len(snake_game_state)
        # Mode 1; normal
        if conversion_mode == 'normal':
                flicker_game_state = ['0' * x_size] * y_size
                flicker_game_state[food_coord[1]] = flicker_game_state[food_coord[1]][0:food_coord[0]] + '1' + flicker_game_state[food_coord[1]][food_coord[0]+1:]
        # Mode 2; collision
        elif conversion_mode == 'collision':
                flicker_game_state = copy.deepcopy(food_game_state)
                flicker_game_state[collision_coord[1]] = flicker_game_state[collision_coord[1]][0:collision_coord[0]] + '0' + flicker_game_state[collision_coord[1]][collision_coord[0]+1:]
        # Mode 3; win
        elif conversion_mode == 'win':
                food_game_state = ['0' * x_size] * y_size
                flicker_game_state = ['1' * x_size] * y_size
        return food_game_state, flicker_game_state

def console_display_func(game_state):
        import curses
        '''As with keyboard_controller_func, this function is not intended to be
        ported to the final product and thus packages have been imported here.
        
        This function will (as of now) simply display the grid of 0's and 1's
        as found in the game state to a Windows console, but I may modify it to
        be more "graphical" in the future.
        '''
        # Init curses screen for display
        global CURSES_SCREEN_INIT_STATUS, CURSES_SCREEN
        try:
                assert CURSES_SCREEN_INIT_STATUS
        except:
                CURSES_SCREEN = curses.initscr()
                curses.noecho()
                curses.cbreak() # test if this produces the wanted behaviour
                CURSES_SCREEN_INIT_STATUS = 1
        # Clear previous screen contents
        CURSES_SCREEN.clear()
        # Write game_state to screen
        for row in game_state:
                CURSES_SCREEN.addstr(row + '\n')
        CURSES_SCREEN.refresh()
        
def dotmatrix_display_func(snake_game_state):
        this_is_incomplete = True

# Main call
def main():
        # Hard-coded values for basic game operation
        '''More sophisticated option specification can come later, and it depends
        on the platform and way in which this program is being run.'''
        x_size = 8
        y_size = 8
        game_update_speed = 1
        # Start main game loop
        snake_game(keyboard_controller_func, console_display_func, x_size, y_size, game_update_speed)

if __name__ == '__main__':
        main()