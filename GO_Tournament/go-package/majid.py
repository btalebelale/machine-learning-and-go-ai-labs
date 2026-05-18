from playerInterface import PlayerInterface
import Goban 
import math
import time

class majidPlayer(PlayerInterface):
    def __init__(self):
        self._board = Goban.Board()
        self._mycolor = None
        self.eye_weight = 50
        self.cut_weight = -50
        self.timeOut = 10
        self.begin = 0

        self.weightedBoard = [
            20,  30,  40,  50,  50,  40,  30,  20,
            30,  40,  60,  70,  70,  60,  40,  30,
            40,  60,  80, 100, 100,  80,  60,  40,
            50,  70, 100, 120, 120, 100,  70,  50,
            50,  70, 100, 120, 120, 100,  70,  50,
            40,  60,  80, 100, 100,  80,  60,  40,
            30,  40,  60,  70,  70,  60,  40,  30,
            20,  30,  40,  50,  50,  40,  30,  20,
        ]

    def getPlayerName(self):
        return "majid"

    def getPlayerMove(self):
        if self._board.is_game_over():
            print("Referee told me to play but the game is over!")
            return "PASS" 
        self.begin = time.time()
        state = self.alpha_beta(3, -math.inf, math.inf, True) #using the alpha beta algorithm
        move=state['move']
        self._board.push(move)
        print("I am playing ", self._board.move_to_str(move))
        print("My current board :")
        self._board.prettyPrint()
        return Goban.Board.flat_to_name(move) 

    def playOpponentMove(self, move):
        print("Opponent played ", move)
        self._board.push(Goban.Board.name_to_flat(move)) 

    def newGame(self, color):
        self._mycolor = color

    def endGame(self, winner):
        if self._mycolor == winner:
            print("I won!!!")
        else:
            print("I lost :(!!")


    def alpha_beta(self, depth, alpha, beta, is_maximizing_player):
        if depth == 0 or time.time() - self.begin >= self.timeOut or self._board.is_game_over():
            return {'score': self.evaluate_position(), 'move': None}
        
        if is_maximizing_player:
            best_state = {'score': -math.inf, 'move': None}
        else:
            best_state = {'score': math.inf, 'move': None}

        legal_moves = self._board.legal_moves()
        for move in legal_moves:
            self._board.push(move)
            if is_maximizing_player:
                result = self.alpha_beta(depth - 1, alpha, beta, False)
                score = result['score']
                if score > alpha:
                    alpha = score
                    best_state['score'] = score
                    best_state['move'] = move
            else:
                result = self.alpha_beta(depth - 1, alpha, beta, True)
                score = result['score']
                if score < beta:
                    beta = score
                    best_state['score'] = score
                    best_state['move'] = move
            self._board.pop()
            if alpha >= beta:
                break

        return best_state


    def evaluate_position(self):
        if self._board.is_game_over():
            return self.evaluate_game_over()

        pawn_number_score = self.calculate_pawn_number_score()

        eye_score = self.evaluate_eyes()
        cut_score = self.evaluate_cuts()

        liberties_string_score = self.evaluate_liberties_string_score()

        score = (int(eye_score) * self.eye_weight) + (int(cut_score) * self.cut_weight) + int(liberties_string_score) + int(pawn_number_score)
        return score
    
    

    def evaluate_game_over(self):
        final_giga_score = 100000
        final_result = self._board.result()
        final_giga_score *= -1 if self._mycolor == self._board._BLACK else 1
        return final_giga_score if final_result == "1-0" else (-final_giga_score if final_result == "0-1" else 0)

    def calculate_pawn_number_score(self):
        pawn_number_score = int(self._board._nbWHITE) - int(self._board._nbBLACK) if self._mycolor == self._board._WHITE else int(self._board._nbBLACK) - int(self._board._nbWHITE)
        return pawn_number_score

    def evaluate_liberties_string_score(self):
        liberties_string_score = 0
        for index in range(len(self._board)):
            if self._board[index] == self._board._EMPTY:
                continue
            root_string = self._board._getStringOfStone(index)
            if self._board[index] == self._mycolor:
                liberties_string_score += int(self._board._stringLiberties[root_string]) * self.weightedBoard[index]
            else:
                liberties_string_score -= int(self._board._stringLiberties[root_string]) * self.weightedBoard[index]
        return liberties_string_score



    def evaluate_eyes(self):
        eye_score = 0
        for index in range(len(self._board)):
            i = index//9
            j= index % 9
            if self._board[index] == self._board._EMPTY:
                neighbors = self.get_neighbors(index)
                if len(neighbors) == 4:
                    # Vérifier si les voisins forment un œil
                    eye = True
                    for x in neighbors:
                        if self._board[x] != self._mycolor:
                            eye = False
                            break
                    if eye:
                        eye_score += 1
        return eye_score

    def evaluate_cuts(self):
        cut_score = 0
        for index in range(len(self._board)):
            if self._board[index] != self._board._EMPTY:
                root_string = self._board._getStringOfStone(index)
                if int(self._board._stringLiberties[root_string]) == 1:
                    cut_score -= 1
        return cut_score
    

    
    def get_neighbors(self, index):
        size = self._board._BOARDSIZE
        neighbors = []
        row = index // size
        col = index % size

        # Ajouter les voisins haut, bas, gauche et droite
        if row > 0:
            neighbors.append(index - size)
        if row < size - 1:
            neighbors.append(index + size)
        if col > 0:
            neighbors.append(index - 1)
        if col < size - 1:
            neighbors.append(index + 1)

        return neighbors



    def update_weighted_board(self, move):
        size = self._board._BOARDSIZE
        row, col = move // size, move % size

        # Définir des poids plus élevés au centre du plateau
        center_weight = 100
        center_range = 2
        for i in range(row - center_range, row + center_range + 1):
            for j in range(col - center_range, col + center_range + 1):
                if 0 <= i < size and 0 <= j < size:
                    self.weightedBoard[i * size + j] = center_weight

        # Définir des poids plus élevés pour les coins
        corner_weight = 150
        corner_positions = [(0, 0), (0, size - 1), (size - 1, 0), (size - 1, size - 1)]
        for pos in corner_positions:
            self.weightedBoard[pos[0] * size + pos[1]] = corner_weight

        # Définir des poids plus élevés pour les bords
        edge_weight = 120
        for i in range(size):
            if i == row:
                for j in range(size):
                    self.weightedBoard[i * size + j] = edge_weight
            else:
                self.weightedBoard[i * size + col] = edge_weight

        # Ajuster les poids des cases adjacentes au coup joué
        adjacent_weight = 80
        for i in range(row - 1, row + 2):
            for j in range(col - 1, col + 2):
                if 0 <= i < size and 0 <= j < size:
                    self.weightedBoard[i * size + j] = adjacent_weight

myPlayer = majidPlayer
