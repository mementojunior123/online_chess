import pygame
from game.sprite import Sprite
from core.core import core_object


class ChessBoard(Sprite):
    TILE_SIZE = 61
    LIGHT_COLOR = '#ffffdd'
    DARK_COLOR = '#86a666'
    test_image = pygame.surface.Surface((TILE_SIZE * 8, TILE_SIZE * 8))
    pygame.draw.rect(test_image, DARK_COLOR, (0, 0, *test_image.get_size()))
    inactive_elements : list['ChessBoard'] = []
    active_elements : list['ChessBoard'] = []
    def __init__(self):
        super().__init__()
        ChessBoard.inactive_elements.append(self)
    
    @classmethod
    def spawn(cls):
        element = cls.inactive_elements[0]

        element.image = cls.test_image
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(480, 270)
        element.align_rect()
        element.zindex = 0

        cls.unpool(element)
        return element
    
    def clean_instance(self):
        super().clean_instance()

ChessBoard()
Sprite.register_class(ChessBoard)