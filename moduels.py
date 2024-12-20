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



        class gameBoard:
            def __init__(self, p1Attack, p1Defence, p2Attack, p2Defence, p1bank, p2bank):
                self.p1Attack = p1Attack
                self.p1Defence = p1Defence
                self.p2Attack = p2Attack
                self.p2Defence = p2Defence
                self.p1bank = p1bank
                self.p2bank = p2bank

            class cardSpread:
                def __init__(self, card1, card2, card3, card4, card5):
                    self.card1 = card1
                    self.card2 = card2
                    self.card3 = card3
                    self.card4 = card4
                    self.card5 = card5

                class card:
                    def __init__(self, CardId, Name, Damage, Cost, Health, Image, Rarity):
                        self.CardId = CardId
                        self.Name = Name
                        self.Damage = Damage
                        self.Cost = Cost
                        self.Health = Health
                        self.Image = Image
                        self.Rarity = Rarity
