import time
import random
from flask import Flask, render_template, request, redirect, url_for

# Constants
BOARD_HEIGHT = 21
BOARD_WIDTH = 7
KING_COOLDOWN = 2  # Seconds
ROOK_COOLDOWN = 2  # Seconds
PAWN_MOVE_INTERVAL = 3  # Seconds
PAWN_CAPTURE_DELAY = 1  # Seconds
PAWN_COLUMNS = [0, 2, 3, 4, 6]  # Specific columns for pawns
WHITE_KING_START_POS = (0, 3)
BLACK_KING_START_POS = (20, 3)
WHITE_ROOK_START_POS = [(0, 0), (0, 6)]  
BLACK_ROOK_START_POS = [(20, 0), (20, 6)]
WHITE_BISHOP_START_POS = [(0, 2), (0, 4)]  
BLACK_BISHOP_START_POS = [(20, 2), (20, 4)]  
WHITE_KNIGHT_START_POS = [(0, 1), (0, 5)]  # Between rooks and bishops
BLACK_KNIGHT_START_POS = [(20, 1), (20, 5)]
MAX_VERTICAL_DISTANCE = 7

# Initialize board
board = [["." for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]

# Initialize pieces
pieces = {
    "white_king": {"position": WHITE_KING_START_POS, "last_move_time": 0, "lives": 3, "pending_move": None},
    "black_king": {"position": BLACK_KING_START_POS, "last_move_time": 0, "lives": 3, "pending_move": None},
    "white_bishops": [{"position": pos, "last_move_time": 0} for pos in WHITE_BISHOP_START_POS],
    "black_bishops": [{"position": pos, "last_move_time": 0} for pos in BLACK_BISHOP_START_POS],
    "white_rooks": [{"position": pos, "last_move_time": 0} for pos in WHITE_ROOK_START_POS],
    "black_rooks": [{"position": pos, "last_move_time": 0} for pos in BLACK_ROOK_START_POS],
    "white_knights": [{"position": pos, "last_move_time": 0} for pos in WHITE_KNIGHT_START_POS],
    "black_knights": [{"position": pos, "last_move_time": 0} for pos in BLACK_KNIGHT_START_POS],
    "white_pawns": [{"position": (2, col), "last_move_time": 0} for col in PAWN_COLUMNS],
    "black_pawns": [{"position": (18, col), "last_move_time": 0} for col in PAWN_COLUMNS]
}

app = Flask(__name__)

def display_board():
    """Return the current board state as a list of strings."""
    temp_board = [row[:] for row in board]
    wx, wy = pieces["white_king"]["position"]
    bx, by = pieces["black_king"]["position"]
    current_time = time.time()
    
    # Check white king cooldown
    if current_time - pieces["white_king"]["last_move_time"] < KING_COOLDOWN:
        temp_board[wx][wy] = "G"  # Gray square for white king on cooldown
    else:
        temp_board[wx][wy] = "K"  # White King
    
    # Check black king cooldown
    if current_time - pieces["black_king"]["last_move_time"] < KING_COOLDOWN:
        temp_board[bx][by] = "g"  # Gray square for black king on cooldown
    else:
        temp_board[bx][by] = "k"  # Black King

    # Render bishops
    for bishop in pieces["white_bishops"]:
        bx, by = bishop["position"]
        temp_board[bx][by] = "B"  # White Bishop
    for bishop in pieces["black_bishops"]:
        bx, by = bishop["position"]
        temp_board[bx][by] = "b"  # Black Bishop

     # Render knights
    for knight in pieces["white_knights"]:
        nx, ny = knight["position"]
        temp_board[nx][ny] = "N"  # White Knight
    for knight in pieces["black_knights"]:
        nx, ny = knight["position"]
        temp_board[nx][ny] = "n"  # Black Knight
    
    # Render rooks
    for rook in pieces["white_rooks"]:
        rx, ry = rook["position"]
        temp_board[rx][ry] = "R"  # White Rook
    for rook in pieces["black_rooks"]:
        rx, ry = rook["position"]
        temp_board[rx][ry] = "r"  # Black Rook
    
    for pawn in pieces["white_pawns"]:
        px, py = pawn["position"]
        temp_board[px][py] = "P"  # White pawns
    for pawn in pieces["black_pawns"]:
        px, py = pawn["position"]
        temp_board[px][py] = "p"  # Black pawns
    return [" ".join(row) for row in temp_board]

def is_legal_move(position, piece):
    """Check if a move is within the board boundaries and follows the movement rules."""
    x, y = position
    if not (0 <= x < BOARD_HEIGHT and 0 <= y < BOARD_WIDTH):
        return False
    current_pos = piece["position"]
    
    # Check if piece is a bishop
    if piece in pieces["white_bishops"] or piece in pieces["black_bishops"]:
        # Bishops can only move diagonally
        if abs(x - current_pos[0]) != abs(y - current_pos[1]):
            return False
        # Check vertical distance limit
        if abs(x - current_pos[0]) > MAX_VERTICAL_DISTANCE:
            return False
            
    # Check if piece is a rook
    elif piece in pieces["white_rooks"] or piece in pieces["black_rooks"]:
        # Rooks can only move horizontally or vertically
        if not (x == current_pos[0] or y == current_pos[1]):
            return False
        # Check vertical distance limit for vertical moves only
        if x != current_pos[0] and abs(x - current_pos[0]) > MAX_VERTICAL_DISTANCE:
            return False
            
    # Check if piece is a king
    elif piece == pieces["white_king"] or piece == pieces["black_king"]:
        if abs(x - current_pos[0]) > MAX_VERTICAL_DISTANCE:
            return False
        if not (x == current_pos[0] or y == current_pos[1] or abs(x - current_pos[0]) == abs(y - current_pos[1])):
            return False
            
    # Check if path is clear (excluding destination square)
    if not is_path_clear(current_pos, (x, y)):
        return False
        
    return True

def is_path_clear(start, end):
    """Check if the path is clear for the piece's movement."""
    sx, sy = start
    ex, ey = end
    if sx == ex:  # Vertical movement
        step = 1 if ey > sy else -1
        for y in range(sy + step, ey, step):
            if any(piece["position"] == (sx, y) for piece_set in pieces.values() if isinstance(piece_set, list) for piece in piece_set):
                return False
            if pieces["white_king"]["position"] == (sx, y) or pieces["black_king"]["position"] == (sx, y):
                return False
    elif sy == ey:  # Horizontal movement
        step = 1 if ex > sx else -1
        for x in range(sx + step, ex, step):
            if any(piece["position"] == (x, sy) for piece_set in pieces.values() if isinstance(piece_set, list) for piece in piece_set):
                return False
            if pieces["white_king"]["position"] == (x, sy) or pieces["black_king"]["position"] == (x, sy):
                return False
    elif abs(ex - sx) == abs(ey - sy):  # Diagonal movement
        x_step = 1 if ex > sx else -1
        y_step = 1 if ey > sy else -1
        x, y = sx + x_step, sy + y_step
        while (x != ex) and (y != ey):  # Fixed condition
            if any(piece["position"] == (x, y) for piece_set in pieces.values() if isinstance(piece_set, list) for piece in piece_set):
                return False
            if pieces["white_king"]["position"] == (x, y) or pieces["black_king"]["position"] == (x, y):
                return False
            x += x_step
            y += y_step
    print(f"Path clear from {start} to {end}")  # Debug logging
    return True

def king_move(king_color, new_position=None):
    """Move the specified king and capture any piece on destination square."""
    king = pieces[king_color]
    current_time = time.time()
    if new_position and current_time - king["last_move_time"] >= KING_COOLDOWN:
        new_x, new_y = new_position
        if is_legal_move((new_x, new_y), king):
            # Capture any piece at the destination
            for piece_set_name, piece_set in pieces.items():
                # Don't capture pieces of same color
                if piece_set_name.startswith(king_color.split('_')[0]):
                    continue
                    
                if isinstance(piece_set, list):
                    for piece in piece_set[:]:  # Create copy to modify during iteration
                        if piece["position"] == (new_x, new_y):
                            piece_set.remove(piece)
                            print(f"{king_color} captures piece at ({new_x}, {new_y})")
                elif piece_set["position"] == (new_x, new_y):
                    piece_set["position"] = None
                    print(f"{king_color} captures piece at ({new_x}, {new_y})")
                    
            # Move king to new position
            king["position"] = (new_x, new_y)
            king["last_move_time"] = current_time
            print(f"{king_color} moved to ({new_x}, {new_y})")

def bishop_move(bishop_color, new_position=None):
    """Move the specified bishop and capture any piece on destination square."""
    current_time = time.time()
    start_x = int(request.form['start_x'])
    start_y = int(request.form['start_y'])
    
    print(f"Attempting to move bishop from ({start_x}, {start_y})")  # Debug log
    
    # Find the specific bishop that was clicked
    clicked_bishop = next(
        (bishop for bishop in pieces[bishop_color] 
         if bishop["position"] == (start_x, start_y)), None)
         
    print(f"Found bishop: {clicked_bishop}")  # Debug log
    
    if clicked_bishop and new_position:
        cooldown_passed = current_time - clicked_bishop["last_move_time"] >= KING_COOLDOWN
        print(f"Cooldown passed: {cooldown_passed}")  # Debug log
        
        if cooldown_passed:
            new_x, new_y = new_position
            if is_legal_move((new_x, new_y), clicked_bishop):
                # Capture logic
                for piece_set_name, piece_set in pieces.items():
                    if piece_set_name.startswith(bishop_color.split('_')[0]):
                        continue
                    
                    if isinstance(piece_set, list):
                        for piece in piece_set[:]:
                            if piece["position"] == (new_x, new_y):
                                piece_set.remove(piece)
                                print(f"{bishop_color} captures piece at ({new_x}, {new_y})")
                    elif piece_set["position"] == (new_x, new_y):
                        piece_set["position"] = None
                        print(f"{bishop_color} captures piece at ({new_x}, {new_y})")
                
                clicked_bishop["position"] = (new_x, new_y)
                clicked_bishop["last_move_time"] = current_time
                print(f"{bishop_color} moved to ({new_x}, {new_y})")
            

def rook_move(rook_color, new_position=None):
    """Move the specified rook and capture any piece on destination square."""
    current_time = time.time()
    start_x = int(request.form['start_x'])
    start_y = int(request.form['start_y'])
    
    # Find the specific rook that was clicked
    clicked_rook = next(
        (rook for rook in pieces[rook_color] 
         if rook["position"] == (start_x, start_y)), None
    )
    
    if clicked_rook and new_position and current_time - clicked_rook["last_move_time"] >= ROOK_COOLDOWN:
        new_x, new_y = new_position
        if is_legal_move((new_x, new_y), clicked_rook):
            # Check for capture (excluding same color pieces)
            for piece_set_name, piece_set in pieces.items():
                if piece_set_name.startswith(rook_color.split('_')[0]):
                    continue
                
                if isinstance(piece_set, list):
                    for piece in piece_set[:]:
                        if piece["position"] == (new_x, new_y):
                            piece_set.remove(piece)
                            print(f"{rook_color} captures piece at ({new_x}, {new_y})")
                elif piece_set["position"] == (new_x, new_y):
                    piece_set["position"] = None
                    print(f"{rook_color} captures piece at ({new_x}, {new_y})")
            
            clicked_rook["position"] = (new_x, new_y)
            clicked_rook["last_move_time"] = current_time
            print(f"{rook_color} moved to ({new_x}, {new_y})")
            

def knight_move(knight_color, new_position=None):
    """Move the specified knight and capture any piece on destination square."""
    current_time = time.time()
    start_x = int(request.form['start_x'])
    start_y = int(request.form['start_y'])
    
    # Find the specific knight that was clicked
    clicked_knight = next(
        (knight for knight in pieces[knight_color] 
         if knight["position"] == (start_x, start_y)), None
    )
    
    if clicked_knight and new_position and current_time - clicked_knight["last_move_time"] >= KING_COOLDOWN:
        new_x, new_y = new_position
        current_pos = clicked_knight["position"]
        
        # Check if move is valid L shape
        dx = abs(new_x - current_pos[0])
        dy = abs(new_y - current_pos[1])
        if not ((dx == 2 and dy == 1) or (dx == 1 and dy == 2)):
            return
            
        # Capture logic
        for piece_set_name, piece_set in pieces.items():
            if piece_set_name.startswith(knight_color.split('_')[0]):
                continue
            
            if isinstance(piece_set, list):
                for piece in piece_set[:]:
                    if piece["position"] == (new_x, new_y):
                        piece_set.remove(piece)
                        print(f"{knight_color} captures piece at ({new_x}, {new_y})")
            elif piece_set["position"] == (new_x, new_y):
                piece_set["position"] = None
                print(f"{knight_color} captures piece at ({new_x}, {new_y})")
        
        clicked_knight["position"] = (new_x, new_y)
        clicked_knight["last_move_time"] = current_time
        print(f"{knight_color} moved to ({new_x}, {new_y})")
        

def move_pawns():
    """Move pawns forward by 0, 1, or 2 squares every 3 seconds."""
    current_time = time.time()
    for pawn_set, direction in [("white_pawns", 1), ("black_pawns", -1)]:
        for pawn in pieces[pawn_set]:
            if current_time - pawn["last_move_time"] >= PAWN_MOVE_INTERVAL:
                px, py = pawn["position"]
                new_x = px + direction * random.choice([0, 1, 2])  # Move 0, 1, or 2 squares
                
                # Check board boundaries and pawn collisions
                if 0 <= new_x < BOARD_HEIGHT:
                    # Check if destination has same color pawn
                    has_collision = any(
                        other_pawn["position"] == (new_x, py) 
                        for other_pawn in pieces[pawn_set] 
                        if other_pawn != pawn
                    )
                    
                    if not has_collision:
                        pawn["position"] = (new_x, py)
                        pawn["last_move_time"] = current_time
                        
                        # Check for captures after moving with delay
                        time.sleep(PAWN_CAPTURE_DELAY)
                        check_pawn_capture("white_king")
                        check_pawn_capture("black_king")

def check_pawn_capture(king_color):
    """Check if pawns can capture the specified king or other pieces."""
    kx, ky = pieces[king_color]["position"]
    
    for pawn_set, direction in [("white_pawns", 1), ("black_pawns", -1)]:
        for pawn in pieces[pawn_set]:
            px, py = pawn["position"]
            
            # Check king capture (diagonal in travel direction)
            if ((pawn_set == "white_pawns" and king_color == "black_king") or 
                (pawn_set == "black_pawns" and king_color == "white_king")):
                if abs(py - ky) == 1 and px + direction == kx:
                    print(f"Pawn at ({px}, {py}) captures the {king_color}!")
                    pieces[king_color]["lives"] -= 1
                    if pieces[king_color]["lives"] > 0:
                        pieces[king_color]["position"] = (
                            WHITE_KING_START_POS if king_color == "white_king" 
                            else BLACK_KING_START_POS
                        )
                        pawn["position"] = (kx, ky)
                    else:
                        return True
            
            # Check pawn captures
            capture_squares = [(px + direction, py - 1), (px + direction, py + 1)]
            for cx, cy in capture_squares:
                if not (0 <= cx < BOARD_HEIGHT and 0 <= cy < BOARD_WIDTH):
                    continue
                
                # Check each piece type for capture
                for piece_set_name, piece_set in pieces.items():
                    # Skip same color pieces
                    if piece_set_name.startswith(pawn_set.split('_')[0]):
                        continue

                    if isinstance(piece_set, list):
                        for piece in piece_set[:]:
                            if piece["position"] == (cx, cy):
                                piece_set.remove(piece)
                                pawn["position"] = (cx, cy)
                                print(f"Pawn at ({px}, {py}) captures piece at ({cx}, {cy})")
                    
    return False

# Add to main.py:
def reset_game():
    """Reset all pieces to starting positions and restore king lives."""
    pieces["white_king"] = {"position": WHITE_KING_START_POS, "last_move_time": 0, "lives": 3, "pending_move": None}
    pieces["black_king"] = {"position": BLACK_KING_START_POS, "last_move_time": 0, "lives": 3, "pending_move": None}
    pieces["white_bishops"] = [{"position": pos, "last_move_time": 0} for pos in WHITE_BISHOP_START_POS]
    pieces["black_bishops"] = [{"position": pos, "last_move_time": 0} for pos in BLACK_BISHOP_START_POS]
    pieces["white_rooks"] = [{"position": pos, "last_move_time": 0} for pos in WHITE_ROOK_START_POS]
    pieces["black_rooks"] = [{"position": pos, "last_move_time": 0} for pos in BLACK_ROOK_START_POS]
    pieces["white_pawns"] = [{"position": (2, col), "last_move_time": 0} for col in PAWN_COLUMNS]
    pieces["black_pawns"] = [{"position": (18, col), "last_move_time": 0} for col in PAWN_COLUMNS]

@app.route('/new_game', methods=['POST'])
def new_game():
    """Handle new game request."""
    reset_game()
    return redirect(url_for('index'))

@app.route('/')
def index():
    board_state = display_board()
    return render_template('index.html', board=board_state)

@app.route('/move', methods=['POST'])
def move():
    new_x = int(request.form['end_x'])
    new_y = int(request.form['end_y'])
    piece_type = request.form['piece_type']
    
    print(f"Move requested for piece type: {piece_type}")  # Debug log
    
    if piece_type in ["K", "G"]:  # White King
        king_move("white_king", (new_x, new_y))
    elif piece_type in ["k", "g"]:  # Black King
        king_move("black_king", (new_x, new_y))
    elif piece_type == "B":  # White Bishop
        print("Attempting white bishop move")
        bishop_move("white_bishops", (new_x, new_y))
    elif piece_type == "b":  # Black Bishop
        print("Attempting black bishop move")
        bishop_move("black_bishops", (new_x, new_y))
    elif piece_type == "R":  # White Rook
        rook_move("white_rooks", (new_x, new_y))
    elif piece_type == "r":  # Black Rook
        rook_move("black_rooks", (new_x, new_y))
    elif piece_type == "N":  # White Knight
        print("Attempting white knight move")
        knight_move("white_knights", (new_x, new_y))
    elif piece_type == "n":  # Black Knight
        print("Attempting black knight move")
        knight_move("black_knights", (new_x, new_y))
    
    move_pawns()
    
    if check_pawn_capture("white_king"):
        return "Game Over! The White King has been captured."
    if check_pawn_capture("black_king"):
        return "Game Over! The Black King has been captured."
    
    return redirect(url_for('index'))

@app.route('/board_state')
def board_state():
    board_state = display_board()
    return {"board": board_state}

if __name__ == "__main__":
    app.run(debug=True)