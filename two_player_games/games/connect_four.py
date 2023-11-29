from dataclasses import fields
from two_player_games.move import Move
from typing import Iterable, List, Optional, Tuple, Union
from two_player_games.game import Game
from two_player_games.player import Player
from two_player_games.state import State


class ConnectFour(Game):
    """Class that represents the hex game"""
    FIRST_PLAYER_DEFAULT_CHAR = '1'
    SECOND_PLAYER_DEFAULT_CHAR = '2'

    def __init__(self, size: Tuple[int, int] = (7, 6), first_player: Player = None, second_player: Player = None):
        """
        Initializes game.

        Parameters:
            size: the size of the game as number of columns and rows
            first_player: the player that will go first (if None is passed, a player will be created)
            second_player: the player that will go second (if None is passed, a player will be created)
        """
        self.first_player = first_player or Player(self.FIRST_PLAYER_DEFAULT_CHAR, True)
        self.second_player = second_player or Player(self.SECOND_PLAYER_DEFAULT_CHAR)

        state = ConnectFourState(size, self.first_player, self.second_player)
        super().__init__(state)


class ConnectFourMove(Move):
    """
    Class that represents a move in the dots and boxes game

    Variables:
        column: index of the column to put the token to
    """

    def __init__(self, column) -> None:
        self.column = column
        super().__init__()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ConnectFourMove):
            return False
        return self.column == other.column


class ConnectFourState(State):
    """Class that represents the state of the hex game"""

    def __init__(
            self, size: Tuple[int, int] = None, current_player: Player = None, other_player: Player = None,
            fields: List[List[Player]] = None
    ):
        if fields is not None:
            self.fields = fields
        else:
            cols, rows = size
            self.fields = [[None for _ in range(rows)] for _ in range(cols)]

        super().__init__(current_player, other_player)

    def get_moves(self) -> Iterable[ConnectFourMove]:
        return [ConnectFourMove(i) for i, column in enumerate(self.fields) if column[-1] is None]

    def get_current_player(self) -> Player:
        return self._current_player

    def make_move(self, move: ConnectFourMove) -> 'ConnectFourState':
        assert move in self.get_moves(), "Wrong move"
        new_fields = [list(column) for column in self.fields]
        self._put(new_fields, move)
        return ConnectFourState(current_player=self._other_player, other_player=self._current_player, fields=new_fields)

    def is_finished(self) -> bool:
        return all(map(all, self.fields)) or self.get_winner() is not None

    def get_winner(self) -> Optional[Player]:
        for column_id in range(len(self.fields)):  # verticals
            for start_row_id in range(len(self.fields[column_id]) - 3):
                winner = self._check_four((column_id, start_row_id), (0, 1))
                if winner:
                    return winner

        for start_column_id in range(len(self.fields) - 3):  # horizontals
            for row_id in range(len(self.fields[start_column_id])):
                winner = self._check_four((start_column_id, row_id), (1, 0))
                if winner:
                    return winner

        for start_column_id in range(len(self.fields) - 3):  # diagonals
            for start_row_id in range(len(self.fields[start_column_id]) - 3):
                winner = \
                    self._check_four((start_column_id, start_row_id), (1, 1)) \
                    or self._check_four((start_column_id, start_row_id + 3), (1, -1))
                if winner:
                    return winner

        return None

    def __str__(self) -> str:
        transposed = zip(*self.fields)
        text = '\n'.join(
            reversed([''.join(f'[{" " if field is None else field.char}]' for field in row) for row in transposed])
        )

        return f'Current player: {self._current_player.char}\n{text}'

    def evaluate_payoff_function(self) -> Union[int, float]:
        pf_value = 0
        for column_id in range(len(self.fields)):  # verticals
            for start_row_id in range(len(self.fields[column_id]) - 3):
                pf_value += self._check_four_payoff((column_id, start_row_id), (0, 1))

        for start_column_id in range(len(self.fields) - 3):  # horizontals
            for row_id in range(len(self.fields[start_column_id])):
                pf_value += self._check_four_payoff((start_column_id, row_id), (1, 0))

        for start_column_id in range(len(self.fields) - 3):  # diagonals
            for start_row_id in range(len(self.fields[start_column_id]) - 3):
                pf_value += self._check_four_payoff((start_column_id, start_row_id), (1, 1))
                pf_value += self._check_four_payoff((start_column_id, start_row_id + 3), (1, -1))

        return pf_value

    # below are helper methods for the public interface

    def _put(self, fields: List[List[Player]], move: ConnectFourMove) -> None:
        for i, field in enumerate(fields[move.column]):
            if field is None:
                fields[move.column][i] = self._current_player
                break

    def _check_four(self, start_coords: Tuple[int, int], move_coords: Tuple[int, int]) -> Optional[Player]:
        fields = {
            self.fields[start_coords[0] + move_coords[0] * i][start_coords[1] + move_coords[1] * i] for i in range(4)
        }

        if len(fields) != 1:
            return None

        return next(iter(fields))

    def _check_four_payoff(self, start_coords: Tuple[int, int],
                           move_coords: Tuple[int, int]) -> int:
        who_is_on_fields_list = [self.fields[start_coords[0] + move_coords[0] * i][start_coords[1] + move_coords[1] * i] for i in range(4)]
        fields_dict = {i: who_is_on_fields_list.count(i) for i in who_is_on_fields_list}

        player1 = self.get_players()[0]
        player2 = self.get_players()[1]
        if player1.is_first:
            max_player = player1
            min_player = player2
        else:
            max_player = player2
            min_player = player1

        if max_player in fields_dict and min_player not in fields_dict:
            return fields_dict[max_player]
        elif min_player in fields_dict and max_player not in fields_dict:
            return -fields_dict[min_player]
        else:
            return 0
