from enum import Enum

class BoardDisplayStyle(Enum):
    STANDARD = 'Standard'
    BLACK_STANDARD = 'BlackStandard'
    BLACK_MIRRORED = 'BlackMirrored'

def board_to_visual_coords(x : int, y : int, style : BoardDisplayStyle) -> tuple[int, int]:
    new_x : int = x if style in {BoardDisplayStyle.STANDARD, BoardDisplayStyle.BLACK_MIRRORED} else 9 - x
    new_y : int = 9 - y if style in {BoardDisplayStyle.STANDARD} else y
    return (new_x - 1, new_y - 1)


def visual_to_board_coords(x : int, y : int, style : BoardDisplayStyle) -> tuple[int, int]:
    x += 1
    y += 1
    new_x : int = x if style in {BoardDisplayStyle.STANDARD, BoardDisplayStyle.BLACK_MIRRORED} else 9 - x
    new_y : int = 9 - y if style in {BoardDisplayStyle.STANDARD} else y
    return (new_x, new_y)

chosen_mode = BoardDisplayStyle.STANDARD
test_xy : tuple[int, int] = (0, 0)
print(board_to_visual_coords(*visual_to_board_coords(*test_xy, chosen_mode), chosen_mode))