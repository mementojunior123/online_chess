import pygame
from typing import Any
from math import floor
from random import shuffle, choice
import random
import os
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
from game.game_states import GameState, GameStates

class Game:
    font_40 = pygame.Font('assets/fonts/Pixeltype.ttf', 40)
    font_50 = pygame.Font('assets/fonts/Pixeltype.ttf', 50)
    font_60 = pygame.Font('assets/fonts/Pixeltype.ttf', 60)
    font_70 = pygame.Font('assets/fonts/Pixeltype.ttf', 70)
    
    def __init__(self) -> None:
        self.STATES = GameStates

        self.active : bool = False
        self.state : None|GameState = None
        self.game_timer : Timer|None = None
        self.game_data : dict|None = {}

        

    def start_game(self, event : pygame.Event):
        self.active = True
        self.game_timer = Timer(-1)
        self.game_data = {}
        self.make_connections()
        self.state = self.STATES.TestGameState(self)

        
    def alert_player(self, text : str, alert_speed : float = 1):
        text_sprite = TextSprite(pygame.Vector2(core_object.main_display.get_width() // 2, 90), 'midtop', 0, text, 
                        text_settings=(core_object.menu.font_60, 'White', False), text_stroke_settings=('Black', 2), colorkey=(0,255,0))
        
        text_sprite.rect.bottom = -5
        text_sprite.position = pygame.Vector2(text_sprite.rect.center)
        temp_y = text_sprite.rect.centery
        core_object.main_ui.add_temp(text_sprite, 5)
        TInfo = TweenModule.TweenInfo
        goal1 = {'rect.centery' : 50, 'position.y' : 50}
        info1 = TInfo(interpolation.quad_ease_out, 0.3 / alert_speed)
        goal2 = {'rect.centery' : temp_y, 'position.y' : temp_y}
        info2 = TInfo(interpolation.quad_ease_in, 0.4 / alert_speed)
        
        on_screen_time = 1 / alert_speed
        info_wait = TInfo(lambda t : t, on_screen_time)
        goal_wait = {}

        chain = TweenModule.TweenChain(text_sprite, [(info1, goal1), (info_wait, goal_wait), (info2, goal2)], True, time_source=self.game_timer.get_time)
        chain.register()
        chain.play()
        
        #Setup varaibles

    def make_connections(self):
        core_object.event_manager.bind(pygame.KEYDOWN, self.handle_key_event)
        core_object.event_manager.bind(pygame.KEYUP, self.handle_key_event)

        core_object.event_manager.bind(pygame.MOUSEBUTTONDOWN, self.handle_mouse_event)
        core_object.event_manager.bind(pygame.MOUSEBUTTONUP, self.handle_mouse_event)
        core_object.event_manager.bind(pygame.MOUSEMOTION, self.handle_mouse_event)
        core_object.event_manager.bind(Sprite.SPRITE_CLICKED, self.handle_mouse_event)

    def remove_connections(self):
        core_object.event_manager.unbind(pygame.KEYDOWN, self.handle_key_event)
        core_object.event_manager.unbind(pygame.KEYUP, self.handle_key_event)

        core_object.event_manager.unbind(pygame.MOUSEBUTTONDOWN, self.handle_mouse_event)
        core_object.event_manager.unbind(pygame.MOUSEBUTTONUP, self.handle_mouse_event)
        core_object.event_manager.unbind(pygame.MOUSEMOTION, self.handle_mouse_event)
        core_object.event_manager.unbind(Sprite.SPRITE_CLICKED, self.handle_mouse_event)

    def handle_key_event(self, event : pygame.Event):
        self.state.handle_key_event(event)
    
    def handle_mouse_event(self, event : pygame.Event):
        self.state.handle_mouse_event(event)

    def update(self, delta : float):
        self.state.main_logic(delta)
    
    def pause(self):
        if not self.active: return
        self.state.pause()
    
    def unpause(self):
        if not self.active: return
        self.state.unpause()
    
    def is_paused(self) -> bool:
        return isinstance(self.state, self.STATES.PausedGameState)
    
    
    def fire_gameover_event(self):
        new_event = pygame.event.Event(core_object.END_GAME, {})
        pygame.event.post(new_event)
    
    def end_game(self):
        self.remove_connections()
        self.cleanup()

    def cleanup(self):
        #Cleanup basic variables
        self.active = False
        self.state = None
        self.game_timer = None
        self.game_data.clear()

        #Cleanup ingame object
        Sprite.kill_all_sprites()
        core_object.main_ui.clear_all()

        #Clear game varaibles
         

   
    def init(self):
        global core_object
        from core.core import core_object

        #runtime imports for game classes
        global game, TestPlayer      
        import game.test_player
        from game.test_player import TestPlayer