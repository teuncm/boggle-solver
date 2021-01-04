#!/usr/bin/env python3
#
# Author: Teun Mathijssen
# Description:
# This program aims to simulate 'Boggle'. It requires Python3.6+ to run.
# Further information can be found on https://github.com/teuncm/boggle-solver
import argparse
import random
import string
import itertools

DICE_LIST = 'dice.dat'
NUM_DICE = 16
NUM_DICE_FACES = 6

class clr:
    """Colors to be used for printing."""
    R = '\033[41m'
    B = '\033[44m'
    RST = '\033[0m'


def get_letter(board, cell):
    """Retrieve letter at cell's position."""
    return board[cell[0]][cell[1]]

def get_points(word):
    """Assign a Boggle point score to a word."""
    if len(word) <= 4:
        return 1
    elif len(word) == 5:
        return 2
    elif len(word) == 6:
        return 3
    elif len(word) == 7:
        return 5
    elif len(word) >= 8:
        return 11

def get_score(words):
    """Get the total score for this game."""
    score = 0
    for word in words:
        score += get_points(word)

    return score

def get_valid_neighbors(args, board, cur_path):
    """Retrieve all valid neighbor cell indices."""
    if args.neighbors == 'all':
        offsets = [(-1, 0), (0, -1), (1, 0), (0, 1),
                   (-1, -1), (-1, 1), (1, 1), (1, -1)]
    elif args.neighbors == 'no_diag':
        offsets = [(-1, 0), (0, -1), (1, 0), (0, 1)]

    cur_cell = cur_path[-1]

    valid_neighbor_cells = []
    for offset in offsets:
        neighbor_cell = (cur_cell[0] + offset[0], cur_cell[1] + offset[1])

        # A neighbor cell is valid if it is within bounds
        # and if it has not been used in the current word path so far.
        if (neighbor_cell[0] >= 0 and neighbor_cell[0] < len(board)
                and neighbor_cell[1] >= 0 and neighbor_cell[1] < len(board)
                and neighbor_cell not in cur_path):
            valid_neighbor_cells.append(neighbor_cell)

    return valid_neighbor_cells

def construct_lookup(args):
    """Construct lookup dictionaries."""
    num_letters = args.size*args.size

    # All words.
    words_dict = set()
    # All words truncated to the n-th character.
    words_trunc_dict = set()
    with open(args.wordlist) as file:
        for line in file:
            cur_word = line.rstrip()
            words_dict.add(cur_word)

            for i in range(1, num_letters+1):
                    words_trunc_dict.add(cur_word[:i])

    return words_dict, words_trunc_dict

def construct_dice():
    """Read dice from the provided dice file."""
    dice = []
    with open(DICE_LIST) as file:
        for line in file:
            dice.append(list(line.rstrip().lower()))

    return dice

def construct_board(args):
    """Construct the Boggle board."""
    board_size = args.size
    num_letters = args.size*args.size

    board = []
    if args.board:
        # Construct board from input.
        last_size = None
        for row in args.board:
            if last_size is not None and len(row) != last_size:
                exit('Error reading board: board must be square')

            board.append(list(row.lower()))
            last_size = len(row)
    else:
        if args.gen == 'random':
            # Construct board randomly.
            abc = string.ascii_lowercase
            letters = random.choices(abc, k=num_letters)

        elif args.gen == 'dice':
            # Construct board by throwing game dice.
            dice = construct_dice()

            # Pick with or without replacement.
            if num_letters <= NUM_DICE:
                positions = random.sample(range(NUM_DICE), k=num_letters)
            else:
                positions = random.choices(range(NUM_DICE), k=num_letters)

            faces = random.choices(range(NUM_DICE_FACES), k=num_letters)
            letters = [dice[positions[i]][faces[i]] for i in range(num_letters)]

        for i in range(board_size):
            row = letters[i*board_size:(i+1)*board_size]
            board.append(row)

    return board

def print_board(board, copy=False):
    """Print the board, optionally as copyable string."""
    for i in range(len(board)):
        if copy:
            print(''.join(board[i]).upper(), end=' ')
        else:
            print(' '.join(board[i]).upper())

    if copy:
        print()

    print()

