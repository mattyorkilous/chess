from typing import List, Optional, Tuple

def get_piece_map_row(fen_row: str) -> List[str]:
    piece_map_row = [
        item for char in fen_row
             for item in (
                     ['--' for _ in range(int(char))] if char.isdigit()
                     else [char.upper() + 'b'] if char.islower()
                     else [char + 'w']
             )
    ]
    return piece_map_row

def get_square(square_name: str) -> Optional[Tuple[int, int]]:
    if square_name in ('-', '--'):
        return None
    
    file, rank = square_name
    row = 8 - int(rank)
    col = ord(file) - 97
    
    return (row, col)

def get_square_name(square: Tuple[int, int]) -> str:
    rank, file = square
    rank_name = str(8 - rank)
    file_name = chr(97 + file)
    return file_name + rank_name