from dataclasses import dataclass
import json

@dataclass
class Player:
    username: str
    isPlayer1: bool
    health: int
    mana: int

@dataclass
class CardSpread:
    card1: str
    card2: str
    card3: str
    card4: str
    card5: str

@dataclass
class GameBoard:
    p1Attack: CardSpread
    p1Defence: CardSpread
    p2Attack: CardSpread
    p2Defence: CardSpread
    p1bank: CardSpread
    p2bank: CardSpread

@dataclass
class Game:
    player1: Player
    player2: Player
    gameID: int
    roundNum: int
    gameBoard: GameBoard
    isPlayer1Turn: bool = True
    isPlayer1: bool = True
