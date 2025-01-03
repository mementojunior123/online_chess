import pygame
from game.sprite import Sprite
from core.core import core_object

import game.chess_module as chess_module
from enum import Enum
from utils.helpers import convert_alpha_to_colorkey
from utils.my_timer import Timer
from typing import Union

class BoardDisplayStyle(Enum):
    STANDARD = 'Standard'
    BLACK_STANDARD = 'BlackStandard'
    BLACK_MIRRORED = 'BlackMirrored'

class ChessBoard(Sprite):
    TILE_SIZE = 61
    IMAGE_SIZE = 60
    LIGHT_COLOR = '#ffffdd'
    DARK_COLOR = '#86a666'
    test_image = pygame.surface.Surface((TILE_SIZE * 8, TILE_SIZE * 8))
    pygame.draw.rect(test_image, DARK_COLOR, (0, 0, *test_image.get_size()))
    inactive_elements : list['ChessBoard'] = []
    active_elements : list['ChessBoard'] = []
    def __init__(self):
        super().__init__()
        self.display_style : BoardDisplayStyle
        self.pieces : list[ChessPiece]
        self.game : chess_module.ChessGame
        ChessBoard.inactive_elements.append(self)

    @classmethod
    def spawn(cls, display_style : BoardDisplayStyle = BoardDisplayStyle.STANDARD):
        element = cls.inactive_elements[0]
        element.display_style = display_style
        element.image = cls.make_empty_board(cls.LIGHT_COLOR, cls.DARK_COLOR, cls.TILE_SIZE, element.display_style)
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(480, 270)
        element.align_rect()
        element.zindex = -1
        
        element.game = chess_module.ChessGame()
        element.pieces = [ChessPiece.spawn(element, piece, element.board_to_visual_coords(*coords, element.display_style)) 
                          for coords, piece in (element.game.get_all_pieces()).items()]
        

        cls.unpool(element)
        return element
    
    def get_at(self, visual_coords : tuple[int, int], ignore : int = 0) -> Union['ChessPiece',None]:
        for piece in self.pieces:
            if piece.captured: continue
            if piece.visual_coords[0] == visual_coords[0] and piece.visual_coords[1] == visual_coords[1]:
                if ignore: ignore -= 1
                else: return piece
        return None
    
    def get_at_board_coords(self, board_coords : tuple[int, int], ignore : int = 0) -> Union['ChessPiece',None]:
        return self.get_at(self.board_to_visual_coords(*board_coords, self.display_style), ignore=ignore)

    
    def add_piece(self, piece_type : chess_module.PieceType, visual_coords : tuple[int, int]):
        self.pieces.append(ChessPiece.spawn(self, piece_type, visual_coords))
    
    def remove_piece(self, piece : 'ChessPiece'):
        if piece in self.pieces: self.pieces.remove(piece)

    def update(self, delta : float):
        to_remove : list[ChessPiece] = []
        for piece in self.pieces:
            if not piece.active:
                to_remove.append(piece)
        for piece in to_remove:
            self.remove_piece(piece)
    
    @staticmethod
    def make_empty_board(light_color : pygame.Color|str, dark_color : pygame.Color|str, tile_size : int, style : BoardDisplayStyle) -> pygame.Surface:
        reverse : bool = False
        mirror_horizontal : bool = False
        if style in {BoardDisplayStyle.BLACK_MIRRORED}:
            reverse = True
        COLORS : list[pygame.Color|str] = [light_color, dark_color]
        new_surf : pygame.Surface = pygame.Surface((tile_size * 8, tile_size * 8))
        for y in range(8):
            for x in range(8):
                color_index : int = (x + y + int(reverse) + int(mirror_horizontal)) % 2
                tile_color = COLORS[color_index]
                pygame.draw.rect(new_surf, tile_color, (x * tile_size, y * tile_size, tile_size, tile_size))
        return new_surf

    @staticmethod
    def board_to_visual_coords(x : int, y : int, style : BoardDisplayStyle) -> tuple[int, int]:
        new_x : int = x if style in {BoardDisplayStyle.STANDARD, BoardDisplayStyle.BLACK_MIRRORED} else 9 - x
        new_y : int = 9 - y if style in {BoardDisplayStyle.STANDARD} else y
        return (new_x - 1, new_y - 1)
    
    @staticmethod
    def visual_to_board_coords(x : int, y : int, style : BoardDisplayStyle) -> tuple[int, int]:
        x += 1
        y += 1
        new_x : int = x if style in {BoardDisplayStyle.STANDARD, BoardDisplayStyle.BLACK_MIRRORED} else 9 - x
        new_y : int = 9 - y if style in {BoardDisplayStyle.STANDARD} else y
        return (new_x, new_y)
    
    def visual_to_real_coords_topleft(self, x : int, y : int) -> tuple[int, int]:
        TS = ChessBoard.TILE_SIZE
        return pygame.Vector2(x * TS, y * TS) + pygame.Vector2(self.rect.topleft)

    def visual_to_real_coords_center(self, x : int, y : int) -> tuple[int, int]:
        TS = ChessBoard.TILE_SIZE
        return pygame.Vector2(x * TS, y * TS) + pygame.Vector2(self.rect.topleft) + pygame.Vector2(TS // 2, TS // 2)
    
    def real_to_visual_coords(self, x : int, y : int) -> tuple[int, int]:
        TS = ChessBoard.TILE_SIZE
        rel_x, rel_Y = pygame.Vector2(x, y) - pygame.Vector2(self.rect.topleft)
        return (int(rel_x // TS), int(rel_Y // TS))
    
    def capture_to_real_pos(self, x : int, y : int) -> tuple[int, int]:
        return self.rect.midright + pygame.Vector2(100, 0)

    @classmethod
    def receive_events(cls, event : pygame.Event):
        if event.type in {pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP}:
            for element in cls.active_elements:
                element.handle_mouse_event(event)

    def handle_mouse_event(self, event : pygame.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            click_pos : tuple[int, int] = event.pos
            vis_coords = self.real_to_visual_coords(*click_pos)
            board_coords = self.visual_to_board_coords(*vis_coords, self.display_style)
            #print(f'{vis_coords} --> {chess_module.number_to_string_coord(*board_coords)}')

    def clean_instance(self):
        super().clean_instance()
        self.display_style = None
        self.game = None
        self.pieces = None


ChessBoard()
Sprite.register_class(ChessBoard)

TL = ChessBoard.TILE_SIZE
def remove_outline(surf : pygame.Surface, colorkey = None) -> pygame.Surface:
    return surf
    mask : pygame.Mask = pygame.mask.from_surface(surf)
    for point in mask.outline():
        mask.set_at(point, 0)
    new_surf : pygame.Surface = pygame.surface.Surface(surf.get_size())
    new_surf = mask.to_surface(new_surf, setsurface=surf, unsetcolor=colorkey, setcolor=None, unsetsurface=None, dest=(0,0))
    new_surf.set_colorkey(colorkey)
    return new_surf

class ChessPiece(Sprite):
    PIECE_RELEASED : int = pygame.event.custom_type()

    inactive_elements : list['ChessPiece'] = []
    active_elements : list['ChessPiece'] = []

    PIECE_IMAGES : dict[chess_module.PieceType, pygame.Surface] = {piece_type : 
    remove_outline(convert_alpha_to_colorkey(pygame.image.load_sized_svg(f'assets/graphics/chess_sets/regular/{piece_type.name.lower()}.svg', 
                                                          (ChessBoard.IMAGE_SIZE, ChessBoard.IMAGE_SIZE)), (0, 255, 255)),colorkey=(0,255,255))
    for piece_type in chess_module.PieceType if piece_type != chess_module.PieceType.EMPTY}

    def __init__(self):
        super().__init__()
        ChessPiece.inactive_elements.append(self)
        self.type : chess_module.PieceType
        self.owner : ChessBoard
        self.visual_coords : list[int, int]
        self.anchored : bool
        self.drag_id : int|None
        self.drag_offset : pygame.Vector2|None
        self.drag_timer : Timer|None
        self.no_hold_drag : bool|None
        self.captured : bool
        self.capture_pos : tuple[int, int]|None

    @property
    def board_coords(self):
        return self.owner.visual_to_board_coords(*self.visual_coords, self.owner.display_style)
    
    @board_coords.setter
    def board_coords(self, new_val : tuple[int, int]):
        self.visual_coords = self.owner.board_to_visual_coords(*new_val, self.owner.display_style)
    
    @classmethod
    def spawn(cls, board : ChessBoard, piece_type : chess_module.PieceType, visual_coords : tuple[int, int]):
        element = cls.inactive_elements[0]
        element.owner = board
        element.type = piece_type
        element.visual_coords = list(visual_coords)
        element.image = cls.PIECE_IMAGES[piece_type]
        element.rect = element.image.get_rect()
        

        element.position = pygame.Vector2(element.owner.visual_to_real_coords_center(*element.visual_coords))
        element.align_rect()
        element.zindex = 0

        element.anchored = True
        element.drag_id = None
        element.drag_offset = None
        element.captured = False
        element.capture_pos = None

        cls.unpool(element)
        return element
    
    def switch_type(self, new_type : chess_module.PieceType):
        if new_type == chess_module.PieceType.EMPTY: return
        self.type = new_type
        self.image = ChessPiece.PIECE_IMAGES[new_type]

    
    def grab(self, grab_id : int, grab_pos : tuple[int, int]):
        if self.drag_id: return
        if self.captured: return
        self.drag_id = grab_id
        self.drag_offset = (self.position - grab_pos)
        if self.drag_offset.magnitude() > 2:
            self.drag_offset.scale_to_length(2)
        self.anchored = False
        self.drag_timer = Timer(-1, time_source=core_object.game.game_timer.get_time)
        self.no_hold_drag = False
    
    def update_grab(self):
        current_grab_pos : pygame.Vector2|None = None
        if self.drag_id == -1:
            if any(pygame.mouse.get_pressed()) != self.no_hold_drag:
                current_grab_pos = pygame.Vector2(pygame.mouse.get_pos())
            elif self.drag_timer.get_time() < 0.1:
                current_grab_pos = pygame.Vector2(pygame.mouse.get_pos())
                self.no_hold_drag = True
            else:
                current_grab_pos = None
        else:
            pass #this is for mobile
        if current_grab_pos is None:

            self.end_grab()
            return
        self.position = current_grab_pos + self.drag_offset
    
    def end_grab(self):
        if self.captured: return
        if self.drag_id:
            pygame.event.post(pygame.Event(ChessPiece.PIECE_RELEASED, {"piece" : self, 'drag_id' : self.drag_id}))
        self.drag_id = None
        self.drag_offset = None
        self.drag_timer = None
        self.no_hold_drag = None
        
    
    def settle_on_board(self, new_visual_coords : tuple[int, int]|None = None):
        if self.captured: return
        self.end_grab()
        self.visual_coords = list(new_visual_coords) if new_visual_coords else self.visual_coords
        self.position = self.owner.visual_to_real_coords_center(*self.visual_coords)
        self.anchored = True
    
    def update(self, delta : float):
        if self.captured: 
            self.update_capture(delta)
            return
        if self.drag_id:
            self.update_grab()
    
    def update_capture(self, delta : float):
        pass

    def capture(self):
        self.captured = True
        self.capture_pos = [0,0]
        self.position = self.owner.capture_to_real_pos(*self.capture_pos)
        self.kill_instance_safe()

    def clean_instance(self):
        super().clean_instance()
        self.type = None
        self.owner = None
        self.visual_coords = None
        self.anchored = None
        self.drag_timer = None
        self.no_hold_drag = None
        self.captured = None
        self.capture_pos = None



for _ in range(64):
    ChessPiece()

Sprite.register_class(ChessPiece)

def do_connections():
    evm = core_object.event_manager
    evm.bind(pygame.MOUSEBUTTONDOWN, ChessBoard.receive_events)
    evm.bind(pygame.MOUSEBUTTONUP, ChessBoard.receive_events)

def remove_connections():
    evm = core_object.event_manager
    evm.unbind(pygame.MOUSEBUTTONDOWN, ChessBoard.receive_events)
    evm.unbind(pygame.MOUSEBUTTONUP, ChessBoard.receive_events)
    
    
del TL