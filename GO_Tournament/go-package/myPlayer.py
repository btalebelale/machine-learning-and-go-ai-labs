# Binome: Mohamed Kraimy & Bella Taleb El Alem
import time
import Goban
import numpy as np
from playerInterface import *

_BOARD_SIZE = Goban.Board._BOARDSIZE
_INF = float('inf')
_CENTER = _BOARD_SIZE // 2

class _Timeout(Exception):
    pass

class myPlayer(PlayerInterface):
    _TOTAL_BUDGET = 45 * 60 - 30  # 2670s (30s safety buffer)
    _TIME_EARLY = 10.0
    _TIME_MID   = 35.0
    _TIME_LATE  = 55.0

    def __init__(self):
        self._board = Goban.Board()
        self._mycolor = None
        self._tt = {}
        self._time_used = 0.0

    def getPlayerName(self):
        return "MohamedBTE"

    def newGame(self, color):
        self._board = Goban.Board()
        self._mycolor = color
        self._tt = {}
        self._time_used = 0.0

    def playOpponentMove(self, move):
        self._board.push(Goban.Board.name_to_flat(move))

    def endGame(self, winner):
        if self._mycolor == winner:
            print("I won!!!")
        else:
            print("I lost :(")

    def getPlayerMove(self):
        if self._board.is_game_over():
            return "PASS"
        move_count = len(self._board._historyMoveNames)
        if move_count < 15:
            base_limit = self._TIME_EARLY
        elif move_count < 45:
            base_limit = self._TIME_MID
        else:
            base_limit = self._TIME_LATE
        time_left = self._TOTAL_BUDGET - self._time_used
        time_limit = min(base_limit, time_left * 0.9)
        start = time.time()
        moves = self._order_moves(self._board._currentHash)
        best_move = moves[0] if moves else -1
        prev_score = 0
        for depth in range(1, 20):
            if time.time() - start >= time_limit * 0.9:
                break
            try:
                move, score = self._root_negamax(depth, start, time_limit, prev_score)
                best_move = move
                prev_score = score
            except _Timeout:
                break
        self._board.push(best_move)
        self._time_used += time.time() - start
        return Goban.Board.flat_to_name(best_move)

    def _root_negamax(self, depth, start, time_limit, prev_score=0):
        window = 8
        alpha = prev_score - window
        beta  = prev_score + window
        for attempt in range(3):
            moves = self._order_moves(self._board._currentHash)
            best_move = moves[0] if moves else -1
            best_score = -_INF
            a = alpha
            for m in moves:
                valid = self._board.push(m)
                if not valid:
                    self._board.pop()
                    continue
                try:
                    score = -self._negamax(depth - 1, -beta, -a, start, time_limit)
                except _Timeout:
                    self._board.pop()
                    raise
                self._board.pop()
                if score > best_score:
                    best_score = score
                    best_move = m
                a = max(a, score)
            if best_score <= alpha:
                alpha = best_score - window * (2 ** attempt)
            elif best_score >= beta:
                beta = best_score + window * (2 ** attempt)
            else:
                break
        self._tt[self._board._currentHash] = (depth, best_score, 'EXACT', best_move)
        return best_move, best_score

    def _negamax(self, depth, alpha, beta, start, time_limit):
        if time.time() - start > time_limit:
            raise _Timeout()
        if self._board.is_game_over():
            return self._eval_terminal()
        if depth == 0:
            return self._evaluate()

        h = self._board._currentHash
        if h in self._tt:
            tt_depth, tt_score, tt_flag, tt_move = self._tt[h]
            if tt_depth >= depth:
                if tt_flag == 'EXACT':
                    return tt_score
                elif tt_flag == 'LOWER':
                    alpha = max(alpha, tt_score)
                elif tt_flag == 'UPPER':
                    beta  = min(beta,  tt_score)
                if alpha >= beta:
                    return tt_score

        orig_alpha = alpha
        moves = self._order_moves(h)
        best = -_INF
        best_move = moves[0] if moves else -1
        for m in moves:
            valid = self._board.push(m)
            if not valid:
                self._board.pop()
                continue
            try:
                val = -self._negamax(depth - 1, -beta, -alpha, start, time_limit)
            except _Timeout:
                self._board.pop()
                raise
            self._board.pop()
            if val > best:
                best = val
                best_move = m
            alpha = max(alpha, best)
            if alpha >= beta:
                break

        flag = 'EXACT' if orig_alpha < best < beta else ('LOWER' if best >= beta else 'UPPER')
        self._tt[h] = (depth, best, flag, best_move)
        return best

    def _order_moves(self, board_hash=None):
        moves = self._board.legal_moves()
        non_pass = [m for m in moves if m != -1]
        captures = [m for m in non_pass if self._is_capture(m)]
        rest     = [m for m in non_pass if not self._is_capture(m)]
        rest.sort(key=self._dist_center)
        ordered = captures + rest + [-1]
        tt_entry = self._tt.get(board_hash)
        if tt_entry is not None:
            tt_move = tt_entry[3]
            if tt_move in ordered:
                ordered.remove(tt_move)
                ordered.insert(0, tt_move)
        return ordered

    def _is_capture(self, m):
        opponent = Goban.Board.flip(self._board._nextPlayer)
        b = self._board
        i = b._neighborsEntries[m]
        while b._neighbors[i] != -1:
            fn = b._neighbors[i]
            if b[fn] == opponent:
                root = b._getStringOfStone(fn)
                if b._stringLiberties[root] == 1:
                    return True
            i += 1
        return False

    def _dist_center(self, m):
        x, y = Goban.Board.unflatten(m)
        return abs(x - _CENTER) + abs(y - _CENTER)

    def _eval_terminal(self):
        winner = self._board.result_number()
        if winner == Goban.Board._EMPTY:
            return 0
        return 100000 if winner == self._board._nextPlayer else -100000

    _WEIGHTS = [
        20,  30,  40,  50,  50,  40,  30,  20,
        30,  40,  60,  70,  70,  60,  40,  30,
        40,  60,  80, 100, 100,  80,  60,  40,
        50,  70, 100, 120, 120, 100,  70,  50,
        50,  70, 100, 120, 120, 100,  70,  50,
        40,  60,  80, 100, 100,  80,  60,  40,
        30,  40,  60,  70,  70,  60,  40,  30,
        20,  30,  40,  50,  50,  40,  30,  20,
    ]

    def _evaluate(self):
        b = self._board
        my  = b._nextPlayer
        opp = Goban.Board.flip(my)
        move_count = len(b._historyMoveNames)

        score_b, score_w = b.compute_score()
        if my == Goban.Board._BLACK:
            territory = score_b - score_w
            captured  = int(b._capturedWHITE) - int(b._capturedBLACK)
        else:
            territory = score_w - score_b
            captured  = int(b._capturedBLACK) - int(b._capturedWHITE)

        my_atari = opp_atari = 0
        my_libs  = opp_libs  = 0
        my_eyes  = opp_eyes  = 0
        my_pos   = opp_pos   = 0
        seen = set()
        W = self._WEIGHTS

        for i in range(_BOARD_SIZE * _BOARD_SIZE):
            stone = b[i]
            if stone == Goban.Board._EMPTY:
                ni = b._neighborsEntries[i]
                nb = []
                while b._neighbors[ni] != -1:
                    nb.append(b._neighbors[ni])
                    ni += 1
                if nb and all(b[n] == my  for n in nb): my_eyes  += 1
                elif nb and all(b[n] == opp for n in nb): opp_eyes += 1
                continue
            if stone == my:
                my_pos += W[i]
            else:
                opp_pos += W[i]
            root = b._getStringOfStone(i)
            if root in seen:
                continue
            seen.add(root)
            libs = int(b._stringLiberties[root])
            if stone == my:
                my_libs += libs
                if libs == 1: my_atari += 1
            else:
                opp_libs += libs
                if libs == 1: opp_atari += 1

        if move_count < 15:
            w_ter, w_cap, w_ata, w_lib, w_eye, w_pos = 2, 2,  3,  1, 2, 1.5
        elif move_count < 45:
            w_ter, w_cap, w_ata, w_lib, w_eye, w_pos = 4, 8,  15, 1, 3, 0.3
        else:
            w_ter, w_cap, w_ata, w_lib, w_eye, w_pos = 6, 8,  15, 1, 4, 0.1

        return (w_ter * territory
                + w_cap * captured
                + w_ata * (opp_atari - my_atari)
                + w_lib * (my_libs   - opp_libs)
                + w_eye * (my_eyes   - opp_eyes)
                + w_pos * (my_pos    - opp_pos))