import copy
import random
from itertools import permutations

import matplotlib.pyplot as plt
import numpy as np

from board import *
from factory import *
from player import *
from state import *
from tile import *


def place_and_score(board, line, col, verbose=False):
    colors = ["blue", "yellow", "red", "black", "lightblue"]
    color = colors[(col - line) % 5]
    stage = copy.deepcopy(Board.SG_AR)
    stage[line] = (stage[line][0], (stage[line][0], color))
    board = Board(board.score, board.wall, stage, 0, False)
    board = board.update_score()

    if verbose:
        print(boards_to_str([board]))
    return board


def go():
    # st = game_state()
    board = Board(0, Board.WALL, Board.SG_AR, 0, False)
    print(boards_to_str([board]))

    # board = board.place_move((0,2))
    # board = board.place_move((1,2))
    # board = board.place_move((2,2))
    # print(boards_to_str([board]))

    # stage = [(1, False), (2, (2, 'blue')), (3, False), (4, False), (5, False)]
    # board = Board(0, board.wall, stage, 0, False)
    # print(boards_to_str([board]))

    # board = board.update_score()
    # print(boards_to_str([board]))

    board = place_and_score(board, 0, 0)
    board = place_and_score(board, 1, 0)
    board = place_and_score(board, 2, 2)


def perm1(line_size):
    # All the possible ways to fill a line of size line_size
    spots = list(range(line_size))
    all_permutations = permutations(spots)

    perm = []
    # We need to create copies because the iteration consummes the iterator
    perm1 = copy.deepcopy(all_permutations)

    nb_boards = 0
    scores = []
    max_score = 0
    histories = {}
    for p1 in perm1:
        # print(p)
        board = Board(0, Board.WALL, Board.SG_AR, 0, False)

        for round in range(5):
            index = p1.index(round)
            board = place_and_score(board, 0, index)

        # print(boards_to_str([board]))
        nb_boards += 1
        scores.append(board.score)
        if not board.score in histories:
            histories[board.score] = []
        histories[board.score].append([p1])
        if board.score > max_score:
            max_score = board.score
    print(nb_boards)
    # sort scores
    scores = sorted(scores)
    print(scores)
    return scores, histories


def perm2(line_size):
    # The iteration consummes the iterator
    perm1 = list(permutations(list(range(line_size))))
    perm2 = list(permutations(list(range(line_size))))

    nb_boards = 0
    scores = []
    total_calls = len(perm1) * len(perm2)
    histories = {}
    for p1 in perm1:
        for p2 in perm2:
            board = Board(0, Board.WALL, Board.SG_AR, 0, False)
            for round in range(5):
                index1 = p1.index(round)
                board = place_and_score(board, 0, index1)
                index2 = p2.index(round)
                board = place_and_score(board, 1, index2)
            # print(boards_to_str([board]))
            nb_boards += 1
            scores.append(board.score)
            if not board.score in histories:
                histories[board.score] = []
            histories[board.score].append((p1, p2))
        print(f"completion: {nb_boards}/{total_calls}")
    print(nb_boards)
    # sort scores
    scores = sorted(scores)
    print(scores)
    return scores, histories


def perm3(line_size):
    # Best possible score is 70.
    # There are 230 ways of doing it out of 1 728 000, that's only 0.013% !
    # The iteration consummes the iterator
    perm1 = list(permutations(list(range(line_size))))
    perm2 = list(permutations(list(range(line_size))))
    perm3 = list(permutations(list(range(line_size))))

    nb_boards = 0
    scores = []
    total_calls = len(perm1) * len(perm2) * len(perm3)
    histories = {}
    for p1 in perm1:
        for p2 in perm2:
            for p3 in perm3:
                board = Board(0, Board.WALL, Board.SG_AR, 0, False)
                for round in range(5):
                    index1 = p1.index(round)
                    board = place_and_score(board, 0, index1)
                    index2 = p2.index(round)
                    board = place_and_score(board, 1, index2)
                    index3 = p3.index(round)
                    board = place_and_score(board, 2, index3)

                # print(boards_to_str([board]))
                nb_boards += 1
                scores.append(board.score)
                if not board.score in histories:
                    histories[board.score] = []
                histories[board.score].append((p1, p2, p3))
            print(f"completion: {nb_boards}/{total_calls}")
    print(nb_boards)
    # sort scores
    scores = sorted(scores)
    print(scores)
    return scores, histories


