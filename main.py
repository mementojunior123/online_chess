import pygame
import asyncio

pygame.init()

GAME_ICON = pygame.image.load('assets/icons/template_icon.png')
GAME_TITLE : str = "Online Chess"
pygame.display.set_icon(GAME_ICON)

window_size = (960, 540)
window = pygame.display.set_mode(window_size)

pygame.mixer.set_num_channels(32)

from core.core import Core, core_object

core = core_object
core.init(window)
core.FPS = 120
if core.is_web(): core.setup_web(1)


pygame.display.set_caption(GAME_TITLE)

from game.sprite import Sprite
Sprite._core_hint()

from utils.animation import Animation, AnimationTrack, _sprite_hint
_sprite_hint()

from utils.ui.base_ui_elements import BaseUiElements, UiSprite
from utils.ui.textsprite import TextSprite
from utils.helpers import rotate_around_pivot_accurate, copysign
from utils.particle_effects import ParticleEffect, Particle
from utils.my_timer import Timer
import utils.interpolation as interpolation
import utils.tween_module as TweenModule

import game.game_states as game_states
from game.test_player import TestPlayer

core.settings.set_default({'Brightness' : 0})
core.settings.load()

core.set_brightness(core.settings.info['Brightness'])

core.menu.init()
core.game.init()
game_states.runtime_imports()

clock = pygame.Clock()

async def main():
    while 1:
        core.update_dt(60)
        for event in pygame.event.get():
            core.event_manager.process_event(event)

        if core.game.active == False:
            window.fill(core.menu.bg_color)
            core.menu.update(core.dt)
            core.menu.render(window)
        else:
            core.game.state.main_logic(core.dt)

            window.fill((94,129,162))    
            Sprite.draw_all_sprites(window)
            core.main_ui.update()
            core.main_ui.render(window)

        core.update()
        if core.settings.info['Brightness'] != 0:
            window.blit(core.brightness_map, (0,0), special_flags=core.brightness_map_blend_mode)
            
        pygame.display.update()
        core.frame_counter += 1
        clock.tick(core.FPS)
        await asyncio.sleep(0)

asyncio.run(main())


