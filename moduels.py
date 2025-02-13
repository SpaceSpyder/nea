from dataclasses import dataclass, field
from typing import List

@dataclass
class Player:
    username: str
    isPlayer1: bool
    health: int
    mana: int

@dataclass
class Card:
    name: str
    attack: int
    cost: int
    health: int

@dataclass
class GameBoard:
    p2Defence: List[Card] = field(default_factory=list)
    p2Attack: List[Card] = field(default_factory=list)
    
    p1Attack: List[Card] = field(default_factory=list)
    p1Defence: List[Card] = field(default_factory=list)

    p1bank: List[Card] = field(default_factory=list)
    p2bank: List[Card] = field(default_factory=list)

@dataclass
class Game:
    player1: Player
    player2: Player
    gameID: int
    roundNum: int
    gameBoard: GameBoard
    isPlayer1Turn: bool = True
