
from enum import Enum, IntEnum
from typing import Any, TypedDict, NotRequired, Literal
from utils.helpers import sign
from copy import deepcopy

class ChessMoveExtraInfo(TypedDict):
    promotion_choice : NotRequired['PieceType']

class ChessMove(TypedDict):
    start_pos : tuple[int, int]
    end_pos : tuple[int, int]
    extra_info : ChessMoveExtraInfo

class TeamType(IntEnum):
    WHITE = 0
    BLACK = 1

    def opposite(self) -> 'TeamType':
        return TeamType.WHITE if self.value == 1 else TeamType.BLACK

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

    def get_color(self) -> TeamType|None:
        if self.value == 0: return None
        return TeamType.WHITE if self.value <= 6 else TeamType.BLACK


class ChessGame:
    def __init__(self):
        self.current_turn : TeamType = TeamType.WHITE
        self.board : list[list[PieceType]] = self.make_new_board()
        self.castling_rights : dict[TeamType, list[bool]] = {TeamType.WHITE : [True, True], TeamType.BLACK : [True, True]}
        self.captured_pieces : dict[TeamType, list[PieceType]] = {TeamType.WHITE : [], TeamType.BLACK : []}
        self.en_passant : tuple[tuple[int, int], tuple[int, int]]|None = None
    
    def copy(self) -> 'ChessGame':
        new_game = ChessGame()
        new_game.current_turn = self.current_turn
        new_game.board = deepcopy(self.board)
        new_game.castling_rights = deepcopy(self.castling_rights)
        new_game.captured_pieces = deepcopy(self.captured_pieces)
        new_game.en_passant = self.en_passant
        return new_game
    
    def make_move(self, start_pos : tuple[int, int], end_pos : tuple[int, int], bonus_info : ChessMoveExtraInfo,
                  simulation : bool = False) -> list[dict[str, Any]]|Literal[False]:
        bonus_instructions : list[dict[str, Any]] = []
        if not simulation:
            if not self.validate_move(start_pos, end_pos, bonus_info): return False
        PT = PieceType
        selected : PieceType = self.get_at(*start_pos)
        team : TeamType = selected.get_color()
        if selected == PT.EMPTY:
            return False
        target : PieceType = self.get_at(*end_pos)
        if target != PT.EMPTY:
            self.captured_pieces[target.get_color()].append(target)
            bonus_instructions.append({'type' : 'capture_at', 'pos' : end_pos})
        self.set_at(*end_pos, selected)
        self.set_at(*start_pos, PieceType.EMPTY)
        target_en_passant : tuple[int, int]|None = None if self.en_passant is None else self.en_passant[0]
        if selected == PT.WHITE_PAWN:
            if end_pos[1] == 8:
                promotion_choice : PieceType = bonus_info.get('promotion_choice', PT.WHITE_QUEEN)
                self.set_at(*end_pos, promotion_choice)
                bonus_instructions.append({'type' : 'change_type', 'pos' : end_pos, 'new_type' : promotion_choice})
            
            if target_en_passant is not None:
                if target_en_passant[0] == end_pos[0] and target_en_passant[1] == end_pos[1]:
                    self.set_at(*(self.en_passant[1]), PT.EMPTY)
                    bonus_instructions.append({'type' : 'capture_at', 'pos' : self.en_passant[1]})

        elif selected == PT.BLACK_PAWN:
            if end_pos[1] == 1:
                promotion_choice : PieceType = bonus_info.get('promotion_choice', PT.BLACK_QUEEN)
                self.set_at(*end_pos, promotion_choice)
                bonus_instructions.append({'type' : 'change_type', 'pos' : end_pos, 'new_type' : promotion_choice})
            
            if target_en_passant is not None:
                if target_en_passant[0] == end_pos[0] and target_en_passant[1] == end_pos[1]:
                    self.set_at(*(self.en_passant[1]), PT.EMPTY)
                    bonus_instructions.append({'type' : 'capture_at', 'pos' : self.en_passant[1]})
            

        elif selected == PT.WHITE_ROOK or selected == PT.BLACK_ROOK:
            team = selected.get_color()
            if start_pos[0] == 1: self.castling_rights[team][0] = False
            if start_pos[0] == 8: self.castling_rights[team][1] = False
        
        elif selected == PT.BLACK_KING:
            self.castling_rights[team] = [False, False]
            if abs(start_pos[0] - end_pos[0]) >= 2:
                direction_x : int = int(sign(end_pos[0] - start_pos[0]))
                rook_x : int = end_pos[0] - direction_x
                rook_y : int = 8
                og_x : int = 8 if end_pos[0] > 5 else 1
                og_y = rook_y
                self.set_at(rook_x, rook_y, PT.BLACK_ROOK)
                self.set_at(og_x, og_y, PT.EMPTY)
                bonus_instructions.append({'type' : 'move_piece_to', 'start_pos' : (og_x, og_y), 'end_pos' : (rook_x, rook_y)})

        elif selected == PT.WHITE_KING:
            self.castling_rights[team] = [False, False]
            if abs(start_pos[0] - end_pos[0]) >= 2:
                direction_x : int = int(sign(end_pos[0] - start_pos[0]))
                rook_x : int = end_pos[0] - direction_x
                rook_y : int = 1
                og_x : int = 8 if end_pos[0] > 5 else 1
                og_y = rook_y
                self.set_at(rook_x, rook_y, PT.WHITE_ROOK)
                self.set_at(og_x, og_y, PT.EMPTY)
                bonus_instructions.append({'type' : 'move_piece_to', 'start_pos' : (og_x, og_y), 'end_pos' : (rook_x, rook_y)})

        self.change_turn()
        self.en_passant = None
        if selected in {PT.WHITE_PAWN, PT.BLACK_PAWN}:
            delta_y : int = end_pos[1] - start_pos[1]
            abs_x : int = abs(end_pos[0] - start_pos[0])
            abs_y : int = abs(delta_y)
            direction_y : int = int(sign(delta_y))
            if abs_y == 2 and abs_x == 0:
                self.en_passant = ((start_pos[0], start_pos[1] + direction_y), end_pos)
        if simulation: return bonus_instructions
        in_check : bool = self.is_check()
        has_legal_move : bool = self.has_legal_move()
        #print(has_legal_move)
        if in_check and has_legal_move:
            bonus_instructions.append({'type' : 'check'})
        elif in_check and not has_legal_move:
            bonus_instructions.append({'type' : 'checkmate'})
        elif not in_check and not has_legal_move:
            bonus_instructions.append({'type' : 'stalemate'})
        else:
            if not (self.has_checkmating_material(TeamType.WHITE) or self.has_checkmating_material(TeamType.BLACK)):
                bonus_instructions.append({'type' : 'insufficent_material'})
        return bonus_instructions
    
    def will_end_turn_in_check(self, start_pos : tuple[int, int], end_pos : tuple[int, int], bonus_info : ChessMoveExtraInfo) -> bool:
        alternate_reality = self.copy()
        alternate_reality.make_move(start_pos, end_pos, bonus_info, simulation=True)
        alternate_reality.change_turn()
        if alternate_reality.is_check(): return True
        return False
    
    def has_legal_move(self, team : TeamType|None = None) -> bool:
        team = team or self.current_turn
        for coords, piece in self.get_all_pieces().items():
            if piece.get_color() != team: continue
            for end_y in range(1, 8 + 1):
                for end_x in range(1, 8 + 1):
                    if self.validate_move(coords, (end_x, end_y), {}):
                        return (coords, (end_x, end_y))
        return False

    def has_checkmating_material(self, team : TeamType|None = None) -> bool:
        team = team or self.current_turn
        piece_count : dict[PieceType, int] = {piece : 0 for piece in PieceType}
        piece_total : int = 0
        for coords, piece in self.get_all_pieces().items():
            if piece.get_color() != team: continue
            if piece == PieceType.WHITE_KING or piece == PieceType.BLACK_KING: continue
            if piece.value % 6 in {1, 4, 5}: return True
            piece_count[piece] += 1
            piece_total += 1
            if piece_total >= 3: return True
            if piece_total == 2 and (piece_count[PieceType.WHITE_KNIGHT] + piece_count[PieceType.BLACK_KNIGHT]) < 2: return True
        return False


    def is_check(self, defending_team : TeamType|None = None) -> bool:
        defending_team = defending_team or self.current_turn
        defending_king_pos : tuple[int, int] = self.get_kings()[defending_team]
        return self.is_square_attacked(*defending_king_pos, defending_team.opposite())
    
    def is_square_attacked(self, target_x : int, target_y : int, attacking_team : TeamType) -> bool:
        for coords, piece in self.get_all_pieces().items():
            if piece.get_color() != attacking_team: continue
            valid_attack : bool = self.validate_movement(coords, (target_x, target_y), piece)
            if valid_attack: return True
        return False
    
    def validate_move(self, start_pos : tuple[int, int], end_pos : tuple[int, int], bonus_info : ChessMoveExtraInfo, return_true : bool = False,
                      verify_turn_end_check : bool = True) -> bool:
        #teamkilling
        #turnorder
        if return_true: return True
        PT = PieceType
        selected_piece : PieceType = self.get_at(*start_pos)
        if selected_piece == PieceType.EMPTY: return False
        team : TeamType = selected_piece.get_color()
        if (team != self.current_turn): return False
        if start_pos[0] == end_pos[0] and start_pos[1] == end_pos[1]: return False
        target : PieceType|None = self.get_at(*end_pos)
        if (target.get_color() == selected_piece.get_color()) and target is not None: return False
        movement_is_valid : bool = self.validate_movement(start_pos, end_pos, selected_piece)
        if not movement_is_valid: return False
        if verify_turn_end_check:
            if self.will_end_turn_in_check(start_pos, end_pos, bonus_info): return False
        return True
    
    def validate_movement(self, start_pos : tuple[int, int], end_pos : tuple[int, int], piece : PieceType) -> bool:
        team = piece.get_color()
        if team is None: return False
        PT = PieceType
        match piece:
            case PT.WHITE_ROOK|PT.BLACK_ROOK:
                movement_is_valid = self.validate_rook_movement(start_pos, end_pos, team)
            case PT.WHITE_BISHOP|PT.BLACK_BISHOP:
                movement_is_valid = self.validate_bishop_movement(start_pos, end_pos, team)
            case PT.WHITE_KNIGHT|PT.BLACK_KNIGHT:
                movement_is_valid = self.validate_knight_movement(start_pos, end_pos, team)
            case PT.WHITE_QUEEN|PT.BLACK_QUEEN:
                movement_is_valid = self.validate_queen_movement(start_pos, end_pos, team)
            case PT.WHITE_PAWN|PT.BLACK_PAWN:
                movement_is_valid = self.validate_pawn_movement(start_pos, end_pos, team)
            case PT.WHITE_KING|PT.BLACK_KING:
                movement_is_valid = self.validate_king_movement(start_pos, end_pos, team)
            case _:
                movement_is_valid = False
        return movement_is_valid

    def validate_rook_movement(self, start_pos : tuple[int, int], end_pos : tuple[int, int], team : TeamType) -> bool:
        delta_x : int = end_pos[0] - start_pos[0]
        delta_y : int = end_pos[1] - start_pos[1]
        abs_x : int = abs(delta_x)
        abs_y : int = abs(delta_y)
        direction_x : int = int(sign(delta_x))
        direction_y : int = int(sign(delta_y))
        if abs_x > 0 and abs_y > 0: return False
        if abs_x == 0 and abs_y == 0: return False
        x, y = start_pos
        while (True):
            x += direction_x
            y += direction_y
            current_tile : PieceType = self.get_at(x, y)
            if x == end_pos[0] and y == end_pos[1]:
                return team != current_tile.get_color()
            if current_tile != PieceType.EMPTY:
                return False
        return False
    
    def validate_bishop_movement(self, start_pos : tuple[int, int], end_pos : tuple[int, int], team : TeamType) -> bool:
        delta_x : int = end_pos[0] - start_pos[0]
        delta_y : int = end_pos[1] - start_pos[1]
        abs_x : int = abs(delta_x)
        abs_y : int = abs(delta_y)
        direction_x : int = int(sign(delta_x))
        direction_y : int = int(sign(delta_y))
        if abs_x != abs_y: return False
        if abs_x == 0: return False
        x, y = start_pos
        while (True):
            x += direction_x
            y += direction_y
            current_tile : PieceType = self.get_at(x, y)
            if x == end_pos[0] and y == end_pos[1]:
                return team != current_tile.get_color()
            if current_tile != PieceType.EMPTY:
                return False
        return False

    def validate_queen_movement(self, start_pos : tuple[int, int], end_pos : tuple[int, int], team : TeamType) -> bool:
        return self.validate_rook_movement(start_pos, end_pos, team) or self.validate_bishop_movement(start_pos, end_pos, team)
    
    def validate_knight_movement(self, start_pos : tuple[int, int], end_pos : tuple[int, int], team : TeamType) -> bool:
        delta_x : int = end_pos[0] - start_pos[0]
        delta_y : int = end_pos[1] - start_pos[1]
        abs_x : int = abs(delta_x)
        abs_y : int = abs(delta_y)
        if (abs_x not in {1, 2}) or (abs_y not in {1, 2}): return False
        if abs_x == abs_y: return False
        return team != self.get_piece_color(self.get_at(*end_pos))
    
    def validate_king_movement(self, start_pos : tuple[int, int], end_pos : tuple[int, int], team : TeamType) -> bool:
        delta_x : int = end_pos[0] - start_pos[0]
        delta_y : int = end_pos[1] - start_pos[1]
        abs_x : int = abs(delta_x)
        abs_y : int = abs(delta_y)
        if abs_x == 0 and abs_y == 0: return False
        if abs_y > 1: return False
        if abs_x > 2: return False
        if abs_x <= 1:
            return team != self.get_piece_color(self.get_at(*end_pos))
        if abs_x == 2 and abs_y > 0: return False
        return self.validate_castling(start_pos, end_pos, team)
    
    def validate_castling(self, start_pos : tuple[int, int], end_pos : tuple[int, int], team : TeamType) -> bool:
        if not any(self.castling_rights[team]): return False
        if self.is_check(defending_team=team): return False
        delta_x : int = end_pos[0] - start_pos[0]
        delta_y : int = end_pos[1] - start_pos[1]
        abs_x : int = abs(delta_x)
        abs_y : int = abs(delta_y)
        direction_x : int = int(sign(delta_x))
        if direction_x == 1:
            if not self.castling_rights[team][1]: return False
        elif direction_x == -1:
            if not self.castling_rights[team][0]: return False
        match team:
            case TeamType.WHITE:
                Y_LEVEL = 1
                if start_pos[0] != 5 or start_pos[1] != Y_LEVEL: return False
                if direction_x == 1:
                    if self.get_at(8, Y_LEVEL) != PieceType.WHITE_ROOK: return False
                elif direction_x == -1:
                    if self.get_at(1,Y_LEVEL) != PieceType.WHITE_ROOK: return False
                if any(self.is_square_attacked(x, Y_LEVEL, TeamType.BLACK) for x in range(5, 5 + direction_x * 3)):
                    return False
            case TeamType.BLACK:
                Y_LEVEL = 8
                #print('break1')
                if start_pos[0] != 5 or start_pos[1] != Y_LEVEL: return False
                #print('break2')
                if direction_x == 1:
                    if self.get_at(8, Y_LEVEL) != PieceType.BLACK_ROOK: return False
                
                elif direction_x == -1:
                    if self.get_at(1,Y_LEVEL) != PieceType.BLACK_ROOK: return False
                #print('break_3')
                if any(self.is_square_attacked(x, Y_LEVEL, TeamType.WHITE) for x in range(5, 5 + direction_x * 3)):
                    return False
        #print('break4')
        return True
    
    def validate_pawn_movement(self, start_pos : tuple[int, int], end_pos : tuple[int, int], team : TeamType) -> bool:
        delta_x : int = end_pos[0] - start_pos[0]
        delta_y : int = end_pos[1] - start_pos[1]
        abs_x : int = abs(delta_x)
        abs_y : int = abs(delta_y)
        direction_x : int = int(int(sign(delta_x)))
        direction_y : int = int(int(sign(delta_y)))
        if abs_x > 1: return False
        if abs_y > 2: return False
        if abs_y == 0: return False
        target : PieceType = self.get_at(*end_pos)
        if team == TeamType.WHITE:
            if direction_y == -1: return False
            if abs_y == 2 and (start_pos[1] != 2 or abs_x != 0 or target != PieceType.EMPTY): return False
        else:
            if direction_y == 1: return False
            if abs_y == 2 and (start_pos[1] != 7 or abs_x != 0 or target != PieceType.EMPTY): return False
        if abs_x == 0: #we are moving forwards
            if abs_y == 1:
                return target == PieceType.EMPTY
            else:
                return (target == PieceType.EMPTY
                        and self.get_at(start_pos[0], start_pos[1] + direction_y)) == PieceType.EMPTY
        else:
            if (self.get_at(*end_pos) == PieceType.EMPTY):
                if self.en_passant is None: return False
                target_en_passant : tuple[int, int] = self.en_passant[0]
                if not (end_pos[0] == target_en_passant[0] and end_pos[1] == target_en_passant[1]): return False
            if self.get_piece_color(self.get_at(*end_pos)) == team: return False
            return True
    
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
        result_dict : dict[tuple[int, int], PieceType] = {}
        for y in range(8):
            for x in range(8):
                current : PieceType = self.board[y][x]
                if current != PieceType.EMPTY:
                    result_dict[(x + 1, y + 1)] = current
        return result_dict
    
    def get_kings(self) -> dict[TeamType, tuple[int, int]]:
        result_dict : dict[TeamType, tuple[int, int]] = {}
        for y in range(8):
            for x in range(8):
                current : PieceType = self.board[y][x]
                if current == PieceType.WHITE_KING:
                    result_dict[TeamType.WHITE] = (x + 1, y + 1)
                elif current == PieceType.BLACK_KING:
                    result_dict[TeamType.BLACK] = (x + 1, y + 1)
        return result_dict

def number_to_string_coord(x : int, y : int):
    return 'abcdefgh'[x-1] + f'{y}' if (1 <= x <= 8) and (type(x) == int) else '??'