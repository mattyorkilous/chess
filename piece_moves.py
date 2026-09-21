from typing import Dict, List, Tuple, Optional
import numpy as np

def get_targets_king(
    position: Dict,
    row: int,
    col: int, 
    color: str
) -> List[Tuple[int, int]]:
    attacked_squares = get_attacked_squares(position)
    squares_attacking = get_squares_attacking_king(position, row, col, color)
    
    targets_standard = [
        (r, c) for r, c in squares_attacking
        if position['piece_map'][r][c][1] != color \
            and (r, c) not in attacked_squares
    ]
    
    if (row, col) in attacked_squares:
        return targets_standard
    
    castle_row = 7 if color == 'w' else 0
    destination_cols = {'K': 6, 'Q': 2}
    paths = {'K': (5, 6), 'Q': (3, 2, 1)}
    targets_castling = []
    
    for side in position['castle_rights']:
        if side == '-':
            break
        
        if (side.isupper() and color == 'b') \
            or (side.islower() and color == 'w'):
                continue
        
        path = paths[side.upper()]
        path_is_clear = True
        
        for c in path:
            if position['piece_map'][castle_row][c] != '--' \
                or ((castle_row, c) in attacked_squares \
                    and c in (path[0], path[1])):
                     path_is_clear = False
                     break
         
        if not path_is_clear:
            continue
        
        destination_col = destination_cols[side.upper()]
        targets_castling.append((castle_row, destination_col))
    
    return targets_standard + targets_castling

def get_attacked_squares(
    position: Dict
) -> List[Tuple[int, int]]:
    squares_attacking_funs = {
        'K': get_squares_attacking_king,
        'P': get_squares_attacking_pawn,
        'N': get_squares_attacking_knight,
        'B': get_squares_attacking_bishop,
        'R': get_squares_attacking_rook,
        'Q': get_squares_attacking_queen,
    }
    
    piece_map = position['piece_map']
    inactive_color = 'b' if position['active_color'] == 'w' else 'w'
    
    squares_from = [
        (row, col) for row in range(8) 
        for col in range(8) 
        if piece_map[row][col][1] == inactive_color
    ]
        
    squares_attacking = [
        square for row, col in squares_from
        for square in squares_attacking_funs[piece_map[row][col][0]](
            position,
            row,
            col,
            piece_map[row][col][1]
        )
    ]
    
    return squares_attacking

def get_squares_attacking_king(
    position: Dict,
    row: int,
    col: int,
    color: str
) -> List[Tuple[int, int]]:
    directions = [
        (y, x) for y in (-1, 0, 1) 
        for x in (-1, 0, 1) 
        if x != 0 or y != 0
    ]
    
    squares_attacking = [
        (row + d[0], col + d[1]) for d in directions
        if 0 <= row + d[0] < 8 and 0 <= col + d[1] < 8
    ]
        
    return squares_attacking

def get_targets_pawn(
    position: Dict,
    row: int,
    col: int,
    color: str
) -> List[Tuple[int, int]]:
    piece_map = position['piece_map']
    ad = -1 if color == 'w' else 1
    start_row = 6 if color == 'w' else 1
    enemy = 'b' if color == 'w' else 'w'
    
    target_advance = (
        [(row + ad, col)] 
        if piece_map[row + ad][col] == '--' and 0 <= row + ad < 8
        else []
    )
        
    target_advance_2 = (
        [(row + 2*ad, col)]
        if (row == start_row 
            and piece_map[row + 2*ad][col] == piece_map[row + ad][col] == '--'
            and 0 <= row + ad < 8)
        else []
    )
        
    targets_capture = [
        (row + ad, col + cd) for cd in (-1, 1)
        if is_legal_pawn_capture(
            cd, row, col, ad, piece_map, enemy, position['ep_target']
        )
    ]
        
    return target_advance + target_advance_2 + targets_capture

def get_squares_attacking_pawn(
    position: Dict,
    row: int,
    col: int,
    color: str
) -> List[Tuple[int, int]]:
    ad = -1 if color == 'w' else 1
    
    squares_attacking = [
        (row + ad, col + cd) for cd in (-1, 1)
        if 0 <= row + ad < 8 and 0 <= col + cd < 8
    ]
    
    return squares_attacking

def is_legal_pawn_capture(
    cd: int,
    row: int,
    col: int,
    ad: int,
    piece_map: np.ndarray,
    enemy: str,
    ep_target: Optional[Tuple[int, int]]
) -> bool:
    return (
        0 <= row + ad < 8 and 0 <= col + cd < 8
        and (
            piece_map[row + ad][col + cd][1] == enemy
            or (row + ad, col + cd) == ep_target
        )
    )

