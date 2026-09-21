from typing import Dict, List, Tuple, Optional, Callable
import numpy as np
import copy
from piece_moves import (
    get_targets_king, get_targets_pawn, get_targets_knight, 
    get_targets_bishop, get_targets_rook, get_targets_queen
)
from utils import get_piece_map_row, get_square, get_square_name

def get_position(fen: str, position_log: List[Dict]) -> Dict:
    (piece_map, active_color, castle_rights, 
     ep_target, hm_clock, fm_clock) = fen.split(' ')
    
    fen_rows = piece_map.split('/')
    
    position = {
        'fen': fen,
        'piece_map': np.array(
            [get_piece_map_row(fen_row) for fen_row in fen_rows]
        ),
        'active_color': active_color,
        'castle_rights': castle_rights,
        'ep_target': get_square(ep_target),
        'hm_clock': int(hm_clock),
        'fm_clock': int(fm_clock)
    }
    
    position = add_position_info(position, position_log)
    
    return position

def add_position_info(
        position: Dict, 
        position_log: Optional[List[Dict]] = None
) -> Dict:
    king_location = np.where(
        position['piece_map'] == "K" + position['active_color']
    )
    
    position['king_row'], position['king_col'] = (
        int(king_location[0][0]), int(king_location[1][0])
    )
    
    (
        position['pins'], 
        position['ep_pin'], 
        position['checks'], 
        position['in_check']
    ) = get_pins_and_checks(position)
    
    position['legal_moves'] = get_legal_moves(position)
    
    position['checkmate'] = (
        len(position['legal_moves']) == 0 and position['in_check']
    )
    
    position['stalemate'] = (
        len(position['legal_moves']) == 0 and not position['in_check']
    )
    
    position['insufficient_material'] = has_insufficient_material(
        position['piece_map']
    )
    
    position['threefold_repetition'] = (
        position_log is not None and 
        has_threefold_repetition(position, position_log)
    )
    
    position['fifty_moves'] = (position['hm_clock'] == 100)
    
    return position

def get_pins_and_checks(
    position: Dict
) -> Tuple[List[Tuple[int, int, int, int]], 
           Tuple[int, int] | Tuple, 
           List[Tuple[int, int, int, int]], 
           bool]:
    pins: List[Tuple[int, int, int, int]] = []
    ep_pin: Tuple[int, int] | Tuple = ()
    checks: List[Tuple[int, int, int, int]] = []
    in_check: bool = False
    
    active_color = position['active_color']
    king_row, king_col = position['king_row'], position['king_col']
    friend = 'w' if active_color == 'w' else 'b'
    enemy = 'b' if active_color == 'w' else 'w'
    
    directions = [(y, x) for y in (-1, 0, 1) 
                         for x in (-1, 0, 1) 
                         if x != 0 or y != 0]
    
    attack_origins: Dict[str, List[Tuple[int, int]]] = {
        'P': [(-1, -1), (-1, 1)] if active_color == 'w' else [(1, -1), (1, 1)],
        'K': directions,
        'N': [(y, x) for y in (-2, -1, 1, 2)
                     for x in (-2, -1, 1, 2)
                     if abs(x) != abs(y)],
        'B': [(y, x) for y in (-1, 1) for x in (-1, 1)],
        'R': [(y, x) for y in (-1, 0, 1) 
                     for x in (-1, 0, 1)
                     if x == 0 or y == 0],
        'Q': directions
    }
    
    for d in directions:
        candidate_pin = None
        
        for i in range(1, 8):
            end_row = king_row + i*d[0]
            end_col = king_col + i*d[1]
            
            if end_row < 0 or end_row >= 8 or end_col < 0 or end_col >= 8:
                break
            
            end_piece = position['piece_map'][end_row][end_col]
            piece_type, color = end_piece
            
            if end_piece == '--':
                continue
            
            if color == friend and candidate_pin is None:
                candidate_pin = (end_row, end_col, d[0], d[1])
                continue
            
            if color == friend and candidate_pin is not None:
                break
            
            piece_attacking = (
                d in attack_origins[piece_type]
                and (i == 1 or piece_type in ('B', 'R', 'Q'))
            )
                
            if color == enemy and piece_attacking and candidate_pin is None:
                in_check = True
                checks.append((end_row, end_col, d[0], d[1]))
                break
            
            if (
                color == enemy 
                and piece_attacking 
                and candidate_pin is not None
            ):
                pins.append(candidate_pin)
                continue
            
            if color == enemy and not piece_attacking:
                break
            
    for km in attack_origins['N']:
        end_row = king_row + km[0]
        end_col = king_col + km[1]
        
        if end_row < 0 or end_row >= 8 or end_col < 0 or end_col >= 8:
            continue
        
        end_piece = position['piece_map'][end_row][end_col]
        
        if end_piece == "N" + enemy:
            in_check = True
            checks.append((end_row, end_col, km[0], km[1]))
    
    return pins, ep_pin, checks, in_check

