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

import asyncio

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
    
    def sync_move(self, start_pos : tuple[int, int], end_pos : tuple[int, int], bonus_info : game.chess_module.ChessMoveExtraInfo):
        extra_instructions = self.board.game.make_move(start_pos, end_pos, bonus_info)
        if extra_instructions is False: return
        piece : ChessPiece|None = self.board.get_at_board_coords(start_pos)
        piece.settle_on_board(self.board.board_to_visual_coords(*end_pos, self.board.display_style))
        for instruction in extra_instructions:
            self.handle_sync_instruction(instruction, piece)
    
    def handle_sync_instruction(self, instruction : dict[str, Any], moved_piece : 'ChessPiece'):
        instruction_type : str = instruction['type']
        if instruction_type == 'capture_at':
            ignore_count : int = 0
            while True:
                to_capture : ChessPiece|None = self.board.get_at(self.board.board_to_visual_coords(*instruction['pos'], self.board.display_style), ignore_count)
                if not to_capture: break
                if to_capture == moved_piece: 
                    ignore_count += 1
                    continue
                to_capture.capture()
                break
        elif instruction_type == 'move_piece_to':
            to_move : ChessPiece|None = self.board.get_at_board_coords(instruction['start_pos'])
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
        elif instruction_type == 'insufficent_material':
            self.switch_to_gameover("Draw!")
    
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
            self.handle_sync_instruction(instruction, piece)
        self.after_move_made(old_board_coords, new_board_coords, {})
    
    def after_move_made(self, start_pos : tuple[int, int], end_pos : tuple[int, int], bonus_info : game.chess_module.ChessMoveExtraInfo):
        pass
    
    def switch_to_gameover(self, message : str):
        core_object.event_manager.unbind(ChessPiece.PIECE_RELEASED, self.handle_piece_release)
        self.game.state = LocalGameOverGameState(self.game, self.board, message)
        self.remove_connections()

    
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

class WaitingForOnlineGameState(NormalGameState):
    def __init__(self, game_object : 'Game'):
        super().__init__(game_object)
        #if core_object.is_web():
            #self.game.alert_player('Online PVP is not avaiable yet!')
            #self.game.state = ChessBaseGameState(self.game)
        self.network_client : NetworkClient

        self.server_ready_delay : Timer = Timer(-1)
        self.local_team : game.chess_module.TeamType|None = None
    
    async def make_network(self):
        self.network_client = NetworkClient(None, 'localhost')
        await self.network_client.connect_to_server()
        #print('WE made it', self.network_client.connected)
        if not self.network_client.connected:
            self.game.fire_gameover_event()
            core_object.menu.alert_player('Could not connect to server!')
            return
        self.make_network_connections()    
        self.network_client.receive_messages()
        #await asyncio.sleep(0)

    def handle_network_event(self, event : pygame.Event):
        match event.type:
            case NetworkClient.NETWORK_MESSAGE_RECIVED:
                data : bytes = event.data
                print(f'Recieved data : {data}')
                core_object.set_debug_message(f'Recieved data : {data}')
                if data.startswith(b'GameStarting'):
                    self.local_team = game.chess_module.TeamType.WHITE if data.removeprefix(b'GameStarting') == b'W' else game.chess_module.TeamType.BLACK
                    self.server_ready_delay.set_duration(1.5)
                    self.game.alert_player('Match Found!')
                elif data.startswith(b'ConnectionEstablished'):
                    self.game.alert_player('Connected to server!')
            case NetworkClient.NETWORK_MESSAGE_FAILED:
                data : bytes = event.data
                progress : int = event.progress
                print(f'Message sending failed at {progress}/{len(data)}')
                return
            case NetworkClient.NETWORK_MESSAGE_SENT:
                data : bytes = event.data
                print(f'Sent data: {data}')
                core_object.set_debug_message(f'Sent data:  {data}')
                return
            case NetworkClient.NETWORK_SERVER_DISCONNECTED:
                self.game.fire_gameover_event()
                core_object.menu.alert_player('Server was disconnected!')
    
    def start_online_game(self, local_team : game.chess_module.TeamType):
        self.game.state = OnlinePvPGameState(self.game, self.network_client, local_team)
        self.remove_network_connections()
    
    def make_network_connections(self):
        core_object.event_manager.bind(NetworkClient.NETWORK_MESSAGE_RECIVED, self.handle_network_event)
        core_object.event_manager.bind(NetworkClient.NETWORK_MESSAGE_FAILED, self.handle_network_event)
        core_object.event_manager.bind(NetworkClient.NETWORK_MESSAGE_SENT, self.handle_network_event)
        core_object.event_manager.bind(NetworkClient.NETWORK_SERVER_DISCONNECTED, self.handle_network_event)
    
    def remove_network_connections(self):
        core_object.event_manager.unbind(NetworkClient.NETWORK_MESSAGE_RECIVED, self.handle_network_event)
        core_object.event_manager.unbind(NetworkClient.NETWORK_MESSAGE_FAILED, self.handle_network_event)
        core_object.event_manager.unbind(NetworkClient.NETWORK_MESSAGE_SENT, self.handle_network_event)
        core_object.event_manager.unbind(NetworkClient.NETWORK_SERVER_DISCONNECTED, self.handle_network_event)
    

    def main_logic(self, delta : float):
        super().main_logic(delta)
        self.network_client.update()
        if self.server_ready_delay.isover():
            self.start_online_game(self.local_team)
    
    def cleanup(self):
        super().cleanup()
        self.network_client.send_message(b'Disconnecting')
        core_object.task_scheduler.schedule_continuous_task(0.5, self.network_client.update)
        core_object.task_scheduler.schedule_task(1, self.network_client.close)
        core_object.task_scheduler.schedule_task(2, self.network_client.cleanup)
        core_object.task_scheduler.schedule_task(3, self.remove_network_connections)
    
    def cleanup_network(self):
        self.network_client.cleanup()
    
    def pause(self):
        return
        super().pause()

