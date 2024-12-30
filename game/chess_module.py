
from enum import Enum, IntEnum
from typing import Any, TypedDict, NotRequired, Literal
from utils.helpers import sign

class ChessMoveExtraInfo(TypedDict):
    promotion_choice : NotRequired[int]


class ChessMove(TypedDict):
    start_pos : tuple[int, int]
    end_pos : tuple[int, int]
    extra_info : ChessMoveExtraInfo

class TeamType(IntEnum):
    WHITE = 0
    BLACK = 1

class PieceType(IntEnum):
    EMPTY = 0

    WHITE_ROOK = 1
    WHITE_KNIGHT = 2
    WHITE_BISHOP = 3
    WHITE_QUEEN = 4
    WHITE_KING = 5
    WHITE_PAWN = 6

    BLACK_ROOK = 7
    BLACK_KNIGHT = 8
    BLACK_BISHOP = 9
    BLACK_QUEEN = 10
    BLACK_KING = 11
    BLACK_PAWN = 12


class ChessGame:
    def __init__(self):
        self.current_turn : TeamType = TeamType.WHITE
        self.board : list[list[PieceType]] = self.make_new_board()
        self.castling_rights : dict[TeamType, bool] = {TeamType.WHITE : True, TeamType.BLACK : True}
        self.captured_pieces : dict[TeamType, list[PieceType]] = {TeamType.WHITE : [], TeamType.BLACK : []}
    
    def make_move(self, start_pos : tuple[int, int], end_pos : tuple[int, int], bonus_info : ChessMoveExtraInfo) -> list[dict[str, Any]]|Literal[False]:
        bonus_instructions : list[dict[str, Any]] = []
        PT = PieceType
        selected : PieceType = self.get_at(*start_pos)
        if selected == PT.EMPTY:
            return False
        target : PieceType = self.get_at(*end_pos)
        if target != PT.EMPTY:
            self.captured_pieces[self.get_piece_color(target)].append(target)
            bonus_instructions.append({'type' : 'capture_at', 'pos' : end_pos})
        self.set_at(*end_pos, selected)
        self.change_turn()
        return bonus_instructions
    
    def validate_move(self, start_pos : tuple[int, int], end_pos : tuple[int, int], bonus_info : ChessMoveExtraInfo, return_true : bool = False) -> bool:
        if return_true: return True
        selected_piece : PieceType = self.get_at(*start_pos)
        if selected_piece == PieceType.EMPTY: return False
        if self.get_piece_color(selected_piece) != self.current_turn: return False
        if start_pos[0] == end_pos[0] and start_pos[1] == end_pos[1]: return False
        target : PieceType|None = self.get_at(*end_pos)
        if (self.get_piece_color(target) == self.get_piece_color(selected_piece)) and target is not None: return False
        return True
    
    def validate_rook_movement(self, start_pos : tuple[int, int], end_pos : tuple[int, int], team : TeamType) -> bool:
        delta_x : int = end_pos[0] - start_pos[0]
        delta_y : int = end_pos[1] - start_pos[1]
        abs_x : int = abs(delta_x)
        abs_y : int = abs(delta_y)
        direction_x : int = sign(delta_x)
        direction_y : int = sign(delta_y)
        if abs_x > 0 and abs_y > 0: return False
        if abs_x == 0 and abs_y == 0: return False
        x, y = start_pos
        while (True):
            x += direction_x
            y += direction_y
            current_tile : PieceType = self.get_at(x, y)
            if x == end_pos[0] and y == end_pos[1]:
                return team != self.get_piece_color(current_tile)
            if current_tile != PieceType.EMPTY:
                return False
        return False
    
    def validate_bishop_movement(self, start_pos : tuple[int, int], end_pos : tuple[int, int], team : TeamType) -> bool:
        delta_x : int = end_pos[0] - start_pos[0]
        delta_y : int = end_pos[1] - start_pos[1]
        abs_x : int = abs(delta_x)
        abs_y : int = abs(delta_y)
        direction_x : int = sign(delta_x)
        direction_y : int = sign(delta_y)
        if abs_x != abs_y: return False
        if abs_x == 0: return False
        x, y = start_pos
        while (True):
            x += direction_x
            y += direction_y
            current_tile : PieceType = self.get_at(x, y)
            if x == end_pos[0] and y == end_pos[1]:
                return team != self.get_piece_color(current_tile)
            if current_tile != PieceType.EMPTY:
                return False
        return False

    def validate_queen_movement(self, start_pos : tuple[int, int], end_pos : tuple[int, int], team : TeamType) -> bool:
        return self.validate_rook_movement(start_pos, end_pos, team) or self.validate_bishop_movement(start_pos, end_pos, team)


    
    def change_turn(self):
        self.current_turn = TeamType.WHITE if self.current_turn == TeamType.BLACK else TeamType.BLACK
    
    @staticmethod
    def get_piece_color(piece : PieceType) -> TeamType|None:
        if piece == PieceType.EMPTY: return None
        return TeamType.WHITE if (1 <= piece.value <= 6) else TeamType.BLACK

    @staticmethod
    def make_new_board() -> list[list[PieceType]]:
        p = PieceType
        return [
        [p.WHITE_ROOK, p.WHITE_KNIGHT, p.WHITE_BISHOP, p.WHITE_QUEEN, p.WHITE_KING, p.WHITE_BISHOP, p.WHITE_KNIGHT, p.WHITE_ROOK],
        [p.WHITE_PAWN for _ in range(8)],
        [p.EMPTY for _ in range(8)],
        [p.EMPTY for _ in range(8)],
        [p.EMPTY for _ in range(8)],
        [p.EMPTY for _ in range(8)],
        [p.BLACK_PAWN for _ in range(8)],
        [p.BLACK_ROOK, p.BLACK_KNIGHT, p.BLACK_BISHOP, p.BLACK_QUEEN, p.BLACK_KING, p.BLACK_BISHOP, p.BLACK_KNIGHT, p.BLACK_ROOK],
        ]
    
    def get_at(self, x : int, y : int) -> PieceType:
        return self.board[y - 1][x - 1]
    
    def set_at(self, x : int, y : int, new_val : PieceType):
        self.board[y - 1][x - 1] = new_val
    
    def get_all_pieces(self) -> dict[tuple[int, int], PieceType]:
        result_dict : dict[PieceType, tuple[int, int]] = {}
        for y in range(8):
            for x in range(8):
                current : PieceType = self.board[y][x]
                if current != PieceType.EMPTY:
                    result_dict[(x + 1, y + 1)] = current
        return result_dict


def number_to_string_coord(x : int, y : int):
    return 'abcdefgh'[x-1] + f'{y}' if (1 <= x <= 8) and (type(x) == int) else '??'