def get_legal_moves(position: Dict) -> List[Dict]:
    targets_funs = {
        'K': get_targets_king,
        'P': get_targets_pawn,
        'N': get_targets_knight,
        'B': get_targets_bishop,
        'R': get_targets_rook,
        'Q': get_targets_queen,
    }
    
    if len(position['checks']) > 1:
        king_targets = get_targets_king(
            position, 
            position['king_row'], 
            position['king_col'], 
            position['active_color']
        )

        return [
            get_move(
                (position['king_row'], position['king_col']), 
                 target, 
                 position['piece_map']
            ) 
            for target in king_targets
        ]
    
    blocking_squares = get_blocking_squares(position)
    
    squares_from = [
        (row, col) for row in range(8) 
                   for col in range(8) 
                   if (
                        position['piece_map'][row][col][1] == 
                            position['active_color']
                   )
    ]
        
    candidate_moves = [
        get_move(
            square_from, 
            square_to, 
            position['piece_map']
        ) for square_from in squares_from
          for square_to in get_targets(square_from, position, targets_funs)
    ]
    
    candidate_moves_with_promotions = [
        move_with_promotion for move in candidate_moves
                            for move_with_promotion in (
                                get_promotions(move) if move['is_promotion']
                                else [move]
                            )
    ]
    
    legal_moves = [
        move for move in candidate_moves_with_promotions
        if is_legal(move, position, blocking_squares)
    ]
    
    return legal_moves

def get_blocking_squares(
    position: Dict
) -> List[Tuple[int, int]]:
    if not position['in_check']:
        return []
    
    check = position['checks'][0]
    piece_checking = position['piece_map'][check[0]][check[1]][0]
    
    if piece_checking in ('N', 'P'):
        return [(check[0], check[1])]
    
    check_direction = (check[2], check[3])
    king_row, king_col = position['king_row'], position['king_col']
    
    distance = 1 + max(
        abs(check[0] - king_row),
        abs(check[1] - king_col)
    )
    
    blocking_squares = [
        (
            king_row + i*check_direction[0], 
            king_col + i*check_direction[1]
        ) for i in range(1, distance)
    ]
    
    return blocking_squares

def get_move(
    square_from: Tuple[int, int],
    square_to: Tuple[int, int],
    piece_map: np.ndarray,
    promotion_piece: Optional[str] = None
) -> Dict:
    row_from, col_from = square_from
    row_to, col_to = square_to
    
    move = {
        'row_from': row_from,
        'col_from': col_from,
        'row_to': row_to,
        'col_to': col_to,
        'piece_moved': piece_map[row_from][col_from],
        'piece_captured': piece_map[row_to][col_to],
        'promotion_piece': promotion_piece,
        'is_ep_capture': False,
        'is_promotion': False,
        'is_castling': False
    }
    
    if move['piece_moved'][0] == 'P' and move['piece_captured'] == '--' \
        and move['col_from'] != move['col_to']:
            move['is_ep_capture'] = True
            move['piece_captured'] = 'P' \
                + ('w' if move['piece_moved'][1] == 'b' else 'b')
                
    final_rank = 0 if move['piece_moved'][1] == 'w' else 7
                
    if move['piece_moved'][0] == 'P' and move['row_to'] == final_rank:
        move['is_promotion'] = True
        
    if move['piece_moved'][0] == 'K' \
        and abs(move['col_to'] - move['col_from']) > 1:
            move['is_castling'] = True
    
    return move

def get_targets(
    square_from: Tuple[int, int],
    position: Dict,
    target_funs: Dict[
        str, 
        Callable[[Dict, int, int, str], List[Tuple[int, int]]]
    ]
) -> List[Tuple[int, int]]:
    row, col = square_from
    piece_type, color = position['piece_map'][row][col]
    targets = target_funs[piece_type](position, row, col, color)
    return targets

def get_promotions(move: Dict) -> List[Dict]:
    promotions = []
    for promotion_piece in ('N', 'B', 'R', 'Q'):
        promotion_move = copy.deepcopy(move)
        promotion_move.update({'promotion_piece': promotion_piece})
        promotions.append(promotion_move)
    return promotions

