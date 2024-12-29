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
                main_hit.grab(finger_id, press_pos)
                self.held_piece = main_hit

    
    def handle_piece_release(self, event : pygame.Event):
        piece : ChessPiece = event.piece
        drag_id : int = event.drag_id
        new_visual_coords : tuple[int, int] = self.board.real_to_visual_coords(piece.position.x, piece.position.y)
        already_there : ChessPiece|None = self.board.get_at(new_visual_coords)
        if already_there and already_there != piece:
            already_there.capture()
        piece.settle_on_board(new_visual_coords)
        self.held_piece = None
    
    def do_connections(self):
        game.chess_sprites.do_connections()
        core_object.event_manager.bind(ChessPiece.PIECE_RELEASED, self.handle_piece_release)
    
    def remove_connections(self):
        game.chess_sprites.remove_connections()

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