def print_path(board, path, word):
    """Print given path on the board as highlighted ASCII characters."""
    for i in range(len(board)):
        for j in range(len(board)):
            if (i, j) == path[0]:
                # Highlight starting character differently.
                print(f'{clr.R}{board[i][j].upper()}{clr.RST}', end='')
            elif (i, j) in path:
                print(f'{clr.B}{board[i][j].upper()}{clr.RST}', end='')
            else:
                print(f'{board[i][j].upper()}', end='')

            print(' ', end='')

        print()

def print_score(sorted_words):
    """Print the overall game score."""
    print(f'{len(sorted_words)} word(s), {get_score(sorted_words)} point(s)!')
    print('-'*25)

def print_found_words(args, board, found_words_paths, sorted_words):
    """Print all found words."""
    for word in sorted_words:
        print(f'{word} - {get_points(word)}')

        if args.display == 'fancy':
            print_path(board, found_words_paths[word], word)
            print()

    if args.display == 'plain':
        print()

def sort_words(args, found_words_paths):
    """Sort the found words."""
    if args.sort == 'abc':
        sorted_words = sorted(list(found_words_paths))
    elif args.sort == 'size':
        sorted_words = sorted(sorted(list(found_words_paths)), key=lambda x: len(x))
    elif args.sort == 'none':
        sorted_words = list(found_words_paths)

    return sorted_words

def solve_board(args, board, words_dict, words_trunc_dict):
    """Find all words on the board that are in the dictionary by DFS."""
    # Each level of the stack contains possible options for the letter
    # at that position in the word.
    to_explore_stack = []
    init_cells = list(itertools.product(range(len(board)), range(len(board))))
    to_explore_stack.append(init_cells)

    # Store all found words and their paths.
    found_words_paths = {}
    # Store the word path for found words.
    cur_path = [None]
    # Allows us to easily construct the current word at any point in time.
    cur_letters = [None]
    while to_explore_stack:
        # Obtain the deepest exploration level so far.
        cur_cells = to_explore_stack[-1]

        # Backtrack if there are no more options to explore at this depth.
        if not cur_cells:
            to_explore_stack.pop()
            cur_path.pop()
            cur_letters.pop()
            continue

        # Get the first cell at this exploration depth.
        cur_cell = cur_cells.pop()
        cur_path[-1] = cur_cell
        cur_letters[-1] = get_letter(board, cur_cell)

        # Check whether we should continue searching from this cell's letter.
        cur_word = ''.join(cur_letters)
        if cur_word not in words_trunc_dict:
            continue
        elif cur_word in words_dict:
            found_words_paths[cur_word] = list(cur_path)

        # Get all cells for next exploration depth.
        neighbor_cells = get_valid_neighbors(args, board, cur_path)
        if neighbor_cells:
            to_explore_stack.append(neighbor_cells)
            cur_path.append(None)
            cur_letters.append(None)

    return found_words_paths

def main(args):
    board = construct_board(args)
    words_dict, words_trunc_dict = construct_lookup(args)

    found_words_paths = solve_board(args, board, words_dict, words_trunc_dict)
    sorted_words = sort_words(args, found_words_paths)

    # Print results.
    print()

    print("Board: ", end='')
    print_board(board, copy=True)
    print_board(board)

    print_score(sorted_words)
    print_found_words(args, board, found_words_paths, sorted_words)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--size', type=int, default=4, help='Board size.')
    parser.add_argument('--board', type=str, nargs='+', help='Board rows, space-separated, overrides board size. Generate random board if not given.')
    parser.add_argument('--wordlist', type=str, default='list_filtered.txt', help='Wordlist file.')
    parser.add_argument('--sort', type=str, default='size',
                        choices=['abc', 'size', 'none'], help='Sorting method for the found words.')
    parser.add_argument('--display', type=str, default='fancy',
                        choices=['plain', 'fancy'], help='Display method for the found words.')
    parser.add_argument('--neighbors', type=str, default='all',
                        choices=['all', 'no_diag'], help='Neighbors to use when searching.')
    parser.add_argument('--gen', type=str, default='dice',
                        choices=['dice', 'random'], help='Whether to use game dice or randomly generated letters.')

    main(parser.parse_args())