class OnlinePvPGameState(ChessBaseGameState):
    def __init__(self, game_object : 'Game', network_client : 'NetworkClient', local_team : 'game.chess_module.TeamType'):

        self.game = game_object
        self.board : ChessBoard = ChessBoard.spawn(display_style=BoardDisplayStyle.STANDARD 
                                                   if local_team == game.chess_module.TeamType.WHITE 
                                                   else BoardDisplayStyle.BLACK_STANDARD)
        self.held_piece : ChessPiece|None = None
        game.chess_sprites.do_connections()
        core_object.event_manager.bind(ChessPiece.PIECE_RELEASED, self.handle_piece_release)

        self.network_client = network_client
        self.local_team : game.chess_module.TeamType = local_team
        if not self.network_client.connected:
            self.network_client.connect_to_server()
        if self.network_client.listening <= 0:
            self.network_client.receive_messages()
        self.make_network_connections()

        self.can_make_move : bool = True
        self.dc_timer : Timer|None = None
        self.current_outcome : str|None = None

    def switch_to_gameover(self, message : str, flag = False):
        if not flag: 
            self.current_outcome = message
            self.can_make_move = False
            self.dc_timer = Timer(3)
            return
        return super().switch_to_gameover(message)
    
    def main_logic(self, delta : float):
        super().main_logic(delta)
        self.network_client.update()
        if self.dc_timer:
            if self.dc_timer.isover():
                self.switch_to_gameover(self.current_outcome, flag=True)

    def handle_network_event(self, event : pygame.Event):
        match event.type:
            case NetworkClient.NETWORK_MESSAGE_RECIVED:
                data : bytes = event.data
                print(f'Recieved data : {data}')
                self.handle_network_message(data)
            case NetworkClient.NETWORK_MESSAGE_FAILED:
                data : bytes = event.data
                progress : int = event.progress
                print(f'Message sending failed at {progress}/{len(data)}')
                return
            case NetworkClient.NETWORK_MESSAGE_SENT:
                data : bytes = event.data
                print(f'Sent data: {data}')
                return
            case NetworkClient.NETWORK_SERVER_DISCONNECTED:
                self.game.fire_gameover_event()
                core_object.menu.alert_player('Server was disconnected!')
    
    def handle_network_message(self, message : bytes):
        if message.startswith(b'GameOver'):
            outcome : bytes = message.removeprefix(b'GameOver')
            self.switch_to_gameover(outcome.decode(), flag=True)
    
        if message.startswith(b'OpponentMove'):
            move_chosen : game.chess_module.ChessMove = game.chess_module.decode_move(message.removeprefix(b'OpponentMove'))
            self.sync_move(move_chosen['start_pos'], move_chosen['end_pos'], move_chosen['extra_info'])
        
        if message.startswith(b'MadeInvalidMove'):
            self.switch_to_gameover('Something went wrong in move validation!', flag=True)
    
    
    def after_move_made(self, start_pos : tuple[int, int], end_pos : tuple[int, int], bonus_info : game.chess_module.ChessMoveExtraInfo):
        move_data : bytes = game.chess_module.encode_move(game.chess_module.ChessMove.new(start_pos, end_pos, bonus_info))
        netowrk_message : bytes = b'TryMove' + move_data
        self.network_client.send_message(netowrk_message)
    
    def make_network_connections(self):
        core_object.event_manager.bind(NetworkClient.NETWORK_MESSAGE_RECIVED, self.handle_network_event)
        core_object.event_manager.bind(NetworkClient.NETWORK_MESSAGE_FAILED, self.handle_network_event)
        core_object.event_manager.bind(NetworkClient.NETWORK_MESSAGE_SENT, self.handle_network_event)
        core_object.event_manager.bind(NetworkClient.NETWORK_SERVER_DISCONNECTED, self.handle_network_event)
    
    def remove_network_connections(self):
        core_object.event_manager.unbind(NetworkClient.NETWORK_MESSAGE_RECIVED, self.handle_network_event)
        core_object.event_manager.unbind(NetworkClient.NETWORK_MESSAGE_FAILED, self.handle_network_event)
        core_object.event_manager.unbind(NetworkClient.NETWORK_MESSAGE_SENT, self.handle_network_event)
        core_object.event_manager.unbind(NetworkClient.NETWORK_SERVER_DISCONNECTED, self.handle_network_event)
    


    def is_piece_grabbable(self, piece : 'ChessPiece') -> bool:
        piece_team : game.chess_module.TeamType = game.chess_module.ChessGame.get_piece_color(piece.type)
        if piece_team != self.board.game.current_turn:
            return False
        if piece_team != self.local_team:
            return False
        return self.can_make_move

    def cleanup(self):
        super().cleanup()
        self.network_client.send_message(b'Disconnecting')
        core_object.task_scheduler.schedule_task(1, self.network_client.close)
        core_object.task_scheduler.schedule_task(2, self.network_client.cleanup)
        self.remove_network_connections()