def is_legal(
    move: Dict,
    position: Dict,
    blocking_squares: List[Tuple[int, int]]
) -> bool:
    in_check, checks = position['in_check'], position['checks']
    pins, ep_pin = position['pins'], position['ep_pin']
    
    if not in_check and len(pins) == 0 and ep_pin == ():
        return True
    
    row_from, col_from = move['row_from'], move['col_from']
    row_to, col_to = move['row_to'], move['col_to']
    
    if (row_from, col_from) == ep_pin \
        and (row_to, col_to) == position['ep_target']:
            return False
    
    pin_locations = [(pin[0], pin[1]) for pin in pins]
    piece_pinned = (row_from, col_from) in pin_locations
    
    if not in_check and not piece_pinned:
        return True
    
    king_row, king_col = position['king_row'], position['king_col']
    
    if in_check:
        check = checks[0]
        piece_checking = position['piece_map'][check[0]][check[1]]
        ad = -1 if position['active_color'] == 'w' else 1
        enemy = 'b' if position['active_color'] == 'w' else 'w'
        
        ep_block = (
            piece_checking == 'P' + enemy
            and (check[0] + ad, check[1]) == position['ep_target']
            and move['is_ep_capture']
        )
        
        escapes_check = (
            (row_from, col_from) == (king_row, king_col)
            or (row_to, col_to) in blocking_squares
            or ep_block
        )
            
        if not escapes_check:
            return False
        
    if piece_pinned:
        pin_direction = [
            (pin[2], pin[3]) for pin in pins 
            if (row_from, col_from) == (pin[0], pin[1])
        ][0]
        
        pin_path: List[Tuple[int, int]] = []
        
        for i in range(1, 8):
            end_row = king_row + i*pin_direction[0]
            end_col = king_col + i*pin_direction[1]
            
            if end_row < 0 or end_row >= 8 or end_col < 0 or end_col >= 8:
                break
            
            end_piece = position['piece_map'][end_row][end_col]
            
            if end_piece == '--':
                pin_path.append((end_row, end_col))
                continue
            
            if (end_row, end_col) == (row_from, col_from):
                continue
            
            if end_piece == '--':
                pin_path.append((end_row, end_col))
                continue
            
            if end_piece != '--':
                pin_path.append((end_row, end_col))
                break
        
        stays_in_pin = (row_to, col_to) in pin_path
        
        if not stays_in_pin:
            return False
        
    return True

def make_move(
    position: Dict,
    move: Dict,
    position_log: List[Dict]
) -> Tuple[Dict, List[Dict]]:
    updated = {
        'piece_map': update_piece_map(
            position['piece_map'], 
            move, 
            position['ep_target']
        ),
        'active_color': 'b' if position['active_color'] == 'w' else 'w',
        'castle_rights': update_castle_rights(position['castle_rights'], move),
        'ep_target': update_ep_target(move),
        'hm_clock': (
            position['hm_clock'] + 1 if is_halfmove(move) else 0
        ),
        'fm_clock': (
            position['fm_clock'] + 1 
            if position['active_color'] == 'b' 
            else position['fm_clock']
        )
    }
    
    updated_log = position_log + [copy.deepcopy(position)]
    updated = add_position_info(updated, updated_log)
    updated['fen'] = get_fen(updated)
    return updated, updated_log

def update_piece_map(
    piece_map: np.ndarray,
    move: Dict,
    ep_target: Optional[Tuple[int, int]]
) -> np.ndarray:
    updated = copy.deepcopy(piece_map)
    updated[move['row_from']][move['col_from']] = '--'
    updated[move['row_to']][move['col_to']] = move['piece_moved']
    
    if move['is_ep_capture'] and ep_target is not None:
        ad = -1 if move['piece_moved'][1] == 'w' else 1
        ep_row, ep_col = ep_target
        updated[ep_row - ad][ep_col] = '--'
        
    if move['is_promotion']:
        updated[move['row_to']][move['col_to']] = move['promotion_piece'] \
            + move['piece_moved'][1]
            
    if move['is_castling']:
        rook_col_old = 7 if move['col_to'] == 6 else 0
        rook_col_new = 5 if move['col_to'] == 6 else 3
        rook_row = 7 if move['piece_moved'][1] == 'w' else 0
        updated[rook_row][rook_col_old] = '--'
        updated[rook_row][rook_col_new] = 'R' + move['piece_moved'][1]
    
    return updated

