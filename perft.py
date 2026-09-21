from typing import Dict, List, Optional
from engine import get_legal_moves, make_move
from utils import get_square_name

def get_perft(
    position: Dict,
    depth: int,
    position_log: Optional[List[Dict]] = None
) -> int:
    if depth == 0:
        return 1

    count = 0
    moves = get_legal_moves(position)
    position_log = position_log or []
    
    for move in moves:
        position_log.append(position)
        new_position, new_log = make_move(position, move, position_log)
        count += get_perft(new_position, depth - 1, new_log)
        position = position_log.pop()

    return count

def perft_divide(
    position: Dict,
    depth: int,
    position_log: Optional[List[Dict]] = None
) -> None:
    moves = get_legal_moves(position)
    total = 0
    position_log = position_log or []
    
    for move in moves:
        position_log.append(position)
        new_position, new_log = make_move(position, move, position_log)
        n = get_perft(new_position, depth - 1, new_log)
        
        move_text = get_square_name(
            (move['row_from'], move['col_from'])
        ) + get_square_name(
            (move['row_to'], move['col_to'])
        )
        
        print(f"{move_text}: {n}")
        total += n
        position = position_log.pop()
        
    print(f"Nodes searched: {total}")