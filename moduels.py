class player: 
    def __init__(self, username, isPlayer1, health, mana):
        self.username = username
        self.isPlayer1 = isPlayer1
        self.health = health
        self.mana = mana


class game:
    def __init__(self, player1, player2, gameID, roundNum, gameBoard):
        self.player1 = player1
        self.player2 = player2
        self.gameID = gameID
        self.isPlayer1Turn = True
        self.roundNum = 1
                       # player1                     player2                   bank
                       #   attack      defence        attack      defence       player1     player2
        self.gameBoard = [[[0,0,0,0,0],[0,0,0,0,0]], [[0,0,0,0,0],[0,0,0,0,0]],[[0,0,0,0,0],[0,0,0,0,0]],]





