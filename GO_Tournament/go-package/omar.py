# -*- coding: utf-8 -*-
''' This is the file you have to modify for the tournament. Your default AI player must be called by this module, in the
myPlayer class.

Right now, this class contains the copy of the randomPlayer. But you have to change this!
'''

import time
import Goban 
from random import choice
from playerInterface import *

# Constantes pour pondérer les composantes de l'heuristique.
#  - une capture vaut beaucoup plus qu'une pierre simple sur le plateau
#  - perdre un groupe (atari) est catastrophique => grosse pénalité
#  - le territoire est ce qui détermine le score final, donc poids fort
W_STONES    = 1     # différence de pierres posées
W_CAPTURED  = 8     # différence de pierres capturées (geste tactique fort)
W_TERRITORY = 4     # différence de territoire (chinese scoring)
W_ATARI     = 15    # pénalité par groupe en atari (1 seule liberté)
W_LIBERTY   = 1     # bonus par liberté supplémentaire (groupes solides)

# Constantes "infinies" pour les positions terminales (victoire/défaite certaine)
WIN_SCORE  = float('inf')
LOSS_SCORE = float('-inf')

DEPTH_MINIMAX = 2
DEPTH_ALPHABETA = 3

TIME_LIMIT_PER_MOVE = 3.0

class TimeoutError_(Exception):
    pass

