import pygame as pg
import math
import copy
from typing import Dict, List, Tuple, Optional, Any
from engine import get_position, get_move, make_move, unmake_move
from ai import get_best_move

def main() -> None:
    """Main function to initialize and run the chess game."""
    height: int = 512

    width_board: int = height
    
    width: float = height * ((1+math.sqrt(5)) / 2)
    
    square_size: int = height // 8
    
    colors: Dict[str, Tuple] = {
        'fill': (255, 255, 255),
        'light_square': (235, 236, 209, 255),
        'dark_square': (129, 149, 88, 255),
        'button': (200, 200, 200),
        'button_hover': (180, 180, 180),
        'button_text': (0, 0, 0)
    }
    
    pieces: List[str] = [
        name + color for color in ['w', 'b'] 
                     for name in ['K', 'P', 'N', 'B', 'R', 'Q']
    ]
    
    piece_images: Dict[str, pg.Surface] = {
        piece: load_image(piece, square_size) for piece in pieces
    }
    
    keys: Dict[int, str] = {
        pg.K_k: 'N', pg.K_b: 'B', pg.K_r: 'R', pg.K_q: 'Q'
    }
    
    pg.init()
    
    screen: pg.Surface = pg.display.set_mode(size=(width, height))
    
    pg.display.set_caption("Chess")
    
    clock: pg.time.Clock = pg.time.Clock()
    
    ai_players: List[str] = select_players(
        screen, width, height, colors, clock
    )
    
    ui_vars: Dict[str, Any] = ui_defaults()
    
    fen: str = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    
    position_log: List[Dict[str, Any]] = []
    
    position: Dict[str, Any] = get_position(fen, position_log)
    
    game_state: Dict[str, Any] = {
        'position': position,
        'position_log': position_log,
        'ui_vars': ui_vars,
        'game_over': False,
        'ai_players': ai_players
    }

    run_game(
        screen, 
        clock, 
        game_state, 
        colors, 
        piece_images, 
        square_size, 
        width_board, 
        height,
        keys
    )
    
    pg.quit()

def run_game(
    screen: pg.Surface,
    clock: pg.time.Clock,
    game_state: Dict[str, Any],
    colors: Dict[str, Tuple],
    piece_images: Dict[str, pg.Surface],
    square_size: int,
    width_board: int,
    height: int,
    keys: Dict[int, str]
) -> Dict[str, Any]:
    """
    Run the main game loop.
    Returns the final game state.
    """
    running: bool = True
    
    # Create a local copy of the game state to avoid modifying the original
    current_state = game_state.copy()
    position = current_state['position']
    position_log = current_state['position_log']
    ui_vars = current_state['ui_vars']
    game_over = current_state['game_over']
    ai_players = current_state['ai_players']
    
    while running:
        is_human_turn: bool = position['active_color'] not in ai_players
        
        if is_human_turn or game_over:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                elif event.type == pg.MOUSEBUTTONDOWN:
                    click_location: Tuple[int, int] = pg.mouse.get_pos()
                    
                    ui_vars = handle_click(
                        click_location, 
                        ui_vars, 
                        square_size, 
                        position
                    )
                elif event.type == pg.MOUSEBUTTONUP:
                    click_location: Tuple[int, int] = (0, 0)
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_z and len(position_log) > 0:
                        position, position_log = unmake_move(position_log)
                        
                        ui_vars['promotion_piece_needed'] = False
                        
                        game_over = False
                    
                    if ui_vars['promotion_piece_needed']:
                        if event.key in keys:
                            ui_vars['move'].update(
                                {'promotion_piece': keys[event.key]}
                            )
        else:
            # AI's turn
            ui_vars['move'] = get_best_move(position)
                
        if (ui_vars['move'] is not None 
                and ui_vars['move'] in position['legal_moves']):
            position, position_log = make_move(
                position, 
                ui_vars['move'],
                position_log
            )
            
            animate_move(
                ui_vars['move'], 
                position_log[-1]['piece_map'], 
                screen,
                clock,
                colors, 
                piece_images, 
                square_size
            )
            
            ui_vars = ui_defaults()
                
        game_over = (
            len(position['legal_moves']) == 0 or position['fifty_moves']
        )
        
        draw_game(
            screen, 
            position,
            ui_vars['square_selected'],
            colors, 
            piece_images, 
            square_size
        )
        
        if ui_vars['promotion_piece_needed']:
            draw_message(
                ('Select piece:', 'q; r; b; k'), 
                screen, 
                width_board, 
                height
            )
            
        if game_over:
            winner: str = (
                'Black' if position['active_color'] == 'w' else 'White'
            )
            
            message: Optional[Tuple[str, str]] = None
            if position['checkmate']:
                message = ('Checkmate:', winner + ' wins!')
            elif position['stalemate']:
                message = ('Stalemate:', "It's a draw!")
            elif position['fifty_moves']:
                message = ('Fifty-move rule:', "It's a draw!")
            else:
                message = ('Game over:', "It's a draw!")
                
            if message:
                draw_message(message, screen, width_board, height)
        
        # Update the local state variables
        current_state = {
            'position': position,
            'position_log': position_log,
            'ui_vars': ui_vars,
            'game_over': game_over,
            'ai_players': ai_players
        }
        
        clock.tick(15)
        
        pg.display.flip()
    
    # Return the final game state
    return current_state

