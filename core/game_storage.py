from sys import platform as PLATFORM
import json
import os
from typing import Any, TypedDict
from utils.helpers import AnyJson

if PLATFORM == 'emscripten':
    from platform import window

class GameData(TypedDict):
    high_score : int

class GameStorage:
    '''Most of these functions are incomplete and need implementing.\nThis module is made to handle file I/O and saving on multiple platforms.'''
    def __init__(self) -> None:
        self.high_score : int = 0

    def reset(self):
        self.high_score = 0
    
    def validate_data(self, data : dict) -> bool:
        if data is None: return False
        if 'high_score' not in data: return False
        return True

    def _get_data(self) -> GameData:
        return {'high_score' : self.high_score}

    def _load_data(self, data : GameData) -> bool:
        if not self.validate_data(data):
            print('Data is invalid!')
            return False
        self.high_score = data['high_score']
        return True

    def load(self, is_web : bool = False) -> bool:
        return self._load_from_file() if not is_web else self._load_from_web()
    
    def save(self, is_web : bool = False) -> None:
        self._save_to_file() if not is_web else self._save_to_web()

    def _load_from_file(self, file_path : str = 'assets/data/game_info.json') -> bool:
        with open(file_path, 'r') as file:
            data = json.load(file)
        if data:
            return self._load_data(data)

    def _save_to_file(self, file_path : str = 'assets/data/game_info.json') -> None:
        data = self._get_data()
        with open(file_path, 'w') as file:
            json.dump(data, file)

    def _load_from_web(self) -> bool:
        web_data = self.get_web('GameData')
        if web_data is not None:
            data = json.loads(web_data)
            if data is not None:
                self._load_data(data)

    def _save_to_web(self) -> None:
        data = self._get_data()
        self.set_web('GameData', json.dumps(data))

    def get_web(self, key : str) -> str:
        window.localStorage.getItem(key)

    def set_web(self, key : str, value : Any):
        window.localStorage.setItem(key, str(value))