class myPlayer(PlayerInterface):
    ''' Example of a random player for the go. The only tricky part is to be able to handle
    the internal representation of moves given by legal_moves() and used by push() and 
    to translate them to the GO-move strings "A1", ..., "J8", "PASS". Easy!

    '''

    def __init__(self):
        self._board = Goban.Board()
        self._mycolor = None

    def getPlayerName(self):
        return "El Badri Bamouss"

    def getPlayerMove(self):
        if self._board.is_game_over():
            print("Referee told me to play but the game is over!")
            return "PASS"
        
        moves = self._board.legal_moves() # Dont use weak_legal_moves() here!
        # move = choice(moves)
        # _, move = self.MiniMax(self._board, DEPTH_MINIMAX, self._mycolor)
        ## on gere le temps dans alphabeta        
        try:
            deadline = time.time() + TIME_LIMIT_PER_MOVE
            _, move = self.alphabeta(self._board, DEPTH_ALPHABETA,float("-inf"), float("inf"), self._mycolor, deadline)
        # surete
        except TimeoutError_:
            try:
                _, move = self.alphabeta(self._board, 1, float("-inf"), float("inf"), self._mycolor, time.time() + 0.5)
            except TimeoutError_:
                 moves = self._board.legal_moves()
                 move = moves[0] if moves else -1
            
        # dans le cas du fin
        if move == None:
            move = -1           # PASS
        self._board.push(move)

        # New here: allows to consider internal representations of moves
        print("I am playing ", self._board.move_to_str(move))
        # print("My current board :")
        # self._board.prettyPrint()
         # move is an internal representation. To communicate with the interface I need to change if to a string
        return Goban.Board.flat_to_name(move) 

    def playOpponentMove(self, move):
        print("Opponent played ", move) # New here
        # the board needs an internal represetation to push the move.  Not a string
        self._board.push(Goban.Board.name_to_flat(move)) 

    def newGame(self, color):
        self._board = Goban.Board()
        self._mycolor = color
        self._opponent = Goban.Board.flip(color)

    def endGame(self, winner):
        if self._mycolor == winner:
            print("I won!!!")
        else:
            print("I lost :(!!")

    # evaluer les feuilles
    # Une position est bonne pour mon IA si elle a plus de pierres, plus de captures, plus de territoire, plus de libertés, et si l’adversaire a plus de groupes en atari que moi.
    def evaluate(self, board):
        my_color = self._mycolor

        # Dans cette cas on connait deja la reponse, c'est pas forcement une strategie gagnant
        if board.is_game_over():
            result = board.result()
            if result == "1/2-1/2":
                return 0
            # result() est "1-0" si BLANC gagne, "0-1" si NOIR gagne
            if (result == "1-0" and my_color == Goban.Board._WHITE) or (result == "0-1" and my_color == Goban.Board._BLACK):
                return WIN_SCORE
            return LOSS_SCORE

        # 1. pierres sur le plateau
        if my_color == Goban.Board._BLACK:
            stones_diff   = board._nbBLACK - board._nbWHITE
            captured_diff = board._capturedWHITE - board._capturedBLACK
        else:
            stones_diff   = board._nbWHITE - board._nbBLACK
            captured_diff = board._capturedBLACK - board._capturedWHITE

        # 2. libertés / atari
        # On parcourt chaque groupe :
        #   - liberté == 1  -> ATARI : on peut la perdre :(
        #   - liberté élevée -> groupe solide
        my_atari, opp_atari = 0, 0
        my_liberties, opp_liberties = 0, 0
        seen_strings = set()

        for fc in range(Goban.Board._BOARDSIZE ** 2):
            color = int(board._board[fc])
            if color == Goban.Board._EMPTY:
                continue
            # Trouver le numéro de chaîne (union-find dans Goban.py)
            s = board._getStringOfStone(fc)
            if s in seen_strings:
                continue
            seen_strings.add(s)
            libs = int(board._stringLiberties[s])
            if color == my_color:
                my_liberties += libs
                if libs == 1:
                    my_atari += 1
            else:
                opp_liberties += libs
                if libs == 1:
                    opp_atari += 1

        atari_diff    = opp_atari - my_atari        # ses ataris = bon pour moi
        liberty_diff  = my_liberties - opp_liberties

        # 3. chinese scoring
        # board._count_areas() retourne (only_black, only_white, contested).
        # C'est un peu coûteux (BFS sur les cases vides) mais très informatif.
        only_black, only_white, _ = board._count_areas()
        if my_color == Goban.Board._BLACK:
            territory_diff = only_black - only_white
        else:
            territory_diff = only_white - only_black

        stones_diff = int(stones_diff)
        captured_diff = int(captured_diff)
        territory_diff = int(territory_diff)
        atari_diff = int(atari_diff)
        liberty_diff = int(liberty_diff)
        
        # Combinaison linéaire pondérée
        score = (W_STONES    * stones_diff
                 + W_CAPTURED  * captured_diff
                 + W_TERRITORY * territory_diff
                 + W_ATARI     * atari_diff
                 + W_LIBERTY   * liberty_diff)
        
        return score
    # retourne score et position
    def MiniMax(self, board, depth, player_color):
        if depth == 0 or board.is_game_over():
            return self.evaluate(board), None

        
        # moi je veux maximaliser
        if player_color == self._mycolor :
            max_score = float("-inf")
            best_move = None
            for move in board.legal_moves():
                board.push(move)
                score,_ = self.MiniMax(board, depth-1,Goban.Board.flip(player_color))
                board.pop()
                if max_score < score:
                    best_move = move
                    max_score = score
            return max_score, best_move
        # enemer min
        else:
            min_score = float("inf")
            best_move = None
            for move in board.legal_moves():
                board.push(move)
                score,_ = self.MiniMax(board, depth-1,Goban.Board.flip(player_color))
                board.pop()
                if score < min_score:
                    best_move = move
                    min_score = score
            return min_score, best_move


    def alphabeta(self, board, depth, alpha, beta, player_color, deadline):
        if time.time() > deadline:
            raise TimeoutError_()
        if depth == 0 or board.is_game_over():
            return self.evaluate(board), None

        # Max
        if player_color == self._mycolor:
            max_score = float("-inf")
            best_move = None
            for move in board.legal_moves():
                board.push(move)
                try:
                    score,_ = self.alphabeta(board, depth-1, alpha, beta, Goban.Board.flip(player_color), deadline)
                finally:
                    board.pop()

                if max_score < score:
                    max_score = score
                    best_move = move
                alpha = max(alpha, max_score)
                # condition d'arret
                if beta <= alpha:
                    break
            return max_score, best_move
        else:
            min_score = float("inf")
            best_move = None
            for move in board.legal_moves():
                board.push(move)
                try:
                    score,_ = self.alphabeta(board, depth-1,alpha, beta, Goban.Board.flip(player_color), deadline)
                finally:
                    board.pop()

                if min_score > score:
                    min_score = score
                    best_move = move
                beta = min(beta, min_score)
                # condition d'arret
                if beta <= alpha:
                    break
            return min_score, best_move
                