import pygame
from typing import Any
from math import floor
from random import shuffle, choice
import random
import game.chess_module
import game.sprite
import utils.tween_module as TweenModule
from utils.ui.ui_sprite import UiSprite
from utils.ui.textbox import TextBox
from utils.ui.textsprite import TextSprite
from utils.ui.base_ui_elements import BaseUiElements
import utils.interpolation as interpolation
from utils.my_timer import Timer
from game.sprite import Sprite
from utils.helpers import average, random_float
from utils.ui.brightness_overlay import BrightnessOverlay

class GameState:
    def __init__(self, game_object : 'Game'):
        self.game = game_object

    def main_logic(self, delta : float):
        pass

    def pause(self):
        pass

    def unpause(self):
        pass

    def handle_key_event(self, event : pygame.Event):
        pass

    def handle_mouse_event(self, event : pygame.Event):
        pass

    def cleanup(self):
        pass

class NormalGameState(GameState):
    def main_logic(self, delta : float):
        Sprite.update_all_sprites(delta)
        Sprite.update_all_registered_classes(delta)

    def pause(self):
        if not self.game.active: return
        self.game.game_timer.pause()
        window_size = core_object.main_display.get_size()
        pause_ui1 = BrightnessOverlay(-60, pygame.Rect(0,0, *window_size), 0, 'pause_overlay', zindex=999)
        pause_ui2 = TextSprite(pygame.Vector2(window_size[0] // 2, window_size[1] // 2), 'center', 0, 'Paused', 'pause_text', None, None, 1000,
                               (self.game.font_70, 'White', False), ('Black', 2), colorkey=(0, 255, 0))
        core_object.main_ui.add(pause_ui1)
        core_object.main_ui.add(pause_ui2)
        self.game.state = PausedGameState(self.game)
    
    def handle_key_event(self, event : pygame.Event):
        if event.type == pygame.K_p:
            self.pause()

class TestGameState(NormalGameState):
    def __init__(self, game_object : 'Game'):
        self.game = game_object
        self.player : TestPlayer = TestPlayer.spawn(pygame.Vector2(random.randint(0, 960),random.randint(0, 540)))
        self.board : ChessBoard = ChessBoard.spawn()
        game.chess_sprites.do_connections()

    def main_logic(self, delta : float):
        super().main_logic(delta)
    
    def cleanup(self):
        game.chess_sprites.remove_connections()

class ChessBaseGameState(NormalGameState):
    def __init__(self, game_object : 'Game'):
        self.game = game_object
        self.board : ChessBoard = ChessBoard.spawn()
        self.held_piece : ChessPiece|None = None
        self.do_connections()
    
    def main_logic(self, delta : float):
        super().main_logic(delta)
    
    def handle_mouse_event(self, event : pygame.Event):
        if event.type == game.sprite.Sprite.SPRITE_CLICKED:
            main_hit : Sprite = event.main_hit
            press_pos : tuple[int, int] = event.pos
            finger_id : int = event.finger_id
            if isinstance(main_hit, ChessPiece) and not self.held_piece:
                if not self.is_piece_grabbable(main_hit): return
                main_hit.grab(finger_id, press_pos)
                self.held_piece = main_hit
                self.held_piece.zindex = 5
    
    def is_piece_grabbable(self, piece : 'ChessPiece') -> bool:
        if game.chess_module.ChessGame.get_piece_color(piece.type) != self.board.game.current_turn:
            return False
        return True
    
    def handle_piece_release(self, event : pygame.Event):
        piece : ChessPiece = event.piece
        drag_id : int = event.drag_id
        old_board_coords : tuple[int, int] = self.board.visual_to_board_coords(*piece.visual_coords, self.board.display_style)
        new_visual_coords : tuple[int, int] = self.board.real_to_visual_coords(piece.position.x, piece.position.y)
        new_board_coords : tuple[int, int] = self.board.visual_to_board_coords(*new_visual_coords, self.board.display_style)
        if not (0 <= new_visual_coords[0] <= 7) or not (0 <= new_visual_coords[1] <= 7):
            piece.settle_on_board()
            piece.zindex = 0
            self.held_piece = None
            return
        if piece.visual_coords[0] == new_visual_coords[0] and piece.visual_coords[1] == new_visual_coords[1]:
            piece.settle_on_board()
            piece.zindex = 0
            self.held_piece = None
            return
        if not self.board.game.validate_move(old_board_coords, new_board_coords, {}):
            self.game.alert_player('Illegal Move!', 1.8)
            piece.settle_on_board()
            piece.zindex = 0
            self.held_piece = None
            return
        extra_instructions = self.board.game.make_move(old_board_coords, new_board_coords, {})
        if extra_instructions is False:
            self.game.alert_player('Move is invalid!', 1.8)
            piece.settle_on_board()
            piece.zindex = 0
            self.held_piece = None
            return
        piece.settle_on_board(new_visual_coords)
        self.held_piece = None
        piece.zindex = 0
        for instruction in extra_instructions:
            instruction_type : str = instruction['type']
            if instruction_type == 'capture_at':
                ignore_count : int = 0
                while True:
                    to_capture : ChessPiece|None = self.board.get_at(self.board.board_to_visual_coords(*instruction['pos'], self.board.display_style), ignore_count)
                    if not to_capture: break
                    if to_capture == piece: 
                        ignore_count += 1
                        continue
                    to_capture.capture()
                    break
            elif instruction_type == 'move_piece_to':
                to_move : ChessPiece|None = self.board.get_at(self.board.board_to_visual_coords(*instruction['start_pos'], self.board.display_style))
                if to_move: to_move.settle_on_board(self.board.board_to_visual_coords(*instruction['end_pos'], self.board.display_style))
            elif instruction_type == 'change_type':
                target_pos : tuple[int, int] = self.board.board_to_visual_coords(*instruction['pos'], self.board.display_style)
                target : ChessPiece|None = self.board.get_at(target_pos)
                if target: target.switch_type(instruction['new_type'])
            elif instruction_type == 'check':
                self.game.alert_player('Check!')
            elif instruction_type == 'checkmate':
                self.switch_to_gameover('Checkmate!')
            elif instruction_type == 'stalemate':
                self.switch_to_gameover("Stalemate!")
    
    def switch_to_gameover(self, message : str):
        core_object.event_manager.unbind(ChessPiece.PIECE_RELEASED, self.handle_piece_release)
        self.game.state = LocalGameOverGameState(self.game, self.board, message)

    
    def do_connections(self):
        game.chess_sprites.do_connections()
        core_object.event_manager.bind(ChessPiece.PIECE_RELEASED, self.handle_piece_release)
    
    def remove_connections(self):
        game.chess_sprites.remove_connections()
        core_object.event_manager.unbind(ChessPiece.PIECE_RELEASED, self.handle_piece_release)

    def cleanup(self):
        self.remove_connections()

class PVPGameState(ChessBaseGameState):
    def __init__(self, game_object : 'Game'):
        super().__init__(game_object)

    def main_logic(self, delta : float):
        super().main_logic(delta)
        pass

    def cleanup(self):
        super().cleanup()


class PvsCPUGameState(ChessBaseGameState):
    def __init__(self, game_object : 'Game'):
        super().__init__(game_object)

    def main_logic(self, delta : float):
        super().main_logic(delta)
        pass

    def cleanup(self):
        super().cleanup()

class LocalGameOverGameState(NormalGameState):
    def __init__(self, game_object : 'Game', board : 'ChessBoard', message : str):
        self.game = game_object
        self.board = board
        self.game.alert_player(message)
        self.close_timer : Timer = Timer(3, time_source=game_object.game_timer.get_time)
        game.chess_sprites.remove_connections()
    
    def main_logic(self, delta : float):
        if self.close_timer.isover():
            self.game.fire_gameover_event()

    def cleanup(self):
        game.chess_sprites.remove_connections()


class PausedGameState(GameState):
    def __init__(self, game_object : 'Game', previous : GameState):
        super().__init__(game_object)
        self.previous_state = previous
    
    def unpause(self):
        if not self.game.active: return
        self.game.game_timer.unpause()
        pause_ui1 = core_object.main_ui.get_sprite('pause_overlay')
        pause_ui2 = core_object.main_ui.get_sprite('pause_text')
        if pause_ui1: core_object.main_ui.remove(pause_ui1)
        if pause_ui2: core_object.main_ui.remove(pause_ui2)
        self.game.state = self.previous_state

    def handle_key_event(self, event : pygame.Event):
        if event.type == pygame.K_p:
            self.unpause()

def runtime_imports():
    global Game
    from game.game_module import Game
    global core_object
    from core.core import core_object

    #runtime imports for game classes
    global game, TestPlayer      
    import game.test_player
    from game.test_player import TestPlayer

    global ChessBoard, ChessPiece
    import game.chess_sprites
    from game.chess_sprites import ChessBoard, ChessPiece


class GameStates:
    NormalGameState = NormalGameState
    TestGameState = TestGameState
    PausedGameState = PausedGameState
    ChessBaseGameState = ChessBaseGameState
    PVPGameState = PVPGameState
    PvsCPUGameState = PvsCPUGameState
    LocalGameOverGameState = LocalGameOverGameState