def select_players(
    screen: pg.Surface, 
    width: float, 
    height: int, 
    colors: Dict[str, Tuple], 
    clock: pg.time.Clock
) -> List[str]:
    """
    Let the user select which players are controlled by AI.
    Returns a list containing 'w' and/or 'b' for AI-controlled players.
    """
    font: pg.font.Font = pg.font.SysFont('Arial', 20, True, False)
    title_font: pg.font.Font = pg.font.SysFont('Arial', 32, True, False)
    
    title: pg.Surface = title_font.render(
        "Select AI Players", True, pg.Color('black')
    )
    
    options: List[Dict[str, Any]] = [
        {"text": "Human vs Human", "value": []},
        {"text": "Human vs AI (Human: White)", "value": ['b']},
        {"text": "Human vs AI (Human: Black)", "value": ['w']},
        {"text": "AI vs AI", "value": ['w', 'b']}
    ]
    
    button_height: int = 50
    button_width: int = 350
    button_margin: int = 20
    
    buttons: List[Dict[str, Any]] = []
    for i, option in enumerate(options):
        total_height = len(options) * (button_height + button_margin)
        y_pos = (
            height 
                // 2 - total_height 
                // 2 + i * (button_height + button_margin)
        )
        buttons.append({
            "rect": pg.Rect(
                (width - button_width) // 2, y_pos, button_width, button_height
            ),
            "text": option["text"],
            "value": option["value"],
            "hover": False
        })
    
    selecting: bool = True
    result: List[str] = []
    
    while selecting:
        screen.fill(colors['fill'])
        
        # Draw title
        title_x = (width - title.get_width()) // 2
        screen.blit(title, (title_x, height // 4))
        
        # Handle events
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()
            elif event.type == pg.MOUSEBUTTONDOWN:
                for button in buttons:
                    if button["rect"].collidepoint(event.pos):
                        result = button["value"]
                        selecting = False
        
        # Update button hover states
        mouse_pos: Tuple[int, int] = pg.mouse.get_pos()
        for button in buttons:
            button["hover"] = button["rect"].collidepoint(mouse_pos)
        
        # Draw buttons
        for button in buttons:
            color = (
                colors['button_hover'] if button["hover"] 
                else colors['button']
            )
            pg.draw.rect(screen, color, button["rect"], border_radius=5)
            pg.draw.rect(
                screen, pg.Color('black'), button["rect"], 2, border_radius=5
            )
            
            text: pg.Surface = font.render(
                button["text"], True, colors['button_text']
            )
            text_rect: pg.Rect = text.get_rect(center=button["rect"].center)
            screen.blit(text, text_rect)
        
        pg.display.flip()
        clock.tick(30)
    
    return result

def load_image(piece: str, square_size: int) -> pg.Surface:
    """Load and scale a chess piece image."""
    image: pg.Surface = pg.transform.scale(
        pg.image.load('Pieces/' + piece + '.png'),
        (square_size, square_size)
    )
    
    return image

def ui_defaults() -> Dict[str, Any]:
    """Return default UI variables."""
    ui_vars: Dict[str, Any] = {
        'square_selected': (),
        'clicks': [],
        'move': None,
        'promotion_piece_needed': False
    }
    
    return ui_vars

def handle_click(
    click_location: Tuple[int, int], 
    ui_vars: Dict[str, Any], 
    square_size: int, 
    position: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle mouse click on the chess board."""
    square_selected, clicks, move, promotion_piece_needed = ui_vars.values()
    
    square_clicked: Tuple[int, int] = (
        click_location[1] // square_size,
        click_location[0] // square_size
    )
    
    if square_clicked == square_selected or square_clicked[1] >= 8:
        square_selected = ()
        clicks = []
    else:
        square_selected = square_clicked
        clicks.append(square_selected)
        
    if len(clicks) == 2:
        square_from, square_to = clicks
        
        move = get_move(
            square_from, 
            square_to, 
            position['piece_map']
        )
        
        if (move['is_promotion'] and 
                move['promotion_piece'] is None):
            promotion_piece_needed = True
        
        if move not in position['legal_moves'] and not promotion_piece_needed:
            clicks = [square_selected]
            
    ui_vars = {
        'square_selected': square_selected,
        'clicks': clicks,
        'move': move,
        'promotion_piece_needed': promotion_piece_needed
    }
    
    return ui_vars

def animate_move(
    move: Dict[str, Any], 
    piece_map_prev: List[List[str]], 
    screen: pg.Surface, 
    clock: pg.time.Clock, 
    colors: Dict[str, Tuple], 
    piece_images: Dict[str, pg.Surface], 
    square_size: int
) -> None:
    """Animate a chess piece moving from one square to another."""
    dr: int = move['row_to'] - move['row_from']
    dc: int = move['col_to'] - move['col_from']
    
    frame_count: int = 10
    
    for frame in range(frame_count + 1):
        # draw game before the move
        draw_board(screen, colors, square_size)
        draw_pieces(screen, piece_map_prev, piece_images, square_size)
        
        # erase the moved piece from its original square
        is_light_square = (move['row_from'] + move['col_from']) % 2 == 0
        color = (
            colors['light_square'] if is_light_square
            else colors['dark_square']
        )
        
        pg.draw.rect(
            screen, 
            color, 
            pg.Rect(
                move['col_from'] * square_size,
                move['row_from'] * square_size,
                square_size,
                square_size
            )
        )
        
        # draw piece at current moment in its journey
        row: float = move['row_from'] + dr * frame / frame_count
        col: float = move['col_from'] + dc * frame / frame_count
        
        screen.blit(
            piece_images[move['piece_moved']], 
            pg.Rect(
                col * square_size,
                row * square_size,
                square_size,
                square_size
            )
        )
        
        clock.tick(60)
        pg.display.flip()
        
    if move['is_castling']:
        king_origin: Tuple[int, int] = (move['row_from'], move['col_from'])
        king_location: Tuple[int, int] = (move['row_to'], move['col_to'])
        
        rook_col_from = 7 if move['col_to'] == 6 else 0
        rook_col_to = 5 if move['col_to'] == 6 else 3
        
        rook_location: Tuple[int, int] = (move['row_from'], rook_col_from)
        rook_destination: Tuple[int, int] = (move['row_to'], rook_col_to)
        
        move_copy: Dict[str, Any] = copy.deepcopy(move)
        piece_map_prev_copy: List[List[str]] = copy.deepcopy(piece_map_prev)
        
        piece_map_prev_copy[king_origin[0]][king_origin[1]] = '--'
        
        piece_map_prev_copy[king_location[0]][king_location[1]] = (
            move['piece_moved']
        )
        
        move_copy['col_from'] = rook_location[1]
        move_copy['col_to'] = rook_destination[1]
        move_copy['piece_moved'] = move_copy['piece_moved'].replace('K', 'R')
        move_copy['is_castling'] = False
        
        animate_move(
            move_copy, 
            piece_map_prev_copy,
            screen, 
            clock, 
            colors, 
            piece_images, 
            square_size
        )
        
def draw_game(
    screen: pg.Surface, 
    position: Dict[str, Any], 
    square_selected: Tuple[int, int], 
    colors: Dict[str, Tuple], 
    piece_images: Dict[str, pg.Surface], 
    square_size: int
) -> None:
    """Draw the complete game state on the screen."""
    draw_board(screen, colors, square_size)
    highlight_square(screen, position, square_selected, square_size)
    draw_pieces(screen, position['piece_map'], piece_images, square_size)
    show_possible_squares(
        screen, 
        square_selected, 
        position['legal_moves'], 
        square_size
    )
    
def draw_board(
    screen: pg.Surface, 
    colors: Dict[str, Tuple], 
    square_size: int
) -> None:
    """Draw the chess board."""
    screen.fill(colors['fill'])
    
    squares = []
    for row in range(8):
        for col in range(8):
            is_light = (row + col) % 2 == 0
            color = (
                colors['light_square'] if is_light else colors['dark_square']
            )
            squares.append({
                'color': color,
                'left': col * square_size,
                'top': row * square_size
            })
    
    for square in squares:
        pg.draw.rect(
            screen, 
            square['color'], 
            pg.Rect(
                square['left'], 
                square['top'], 
                square_size, 
                square_size
            )
        )
        
def highlight_square(
    screen: pg.Surface, 
    position: Dict[str, Any], 
    square_selected: Tuple[int, int], 
    square_size: int
) -> None:
    """Highlight the selected square."""
    if square_selected != ():
        row, col = square_selected
        
        if position['piece_map'][row][col][1] == position['active_color']:
            s: pg.Surface = pg.Surface((square_size, square_size))
            s.set_alpha(127)
            s.fill(pg.Color('yellow'))
            screen.blit(s, (col * square_size, row * square_size))
        
def draw_pieces(
    screen: pg.Surface, 
    piece_map: List[List[str]], 
    piece_images: Dict[str, pg.Surface], 
    square_size: int
) -> None:
    """Draw all chess pieces on the board."""
    occupied_squares = []
    for row in range(8):
        for col in range(8):
            if piece_map[row][col] != '--':
                occupied_squares.append((row, col))
    
    for row, col in occupied_squares:
        piece: str = piece_map[row][col]
        screen.blit(
            piece_images[piece], 
            pg.Rect(
                col * square_size, 
                row * square_size, 
                square_size, 
                square_size
            )
        )
        
def show_possible_squares(
    screen: pg.Surface, 
    square_selected: Tuple[int, int], 
    legal_moves: List[Dict[str, Any]], 
    square_size: int
) -> None:
    """Show dots on squares where the selected piece can move."""
    if square_selected != ():
        possible_moves = [
            move for move in legal_moves 
            if (move['row_from'], move['col_from']) == square_selected
        ]
        
        for move in possible_moves:
            center_x = (move['col_to'] + 0.5) * square_size
            center_y = (move['row_to'] + 0.5) * square_size
            pg.draw.circle(
                screen, 
                pg.Color('gray'),
                (center_x, center_y),
                square_size / 8
            )
        
def draw_message(
    message: Tuple[str, str], 
    screen: pg.Surface, 
    width_board: int, 
    height: int
) -> None:
    """Draw a message on the screen."""
    location_names = ['sidebar-message-hi', 'sidebar-message-lo']
    
    for i in range(len(message)):
        draw_text(
            message[i],
            screen,
            14,
            location_names[i],
            width_board,
            height
        )
        
def draw_text(
    text: str, 
    screen: pg.Surface, 
    size: int, 
    location_name: str, 
    width_board: int, 
    height: int
) -> None:
    """Draw text at a specific location on the screen."""
    font: pg.font.Font = pg.font.SysFont('Garamond', size, True, False)
    text_object: pg.Surface = font.render(text, True, pg.Color('black'))
    
    locations: Dict[str, Tuple[int, int]] = {
        'sidebar-message-hi': (
            width_board + 4, 
            int(height/2 - text_object.get_height())
        ),
        'sidebar-message-lo': (width_board + 4, int(height / 2))
    }
    
    screen.blit(text_object, locations[location_name])

if __name__ == '__main__':
    main()