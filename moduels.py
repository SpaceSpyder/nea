from dataclasses import dataclass
import json

@dataclass
class Player:
    username: str
    isPlayer1: bool
    health: int
    mana: int

@dataclass
class GameBoard:
    p1Attack: int
    p1Defence: int
    p2Attack: int
    p2Defence: int
    p1bank: int
    p2bank: int

@dataclass
class CardSpread:
    card1: str
    card2: str
    card3: str
    card4: str
    card5: str

@dataclass
class Game:
    player1: Player
    player2: Player
    gameID: int
    roundNum: int
    gameBoard: GameBoard
    isPlayer1Turn: bool = True