class LocalGameOverGameState(NormalGameState):
    def __init__(self, game_object : 'Game', board : 'ChessBoard', message : str):
        self.game = game_object
        self.board = board
        self.game.alert_player(message)
        self.close_timer : Timer = Timer(3, time_source=game_object.game_timer.get_time)
    
    def main_logic(self, delta : float):
        if self.close_timer.isover():
            self.game.fire_gameover_event()

    def cleanup(self):
        pass


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

    global ChessBoard, ChessPiece, BoardDisplayStyle
    import game.chess_sprites
    from game.chess_sprites import ChessBoard, ChessPiece, BoardDisplayStyle

    global online, NetworkClient, WebNetworkClient
    if (not core_object.is_web()) and False:
        import online.network_client
        online.network_client.init()
        from online.network_client import NetworkClient
    else:
        import online.web_network_client
        from online.web_network_client import WebNetworkClient as NetworkClient
        #WebNetworkClient = NetworkClient


class GameStates:
    NormalGameState = NormalGameState
    TestGameState = TestGameState
    PausedGameState = PausedGameState
    ChessBaseGameState = ChessBaseGameState
    PVPGameState = PVPGameState
    PvsCPUGameState = PvsCPUGameState
    LocalGameOverGameState = LocalGameOverGameState
    WaitingForOnlineGameState = WaitingForOnlineGameState
    OnlinePvPGameState = OnlinePvPGameState