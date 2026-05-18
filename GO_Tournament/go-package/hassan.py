# -*- coding: utf-8 -*-
from time import time
import Goban
from numpy.random import normal
from playerInterface import *
import math

def findNeighbors(stone):
    neighbors_list = []
    position = divmod(stone, 8) 
    candidates = (
        (position[0]-1, position[1]), 
        (position[0], position[1]-1), 
        (position[0], position[1]+1), 
        (position[0]+1, position[1])
    )
    for pos in candidates:
        if 0 <= pos[0] < 8 and 0 <= pos[1] < 8:
            neighbors_list.append(8 * pos[0] + pos[1])
    return neighbors_list

class myPlayer(PlayerInterface):
    pruneScore = 20000

    def __init__(self):
        self._board = Goban.Board()
        self._mycolor = None
        self.corners = [0, 7, 56, 63]
        self.time_left = 30 * 60  

    def evaluate(self, board):
        b = list(board)
        empty = b.count(0)
        win_score = 100 - empty

        if self._hasCapturedCorner(b):
            return self.pruneScore

        my_score, oppo_score = self._getScores()

        if self._isWinningClearly(my_score, oppo_score):
            return self.pruneScore

        my_groups = self._buildGroups(b, self._mycolor)
        oppo_groups = self._buildGroups(b, self._opponent)

        my_groups_liberties = self._getGroupsLiberties(b, my_groups)
        oppo_groups_liberties = self._getGroupsLiberties(b, oppo_groups)

        if self._hasAtariGroup(my_groups_liberties):
            return (win_score - 10000) / 2

        win_score = self._evaluateOpponentGroups(win_score, oppo_groups_liberties)

        win_score += self._scoreMyGroups(my_groups, my_groups_liberties)
        win_score -= self._scoreOpponentGroups(oppo_groups, oppo_groups_liberties)

        win_score += self._groupsLibertiesBalance(my_groups_liberties, oppo_groups_liberties)

        # Add small noise to avoid ties
        x = normal(1, 0.1)
        return win_score + x * (oppo_groups_liberties.count(2) - my_groups_liberties.count(2))

    def _hasCapturedCorner(self, board_list):
        for corner in self.corners[:]:  # Copy to avoid modifying while iterating
            if board_list[corner] == self._mycolor:
                self.corners.remove(corner)
                return True
        return False

    def _getScores(self):
        black_score, white_score = self._board.compute_score()
        if self._mycolor == 1:
            return black_score, white_score
        else:
            return white_score, black_score

    def _isWinningClearly(self, my_score, oppo_score):
        return my_score >= (oppo_score * 2) and oppo_score > 4

    def _buildGroups(self, board_list, color):
        groups = []
        visited = set()

        def dfs(stone, group):
            for n in findNeighbors(stone):
                if 0 <= n < len(board_list):
                    if board_list[n] == color and n not in group:
                        group.add(n)
                        dfs(n, group)

        for i in range(len(board_list)):
            if board_list[i] == color and i not in visited:
                group = set([i])
                dfs(i, group)
                visited |= group
                groups.append(list(group))
        return groups

    def _getGroupsLiberties(self, board_list, groups):
        liberties = []
        for group in groups:
            group_liberties = set()
            for stone in group:
                for n in findNeighbors(stone):
                    if 0 <= n < len(board_list) and board_list[n] == 0:
                        group_liberties.add(n)
            liberties.append(len(group_liberties))
        return liberties

    def _hasAtariGroup(self, liberties_list): # Check if any group has 1 or fewer liberties
        for lib in liberties_list:
            if lib <= 1:
                return True
        return False

    def _evaluateOpponentGroups(self, win_score, oppo_groups_liberties):
        pt = 0
        for lib in oppo_groups_liberties:
            if lib == 1:
                win_score += 50
            if lib == 0:
                pt += 1
                if pt == 2:
                    return self.pruneScore
                else:
                    win_score += 100
        return win_score

    def _scoreMyGroups(self, my_groups, my_groups_liberties):
        score = 0
        for i in range(len(my_groups)):
            if len(my_groups[i]) >= 2:
                score += (
                    len(my_groups[i]) * my_groups_liberties[i]
                    + my_groups_liberties[i] * 5
                    + 20
                )
        return score

    def _scoreOpponentGroups(self, oppo_groups, oppo_groups_liberties):
        score = 0
        for i in range(len(oppo_groups)):
            score += len(oppo_groups[i]) * oppo_groups_liberties[i]
        return score

    def _groupsLibertiesBalance(self, my_groups_liberties, oppo_groups_liberties):
        my_count_2 = my_groups_liberties.count(2)
        oppo_count_2 = oppo_groups_liberties.count(2)
        return (oppo_count_2 - my_count_2) + (sum(my_groups_liberties) - sum(oppo_groups_liberties))

    def alphaBetaSearch(self, board, depth, alpha, beta, startingTime, deadline):
        legalMoves = board.generate_legal_moves()
        myTurn = board._nextPlayer == self._mycolor
        result = self.evaluate(board)
        if (time() - startingTime >= deadline 
            or board.is_game_over() 
            or depth == 0 
            or not legalMoves 
            or abs(result) >= self.pruneScore):
            return result

        if myTurn:
            for m in legalMoves:
                board.push(m)
                alpha = max(alpha, self.alphaBetaSearch(board, depth - 1, alpha, beta, startingTime, deadline))
                board.pop()
                if beta <= alpha:
                    break
            return alpha
        else:
            for m in legalMoves:
                board.push(m)
                beta = min(beta, self.alphaBetaSearch(board, depth - 1, alpha, beta, startingTime, deadline))
                board.pop()
                if beta <= alpha:
                    break
            return beta

    def iterativeDeepeningSearch(self, board, deadline):
        begin = time()
        finish = begin + deadline
        depth = 1
        result = 0
        while time() < finish:
            value = self.alphaBetaSearch(board, depth, -math.inf, math.inf, time(), finish - time())
            if value >= self.pruneScore:
                return value
            result = value
            depth += 1
        return result

    def selectNextMove(self, time_limit):
        legalMoves = self._board.generate_legal_moves()
        if -1 in legalMoves:
            legalMoves.remove(-1)

        if len(legalMoves) < 64:
            black_score, white_score = self._board.compute_score()
            if self._board._lastPlayerHasPassed:
                if (self._mycolor == 1 and black_score > white_score) or (self._mycolor == 2 and white_score > black_score):
                    return -1
            if not legalMoves:
                return -1

        bestMove, maxGain = None, -math.inf
        for m in legalMoves:
            self._board.push(m)
            gain = self.iterativeDeepeningSearch(self._board, time_limit / len(legalMoves))
            self._board.pop()
            if gain >= self.pruneScore:
                return m
            if gain > maxGain:
                maxGain, bestMove = gain, m
        return bestMove if bestMove is not None else -1

    def getPlayerName(self):
        return "Hassen & Karim"

    def getPlayerMove(self):
        if self._board.is_game_over():
            print("Referee told me to play but the game is over!")
            return "PASS"
        if self.time_left <= 0:
            print("Timeout: plus de temps disponible, je passe.")
            return "PASS"
        TIME_LIMIT = min(5.0, self.time_left)  
        start_time = time()
        move = self.selectNextMove(TIME_LIMIT)
        self._board.push(move)
        print("I am playing", self._board.move_to_str(move))
        self._board.prettyPrint()  
        elapsed = time() - start_time
        self.time_left -= elapsed
        return Goban.Board.flat_to_name(move)

    def playOpponentMove(self, move):
        print("Opponent played", move)
        if isinstance(move, int):
            self._board.push(move)
        else:
            self._board.push(Goban.Board.name_to_flat(move))

    def newGame(self, color):
        self._mycolor = color
        self._opponent = Goban.Board.flip(color)

    def endGame(self, winner):
        black_score, white_score = self._board.compute_score()
        print(f"Final Score: Black = {black_score}, White = {white_score}")
        self._board.prettyPrint()  
        print("I won!!!" if self._mycolor == winner else "I lost :(!!")
