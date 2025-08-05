import typing

def print_board(board: list[list[int]]) -> None:
    """
    Prints the Sudoku board in a formatted way.

    Args:
        board (list[list[int]]): The 9x9 Sudoku board.
    """
    for i in range(len(board)):
        # Print horizontal separator after every 3 rows (except the first)
        if i % 3 == 0 and i != 0:
            print("- - - - - - - - - - - - - ")

        for j in range(len(board[0])):
            # Print vertical separator after every 3 columns (except the last)
            if j % 3 == 0 and j != 0:
                print(" | ", end="")

            # Print the number, followed by a space, unless it's the last column
            if j == 8:
                print(board[i][j])
            else:
                print(str(board[i][j]) + " ", end="")


def find_empty(board: list[list[int]]) -> typing.Optional[tuple[int, int]]:
    """
    Finds the next empty (0) cell on the Sudoku board.

    Args:
        board (list[list[int]]): The 9x9 Sudoku board.

    Returns:
        tuple[int, int]: A tuple (row, col) of the empty cell, or None if no empty cell is found.
    """
    for r in range(len(board)):
        for c in range(len(board[0])):
            if board[r][c] == 0: # Check if the current cell contains a 0 (empty)
                return (r, c) # Return the row and column of the empty cell
    return None # No empty cells found, board is full


def valid(board: list[list[int]], num: int, pos: tuple[int, int]) -> bool:
    """
    Checks if placing a number 'num' at 'pos' (row, col) is valid according to Sudoku rules.

    Args:
        board (list[list[int]]): The 9x9 Sudoku board.
        num (int): The number (1-9) to check for validity.
        pos (tuple[int, int]): The position (row, col) on the board where 'num' is being considered.

    Returns:
        bool: True if the number is valid at the given position, False otherwise.
    """
    row, col = pos

    # Check row: Iterate through all columns in the current row
    for c in range(len(board[0])):
        # If the number 'num' is found in the row and it's not the position we are checking
        if board[row][c] == num and col != c:
            return False

    # Check column: Iterate through all rows in the current column
    for r in range(len(board)):
        # If the number 'num' is found in the column and it's not the position we are checking
        if board[r][col] == num and row != r:
            return False

    # Check 3x3 box: Determine the top-left corner of the 3x3 box
    box_x = col // 3 # Integer division to get the box's column index (0, 1, or 2)
    box_y = row // 3 # Integer division to get the box's row index (0, 1, or 2)

    # Iterate through cells within the determined 3x3 box
    for r_box in range(box_y * 3, box_y * 3 + 3):
        for c_box in range(box_x * 3, box_x * 3 + 3):
            # If the number 'num' is found in the box and it's not the position we are checking
            if board[r_box][c_box] == num and (r_box, c_box) != pos:
                return False

    return True # If no conflicts are found, the number is valid


def solve(board: list[list[int]]) -> bool:
    """
    Solves the Sudoku board using a backtracking algorithm.

    This function attempts to fill empty cells (represented by 0) with valid numbers
    (1-9). If a number leads to a solution, it returns True. If not, it backtracks
    and tries another number.

    Args:
        board (list[list[int]]): The 9x9 Sudoku board to be solved.
                                 This board will be modified in-place.

    Returns:
        bool: True if the board is successfully solved, False otherwise (no solution exists).
    """
    find = find_empty(board) # Find the next empty cell (row, col)

    # Base case: If no empty cell is found, the board is solved
    if not find:
        return True
    else:
        row, col = find # Unpack the row and column of the empty cell

    # Try numbers from 1 to 9 in the current empty cell
    for num_to_try in range(1, 10):
        if valid(board, num_to_try, (row, col)): # Check if the number is valid at this position
            board[row][col] = num_to_try # If valid, place the number on the board

            # Recursively call solve for the updated board
            if solve(board):
                return True # If the recursive call finds a solution, propagate True

            # Backtrack: If the current number doesn't lead to a solution, reset the cell to 0
            board[row][col] = 0

    return False # No number from 1-9 worked for the current empty cell, so backtrack further


if __name__ == "__main__":
    # Example Sudoku board
    initial_board = [
        [7,8,0,4,0,0,1,2,0],
        [6,0,0,0,7,5,0,0,9],
        [0,0,0,6,0,1,0,7,8],
        [0,0,7,0,4,0,2,6,0],
        [0,0,1,0,5,0,9,3,0],
        [9,0,4,0,6,0,0,0,5],
        [0,7,0,3,0,0,
