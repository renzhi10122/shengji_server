import random


class Card:
    suits = ["hearts", "diamonds", "clubs", "spades"]
    ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    
    def __init__(self, suit, rank, image_name):
        self.suit = suit
        self.rank = rank
        self.actual_suit = suit
        self.image_name = image_name
        self.hand = -1 # -1 is deck, 0-3 is hand, 4-7 is respsective fields, 8 is bottom, 9 is point
        self.selected = '0' # if selected, give number of pixels to raise by
        self.previous = False
        self.current = False
        self.sorting_rank = self.assign_rank(0, 0)
        
    def get_rank(self):
        return self.rank
    
    def get_ordered_rank(self): #so this puts A as 14
        if self.rank == 1:
            return 14
        return self.rank
    
    def get_suit(self):
        return self.suit
    
    def get_actual_suit(self):
        return self.actual_suit

    def assign_rank(self, trump_suit, trump_rank): # Card obj
        # Normal H cards get rank 2 to 14, A=14 skipping out trump rank
        # then trump cards get 16 to 28 skipping out trump rank
        # then normal trump rank gets 29, trump trump rank gets 30
        # small joker 31, big joker 32
        if self.get_suit() == 4:
            if self.get_rank() == 14:
                return 10001
            return 10002
        
        if self.get_rank() == trump_rank:
            if self.get_suit() == trump_suit:
                return 10000
            return 7000 + self.get_ordered_rank() + self.get_suit() * 40
        elif self.get_suit() == trump_suit:
            return self.get_ordered_rank() + 5000
        elif self.get_suit() % 2 == trump_suit % 2:
            return self.get_ordered_rank() + 3500
        
        return self.get_ordered_rank() + self.get_suit() * 40 + ((self.get_suit() - trump_suit) % 2) * 1000

class Deck:
    def __init__(self, num_of_decks = 1, shuffle = True, jokers = True):
        self.cards = []
        
        for i in range(1, num_of_decks + 1):
            suits = ['H', 'D', 'C', 'S']
            for suit in range(0, 4):
                for rank in range(1, 14):
                    self.cards.append(Card(suit, rank, 'static/' + str(rank) + '_' + suits[suit] + '.png'))
                        
            if jokers:
                self.cards.append(Card(4, 14, 'static/B.png'))
                self.cards.append(Card(4, 15, 'static/R.png'))
        
        if shuffle:        
            self.shuffle()
            
    def shuffle(self):
        random.shuffle(self.cards)
            
    def recall(self):
        for card in self.cards:
            card.selected = '0'

    def assign_ranks(self, trump_suit, trump_rank):
        for card in self.cards:
            card.sorting_rank = card.assign_rank(trump_suit, trump_rank)

class Game:
    def __init__(self, stacks):
        self.to_be_saved = ''
        self.stacks = {}
        for stack in stacks:
            args = stacks[stack]
            self.stacks[stack] = Stack(*args) if args else Stack()
        self.trump_suit = 3
        self.trump_rank = -1

    def reset(self):
        for stack in self.stacks:
            if not stack == 'deck':
                for card in self.stacks[stack].cards:
                    self.stacks['deck'].append(card)
                self.stacks[stack].cards = []

        random.shuffle(self.stacks['deck'].cards)

    def set_trump_suit(self, trump_suit):
        self.trump_suit = trump_suit

    def set_trump_rank(self, trump_rank):
        self.trump_rank = trump_rank

class Stack:
    def __init__(self, *args):
        if args:
            self.face_up = args[0]
            self.offset = args[1]
            self.cards = args[2]
            self.to_sort = args[3]
        else:
            self.face_up = False
            self.offset = '0'
            self.cards = []
            self.to_sort = False

    def sort_cards(self):
        if self.to_sort:
            self.cards.sort(key=lambda x: x.sorting_rank, reverse=True)

    def update_cards(self, cards):
        self.cards = cards
        self.sort_cards()

    def take_card(self, i = -1):
        return self.cards.pop(i)

    def append(self, card):
        self.cards.append(card)
        self.sort_cards()

    def image_names_to_csv(self):
        return ','.join([c.image_name for c in self.cards])

    def selected_to_csv(self):
        return ','.join([c.selected for c in self.cards])