def get_targets_knight(
    position: Dict,
    row: int,
    col: int,
    color: str
) -> List[Tuple[int, int]]:
    squares_attacking = get_squares_attacking_knight(position, row, col, color)
    targets = [
        (r, c) for r, c in squares_attacking
        if position['piece_map'][r][c][1] != color
    ]
    return targets

def get_squares_attacking_knight(
    position: Dict,
    row: int,
    col: int,
    color: str
) -> List[Tuple[int, int]]:
    directions = [
        (y, x) for y in (-2, -1, 1, 2)
        for x in (-2, -1, 1, 2)
        if abs(x) != abs(y)
    ]
    
    squares_attacking = [
        (row + d[0], col + d[1]) for d in directions
        if 0 <= row + d[0] < 8 and 0 <= col + d[1] < 8
    ]
    
    return squares_attacking

def get_targets_bishop(
    position: Dict,
    row: int,
    col: int,
    color: str
) -> List[Tuple[int, int]]:
    targets: List[Tuple[int, int]] = []
    directions = [(y, x) for y in (-1, 1) for x in (-1, 1)]
        
    for d in directions:
        for i in range(1, 8):
            end_row, end_col = row + i*d[0], col + i*d[1]
            
            if end_row < 0 or end_row >= 8 or end_col < 0 or end_col >= 8:
                break
            
            end_piece = position['piece_map'][end_row][end_col]
            
            if end_piece == '--':
                targets.append((end_row, end_col))
                continue
            
            if end_piece[1] != color:
                targets.append((end_row, end_col))
            break
    
    return targets

def get_squares_attacking_bishop(
    position: Dict,
    row: int,
    col: int,
    color: str
) -> List[Tuple[int, int]]:
    enemy = 'b' if color == 'w' else 'w'
    squares_attacking: List[Tuple[int, int]] = []
    directions = [(y, x) for y in (-1, 1) for x in (-1, 1)]
    
    for d in directions:
        for i in range(1, 8):
            end_row, end_col = row + i*d[0], col + i*d[1]
            
            if end_row < 0 or end_row >= 8 or end_col < 0 or end_col >= 8:
                break
            
            end_piece = position['piece_map'][end_row][end_col]
            
            if end_piece == '--' or end_piece == 'K' + enemy:
                squares_attacking.append((end_row, end_col))
                continue
            
            squares_attacking.append((end_row, end_col))
            break
    
    return squares_attacking

def get_targets_rook(
    position: Dict,
    row: int,
    col: int,
    color: str
) -> List[Tuple[int, int]]:
    targets: List[Tuple[int, int]] = []
    directions = [
        (y, x) for y in (-1, 0, 1) 
        for x in (-1, 0, 1)
        if (x == 0) ^ (y == 0)
    ]
        
    for d in directions:
        for i in range(1, 8):
            end_row, end_col = row + i*d[0], col + i*d[1]
            
            if end_row < 0 or end_row >= 8 or end_col < 0 or end_col >= 8:
                break
            
            end_piece = position['piece_map'][end_row][end_col]
            
            if end_piece == '--':
                targets.append((end_row, end_col))
                continue
            
            if end_piece[1] != color:
                targets.append((end_row, end_col))
            break
    
    return targets

def get_squares_attacking_rook(
    position: Dict,
    row: int,
    col: int,
    color: str
) -> List[Tuple[int, int]]:
    enemy = 'b' if color == 'w' else 'w'
    squares_attacking: List[Tuple[int, int]] = []
    directions = [
        (y, x) for y in (-1, 0, 1) 
        for x in (-1, 0, 1)
        if (x == 0) ^ (y == 0)
    ]
    
    for d in directions:
        for i in range(1, 8):
            end_row, end_col = row + i*d[0], col + i*d[1]
            
            if end_row < 0 or end_row >= 8 or end_col < 0 or end_col >= 8:
                break
            
            end_piece = position['piece_map'][end_row][end_col]
            
            if end_piece == '--' or end_piece == 'K' + enemy:
                squares_attacking.append((end_row, end_col))
                continue
            
            squares_attacking.append((end_row, end_col))
            break
    
    return squares_attacking

def get_targets_queen(
    position: Dict,
    row: int,
    col: int,
    color: str
) -> List[Tuple[int, int]]:
    targets = get_targets_bishop(position, row, col, color) \
        + get_targets_rook(position, row, col, color)
    return targets

def get_squares_attacking_queen(
    position: Dict,
    row: int,
    col: int,
    color: str
) -> List[Tuple[int, int]]:
    squares_attacking = get_squares_attacking_bishop(
        position, 
        row, 
        col, 
        color
    ) + get_squares_attacking_rook(position, row, col, color)
    return squares_attacking