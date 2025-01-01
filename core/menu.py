import pygame
import random
from utils.ui.ui_sprite import UiSprite
from utils.ui.textsprite import TextSprite
from utils.ui.base_ui_elements import BaseUiElements
import utils.tween_module as TweenModule
import utils.interpolation as interpolation
from utils.my_timer import Timer
from utils.ui.brightness_overlay import BrightnessOverlay
from math import floor
from utils.helpers import ColorType
from typing import Callable

class BaseMenu:
    font_40 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 40)
    font_50 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 50)
    font_60 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 60)
    font_70 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 70)
    font_150 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 150)

    def __init__(self) -> None:
        self.stage : int
        self.stages : list[list[UiSprite]]
        self.bg_color : ColorType|str
        self.temp : dict[UiSprite, Timer] = {}
        
    def init(self):
        self.bg_color = (94, 129, 162)
        self.stage = 1
        self.stage_data : list[dict] = [None, {}]
        self.stages = [None, []]
    
    def add_temp(self, element : UiSprite, time : float|Timer, override = False, time_source : Callable[[], float]|None = None, time_scale : float = 1):
        if element not in self.temp or override == True:
            timer = time if type(time) == Timer else Timer(time, time_source, time_scale)
            self.temp[element] = timer
    def alert_player(self, text : str, alert_speed : float = 1):
        text_sprite = TextSprite(pygame.Vector2(core_object.main_display.get_width() // 2, 90), 'midtop', 0, text, 
                        text_settings=(core_object.menu.font_60, 'White', False), text_stroke_settings=('Black', 2), colorkey=(0,255,0))
        
        text_sprite.rect.bottom = -5
        text_sprite.position = pygame.Vector2(text_sprite.rect.center)
        temp_y = text_sprite.rect.centery
        self.add_temp(text_sprite, 5)
        TInfo = TweenModule.TweenInfo
        goal1 = {'rect.centery' : 50, 'position.y' : 50}
        info1 = TInfo(interpolation.quad_ease_out, 0.3 / alert_speed)
        goal2 = {'rect.centery' : temp_y, 'position.y' : temp_y}
        info2 = TInfo(interpolation.quad_ease_in, 0.4 / alert_speed)
        
        on_screen_time = 1 / alert_speed
        info_wait = TInfo(lambda t : t, on_screen_time)
        goal_wait = {}

        chain = TweenModule.TweenChain(text_sprite, [(info1, goal1), (info_wait, goal_wait), (info2, goal2)], True)
        chain.register()
        chain.play()

    def add_connections(self):
        core_object.event_manager.bind(pygame.MOUSEBUTTONDOWN, self.handle_mouse_event)
        core_object.event_manager.bind(UiSprite.TAG_EVENT, self.handle_tag_event)
    
    def remove_connections(self):
        core_object.event_manager.unbind(pygame.MOUSEBUTTONDOWN, self.handle_mouse_event)
        core_object.event_manager.unbind(UiSprite.TAG_EVENT, self.handle_tag_event)
    
    def __get_core_object(self):
        global core_object
        from core.core import core_object

    def render(self, display : pygame.Surface):
        sprite_list = [sprite for sprite in (self.stages[self.stage] + list(self.temp.keys())) if sprite.visible == True]
        sprite_list.sort(key = lambda sprite : sprite.zindex)
        for sprite in sprite_list:
            sprite.draw(display)
        
    
    def update(self, delta : float):
        to_del = []
        for item in self.temp:
            if self.temp[item].isover(): to_del.append(item)
        for item in to_del:
            self.temp.pop(item)

        stage_data = self.stage_data[self.stage]
        match self.stage:
            case 1:
                pass
    
    def prepare_entry(self, stage : int = 1):
        self.add_connections()
        self.stage = stage
    
    def prepare_exit(self):
        self.stage = 0
        self.remove_connections()
        self.temp.clear()
    
    def goto_stage(self, new_stage : int):
        self.stage = new_stage

    def launch_game(self):
        new_event = pygame.event.Event(core_object.START_GAME, {})
        pygame.event.post(new_event)

    def get_sprite(self, stage, tag):
        """Returns the 1st sprite with a corresponding tag.
        None is returned if it was not found in the stage."""
        if tag is None or stage is None: return None

        the_list = self.stages[stage]
        for sprite in the_list:
            if sprite.tag == tag:
                return sprite
        return None
    
    def get_sprite_by_name(self, stage, name):
        """Returns the 1st sprite with a corresponding name.
        None is returned if it was not found in the stage."""
        if name is None or stage is None: return None

        the_list = self.stages[stage]
        sprite : UiSprite
        for sprite in the_list:
            if sprite.name == name:
                return sprite
        return None

    def get_sprite_index(self, stage, name = None, tag = None):
        '''Returns the index of the 1st occurence of sprite with a corresponding name or tag.
        None is returned if the sprite is not found'''
        if name is None and tag is None: return None
        the_list = self.stages[stage]
        sprite : UiSprite
        for i, sprite in enumerate(the_list):
            if sprite.name == name and name is not None:
                return i
            if sprite.tag == tag and tag is not None:
                return i
        return None
    
    def find_and_replace(self, new_sprite : UiSprite, stage : int, name : str|None = None, tag : int|None = None, sprite : UiSprite|None = None) -> bool:
        found : bool = False
        for index, sprite in enumerate(self.stages[stage]):
            if sprite == new_sprite and sprite is not None:
                found = True
                break
            if sprite.tag == tag and tag is not None:
                found = True
                break
            if sprite.name == name and name is not None:
                found = True
                break
        
        if found:
            self.stages[stage][index] = new_sprite
        else:
            print('Find and replace failed')
        return found
    
    def handle_tag_event(self, event : pygame.Event):
        if event.type != UiSprite.TAG_EVENT:
            return
        tag : int = event.tag
        name : str = event.name
        trigger_type : str = event.trigger_type
        stage_data = self.stage_data[self.stage]
        match self.stage:
            case 1:
                pass
                   
    
    def handle_mouse_event(self, event : pygame.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos : tuple = event.pos
            sprite : UiSprite
            for sprite in self.stages[self.stage]:
                if type(sprite) != UiSprite: continue
                if sprite.rect.collidepoint(mouse_pos):
                    sprite.on_click()

class Menu(BaseMenu):
    font_40 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 40)
    font_50 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 50)
    font_60 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 60)
    font_70 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 70)
    font_150 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 150)
    
    def init(self):
        window_size = core_object.main_display.get_size()
        centerx = window_size[0] // 2

        self.stage = 1
        
        self.stage_data : list[dict] = [None, {}]
        self.stages = [None, 
        [BaseUiElements.new_text_sprite('Online Chess', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 50)),
        BaseUiElements.new_button('BlueButton', 'Local', 1, 'midbottom', (centerx - 260, window_size[1] - 15), (0.5, 1.4), 
        {'name' : 'play_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Online', 1, 'midbottom', (centerx + 260, window_size[1] - 15), (0.5, 1.4), 
        {'name' : 'online_button'}, (Menu.font_40, 'Black', False))], #stage 1
        ]
        self.bg_color = (94, 129, 162)
        self.add_connections()
    
    def update(self, delta : float):
        stage_data = self.stage_data[self.stage]
        match self.stage:
            case 1:
                pass
    
    def handle_tag_event(self, event : pygame.Event):
        if event.type != UiSprite.TAG_EVENT:
            return
        tag : int = event.tag
        name : str = event.name
        trigger_type : str = event.trigger_type
        stage_data = self.stage_data[self.stage]
        match self.stage:
            case 1:
                if name == "play_button":
                    pygame.event.post(pygame.Event(core_object.START_GAME, {}))
                elif name == 'online_button':
                    self.alert_player('Online mode is not available yet!')