def update_castle_rights(castle_rights: str, move: Dict) -> str:
    updated = castle_rights
    
    for char in castle_rights:
        if char == '-':
            break
        
        king_color = 'w' if char.isupper() else 'b'
        rook_row = 7 if char.isupper() else 0
        rook_col = 7 if char.upper() == 'K' else 0
        
        if (move['piece_moved'] == 'K' + king_color
                or (move['row_from'], move['col_from']) == (rook_row, rook_col)
                or (move['row_to'], move['col_to']) == (rook_row, rook_col)):
            updated = updated.replace(char, '')
                    
    return '-' if updated == '' else updated

def update_ep_target(move: Dict) -> Optional[Tuple[int, int]]:
    if move['piece_moved'] == 'Pw' \
        and move['row_from'] == 6 \
        and move['row_to'] == 4:
            return (5, move['col_from'])
    elif move['piece_moved'] == 'Pb' \
        and move['row_from'] == 1 \
        and move['row_to'] == 3:
            return (2, move['col_from'])
    return None

def is_halfmove(move: Dict) -> bool:
    return move['piece_moved'][0] != 'P' and move['piece_captured'] == '--'

def unmake_move(
    position_log: List[Dict]
) -> Tuple[Dict, List[Dict]]:
    updated = position_log.pop()
    return updated, position_log

def get_fen(position: Dict) -> str:
    fen = ''
    
    for r in range(len(position['piece_map'])):
        count = 0
        for c in range(len(position['piece_map'][r])):
            piece_type, color = position['piece_map'][r][c]
            
            if piece_type == '-':
                count += 1
                if c == 7:
                    fen += str(count)
            else:
                if count > 0:
                    fen += str(count)
                count = 0
                fen += piece_type if color == 'w' else piece_type.lower()
                
            if c == 7 and r < 7:
                fen += '/'
                
    fen += (
        ' ' + position['active_color'] + ' ' 
        + position['castle_rights'] + ' '
    )

    fen += '-' if position['ep_target'] is None \
        else get_square_name(position['ep_target'])
        
    fen += f" {position['hm_clock']} {position['fm_clock']}"
    
    return fen

def has_insufficient_material(piece_map: np.ndarray) -> bool:
    # Count pieces by type
    pieces = {}
    for row in range(8):
        for col in range(8):
            piece = piece_map[row][col]
            if piece != '--':
                piece_type, color = piece
                if piece_type not in pieces:
                    pieces[piece_type] = {'w': 0, 'b': 0, 'squares': []}
                pieces[piece_type][color] += 1
                if piece_type == 'B':
                    pieces[piece_type]['squares'].append((row, col))
    
    # Kings only
    if len(pieces) == 1 and 'K' in pieces:
        return True
    
    # King and minor piece vs King
    if len(pieces) == 2 and 'K' in pieces and ('N' in pieces or 'B' in pieces):
        minor_piece = 'N' if 'N' in pieces else 'B'
        if pieces[minor_piece]['w'] + pieces[minor_piece]['b'] == 1:
            return True
    
    # King + Bishop vs King + Bishop (same colored squares)
    if (len(pieces) == 2 and 'K' in pieces and 'B' in pieces and
            pieces['B']['w'] == 1 and pieces['B']['b'] == 1):
        # Check if bishops are on same colored squares
        bishop_squares = pieces['B']['squares']
        if ((bishop_squares[0][0] + bishop_squares[0][1]) % 2 == 
                (bishop_squares[1][0] + bishop_squares[1][1]) % 2):
            return True
    
    return False

def has_threefold_repetition(position: Dict, position_log: List[Dict]) -> bool:
    # Get simplified FEN of current position (excluding move counters)
    if 'fen' not in position:
        position['fen'] = get_fen(position)
        
    current_fen_parts = position['fen'].split(' ')
    current_simplified_fen = ' '.join(current_fen_parts[:4])
    
    # Count occurrences in position log
    repetition_count = 1  # Start with 1 for the current position
    
    for past_position in position_log:
        if 'fen' not in past_position:
            past_position['fen'] = get_fen(past_position)
            
        past_fen_parts = past_position['fen'].split(' ')
        past_simplified_fen = ' '.join(past_fen_parts[:4])
        
        if past_simplified_fen == current_simplified_fen:
            repetition_count += 1
            
            if repetition_count >= 3:
                return True
    
    return False




        
        
    
    
    
    
    