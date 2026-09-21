import random
from typing import Dict, List, Any, Optional
from engine import make_move, unmake_move

def ai_defaults() -> Dict[str, Any]:
    """Return default AI configuration values."""
    ai_values: Dict[str, Any] = {
        'search_depth': 4,
        'transposition_table_size': 1000000,
        'piece_values': {
            'P': 100,
            'N': 320,
            'B': 330,
            'R': 500,
            'Q': 900,
            'K': 20000
        },
        'position_values': {
            'P': [
                [0, 0, 0, 0, 0, 0, 0, 0],
                [50, 50, 50, 50, 50, 50, 50, 50],
                [10, 10, 20, 30, 30, 20, 10, 10],
                [5, 5, 10, 25, 25, 10, 5, 5],
                [0, 0, 0, 20, 20, 0, 0, 0],
                [5, -5, -10, 0, 0, -10, -5, 5],
                [5, 10, 10, -20, -20, 10, 10, 5],
                [0, 0, 0, 0, 0, 0, 0, 0]
            ],
            'N': [
                [-50, -40, -30, -30, -30, -30, -40, -50],
                [-40, -20, 0, 0, 0, 0, -20, -40],
                [-30, 0, 10, 15, 15, 10, 0, -30],
                [-30, 5, 15, 20, 20, 15, 5, -30],
                [-30, 0, 15, 20, 20, 15, 0, -30],
                [-30, 5, 10, 15, 15, 10, 5, -30],
                [-40, -20, 0, 5, 5, 0, -20, -40],
                [-50, -40, -30, -30, -30, -30, -40, -50]
            ],
            'B': [
                [-20, -10, -10, -10, -10, -10, -10, -20],
                [-10, 0, 0, 0, 0, 0, 0, -10],
                [-10, 0, 10, 10, 10, 10, 0, -10],
                [-10, 5, 10, 10, 10, 10, 5, -10],
                [-10, 0, 10, 10, 10, 10, 0, -10],
                [-10, 10, 10, 10, 10, 10, 10, -10],
                [-10, 5, 0, 0, 0, 0, 5, -10],
                [-20, -10, -10, -10, -10, -10, -10, -20]
            ],
            'R': [
                [0, 0, 0, 0, 0, 0, 0, 0],
                [5, 10, 10, 10, 10, 10, 10, 5],
                [-5, 0, 0, 0, 0, 0, 0, -5],
                [-5, 0, 0, 0, 0, 0, 0, -5],
                [-5, 0, 0, 0, 0, 0, 0, -5],
                [-5, 0, 0, 0, 0, 0, 0, -5],
                [-5, 0, 0, 0, 0, 0, 0, -5],
                [0, 0, 0, 5, 5, 0, 0, 0]
            ],
            'Q': [
                [-20, -10, -10, -5, -5, -10, -10, -20],
                [-10, 0, 0, 0, 0, 0, 0, -10],
                [-10, 0, 5, 5, 5, 5, 0, -10],
                [-5, 0, 5, 5, 5, 5, 0, -5],
                [0, 0, 5, 5, 5, 5, 0, -5],
                [-10, 5, 5, 5, 5, 5, 0, -10],
                [-10, 0, 5, 0, 0, 0, 0, -10],
                [-20, -10, -10, -5, -5, -10, -10, -20]
            ],
            'K': [
                [-30, -40, -40, -50, -50, -40, -40, -30],
                [-30, -40, -40, -50, -50, -40, -40, -30],
                [-30, -40, -40, -50, -50, -40, -40, -30],
                [-30, -40, -40, -50, -50, -40, -40, -30],
                [-20, -30, -30, -40, -40, -30, -30, -20],
                [-10, -20, -20, -20, -20, -20, -20, -10],
                [20, 20, 0, 0, 0, 0, 20, 20],
                [20, 30, 10, 0, 0, 10, 30, 20]
            ]
        }
    }
    
    return ai_values

# Add a global transposition table
transposition_table = {}

def get_best_move(position: Dict[str, Any]) -> Dict[str, Any]:
    """
    Select the best move for the AI to play using iterative deepening.
    """
    config: Dict[str, Any] = ai_defaults()
    legal_moves: List[Dict[str, Any]] = position['legal_moves']
    
    # If only one legal move, return it immediately
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    best_move: Optional[Dict[str, Any]] = None
    position_log: List[Dict[str, Any]] = []
    
    # Iterative deepening
    for current_depth in range(1, config['search_depth'] + 1):
        best_score = float('-inf')
        current_best_move = None
        
        for move in order_moves(position, legal_moves):
            # Make the move
            new_position: Dict[str, Any]
            new_position, position_log = make_move(position, move, position_log)
            
            # Evaluate the resulting position
            score: float = -minimax(
                new_position, 
                current_depth - 1, 
                float('-inf'), 
                float('inf'), 
                False,
                position_log
            )
            
            # Unmake the move
            position, position_log = unmake_move(position_log)
            
            if score > best_score:
                best_score = score
                current_best_move = move
        
        best_move = current_best_move if current_best_move else best_move
    
    return best_move if best_move else random.choice(legal_moves)