def plot_scores(scores, num_lines):
    bin_edges = np.arange(min(scores) - 0.5, max(scores) + 1.5, 1)

    plt.hist(scores, bins=bin_edges, edgecolor="black")
    plt.title(
        f"Frequency of Each Score when filling {num_lines} lines in Azul ({len(scores)} scores)"
    )
    plt.xlabel("Score")
    plt.ylabel("Frequency")
    plt.xticks(range(min(scores), max(scores) + 1))

    plt.show()


def two_line_test():
    board = Board(0, Board.WALL, Board.SG_AR, 0, False)
    print(boards_to_str([board]))
    for i in range(5):
        board = place_and_score(board, 0, i)
        board = place_and_score(board, 1, i)


def analyze_histories(histories):
    # find best score
    max_score = 0
    min_score = 100000
    nb_boards = 0
    for score in histories:
        nb_boards += len(histories[score])
        if score > max_score:
            max_score = score
        if score < min_score:
            min_score = score
    best_histories = histories[max_score]
    worst_histories = histories[min_score]
    print(
        f"All of the combinations that score the maximum score for {len(histories[max_score][0])} lines: {max_score} points"
    )
    print(
        f"There are {len(best_histories)} ways of doing it out of {nb_boards}, that's {len(best_histories)/nb_boards*100:.3f}%"
    )
    for history in best_histories:
        for line in history:
            print(line)
        print()

    print(
        f"All of the combinations that score the minimum score for {len(histories[min_score][0])} lines: {min_score} points"
    )
    print(
        f"There are {len(worst_histories)} ways of doing it out of {nb_boards}, that's {len(worst_histories)/nb_boards*100:.3f}%"
    )
    for history in worst_histories:
        for line in history:
            print(line)
        print()


def process_data(groups):
    processed_groups = set()
    for group in groups:
        processed_group = tuple(
            tuple("0" if num == 0 else "X" for num in row) for row in group
        )
        processed_groups.add(processed_group)
    return processed_groups


def read_data_from_file(file_path):
    with open(file_path, "r") as file:
        groups = []
        current_group = []
        for line in file:
            if line.startswith("("):  # Start of a new tuple
                current_group.append(tuple(map(int, line.strip("()\n").split(", "))))
            elif line.strip() == "" and current_group:  # Empty line, group is complete
                groups.append(tuple(current_group))
                current_group = []
        if current_group:  # Add the last group if file doesn't end with an empty line
            groups.append(tuple(current_group))
    return groups


def starting_positions():
    # Assuming your file content is stored in 'file_content'
    file_path = "../results/3_lines_worst_combinations.txt"
    file_path = "../results/3_lines_best_combinations.txt"
    data = read_data_from_file(file_path)
    unique_processed_data = process_data(data)

    # Print the processed data
    for group in unique_processed_data:
        for line in group:
            print(line)
        print()


## To test the overall behaviour of the library
# go()
# two_line_test()

## Brute force all the possibilities for 1 line
# scores, histories = perm1(5)
# plot_scores(scores, 1)
# analyze_histories(histories)

## Brute force all the possibilities for 2 lines
scores, histories = perm2(5)
plot_scores(scores, 2)
analyze_histories(histories)

## Brute force all the possibilities for 3 lines
# scores, histories = perm3(5)
# plot_scores(scores, 3)
# analyze_histories(histories)

## Analyze best and worst starting positions for 3 lines
# starting_positions()