def minimax(
    position: Dict[str, Any], 
    depth: int, 
    alpha: float, 
    beta: float, 
    maximizing_player: bool,
    position_log: List[Dict[str, Any]]
) -> float:
    """
    Minimax algorithm with alpha-beta pruning and transposition table.
    """
    # Create a position hash key
    position_hash = hash_position(position)
    
    # Check transposition table
    if position_hash in transposition_table:
        stored_depth, stored_value = transposition_table[position_hash]
        if stored_depth >= depth:
            return stored_value
    
    if depth == 0 or len(position['legal_moves']) == 0:
        evaluation = evaluate_position(position)
        transposition_table[position_hash] = (depth, evaluation)
        return evaluation
    
    # Use a common function to evaluate moves for both players
    best_value = float('-inf') if maximizing_player else float('inf')
    compare_func = max if maximizing_player else min
    next_player_maximizing = not maximizing_player
    
    for move in position['legal_moves']:
        # Make the move
        new_position, position_log = make_move(position, move, position_log)
        
        # Evaluate
        eval_score = minimax(
            new_position, 
            depth - 1, 
            alpha, 
            beta, 
            next_player_maximizing, 
            position_log
        )
        
        # Negate score for minimizing player's perspective
        if not maximizing_player:
            eval_score = -eval_score
            
        # Unmake the move
        position, position_log = unmake_move(position_log)
        
        # Update best value
        best_value = compare_func(best_value, eval_score)
        
        # Update alpha/beta
        if maximizing_player:
            alpha = max(alpha, best_value)
        else:
            beta = min(beta, best_value)
            
        # Alpha-beta pruning
        if beta <= alpha:
            break
    
    # Store result in transposition table
    transposition_table[position_hash] = (depth, best_value)
    return best_value

def hash_position(position: Dict[str, Any]) -> int:
    """Create a hash value for the position."""
    # Simple implementation - in practice, you'd use Zobrist hashing
    board_str = str(position['piece_map']) + position['active_color']
    return hash(board_str)

def evaluate_position(position: Dict[str, Any]) -> float:
    """
    Enhanced position evaluation with additional heuristics.
    """
    config: Dict[str, Any] = ai_defaults()
    piece_values: Dict[str, int] = config['piece_values']
    position_tables: Dict[str, List[List[int]]] = config['position_values']
    
    # If checkmate, return a very high/low score
    if position['checkmate']:
        return -10000  # Current player is in checkmate
    
    # If stalemate, return 0
    if position['stalemate']:
        return 0
    
    # Calculate material balance
    score: float = 0
    piece_map: List[List[str]] = position['piece_map']
    current_color: str = position['active_color']
    
    # Sum up material values
    material_score: int = sum(
        piece_values[piece[0]] * (1 if piece[1] == current_color else -1)
        for row in piece_map
        for piece in row
        if piece != '--'
    )
    
    # Add positional bonuses for all pieces
    position_score: int = 0
    for row in range(8):
        for col in range(8):
            piece: str = piece_map[row][col]
            if piece != '--':
                piece_type: str = piece[0]
                piece_color: str = piece[1]
                
                # Skip if piece type doesn't have position values
                if piece_type not in position_tables:
                    continue
                
                # Get position value (flipped for black)
                position_value: int
                if piece_color == 'w':
                    position_value = position_tables[piece_type][row][col]
                else:
                    position_value = position_tables[piece_type][7-row][col]
                
                # Add or subtract based on piece color
                multiplier: int = 1 if piece_color == current_color else -1
                position_score += position_value * multiplier
    
    # Mobility bonus (number of legal moves)
    mobility_score: int = len(position['legal_moves'])
    
    # Add pawn structure evaluation
    pawn_structure_score = evaluate_pawn_structure(position, current_color)
    
    # King safety evaluation
    king_safety_score = evaluate_king_safety(position, current_color)
    
    # Control of center squares
    center_control = evaluate_center_control(position, current_color)
    
    # Combine all scores with appropriate weights
    score = (
        material_score + 
        position_score * 0.1 + 
        mobility_score * 0.1 + 
        pawn_structure_score * 0.05 +
        king_safety_score * 0.2 +
        center_control * 0.15
    )
    
    return score

def evaluate_pawn_structure(position: Dict[str, Any], player_color: str) -> float:
    """Evaluate pawn structure - doubled, isolated, and passed pawns."""
    # Implementation would analyze pawn formations
    # This is a placeholder that you would expand
    return 0

def evaluate_king_safety(position: Dict[str, Any], player_color: str) -> float:
    """Evaluate king safety based on pawn shield and attacking pieces."""
    # Implementation would check pawns in front of castled king, etc.
    return 0

def evaluate_center_control(position: Dict[str, Any], player_color: str) -> float:
    """Evaluate control of the center squares (d4, d5, e4, e5)."""
    # Implementation would count attackers and defenders of center squares
    return 0

def order_moves(position: Dict[str, Any], moves: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Order moves to improve alpha-beta pruning efficiency."""
    # Prioritize captures and promotions
    move_scores = [(move, score_move(position, move)) for move in moves]
    return [move for move, _ in sorted(move_scores, key=lambda x: x[1], reverse=True)]

def score_move(position: Dict[str, Any], move: Dict[str, Any]) -> int:
    """Score a move for ordering heuristics."""
    score = 0
    piece_map = position['piece_map']
    piece_values = ai_defaults()['piece_values']
    
    # Capturing moves (MVV-LVA: Most Valuable Victim - Least Valuable Aggressor)
    if move.get('piece_captured'):
        victim_type = move['piece_captured'][0]
        aggressor_type = piece_map[move['row_from']][move['col_from']][0]
        
        # Check if victim_type is an empty square
        if victim_type == '-':
            # No piece captured, so no value to add for victim
            score += 0 - piece_values[aggressor_type]
        else:
            score += 10 * piece_values[victim_type] - piece_values[aggressor_type]
    
    # Promotion bonus
    if move.get('promotion_piece'):
        score += piece_values[move['promotion_piece']]
        
    return score