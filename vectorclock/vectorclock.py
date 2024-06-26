import json
from json import JSONDecodeError
from typing import Dict, Optional, Union


class VectorClock:
    """
    A vector clock is a data structure used for determining the partial
    ordering of events in a distributed system and detecting causality
    violations.

    See https://en.wikipedia.org/wiki/Vector_clock.

    This implements a vector where each process has its own clock.

    A typical description will have the counter start from 1 and increment by
    1 every time there is a change.

    However, this implementation allows the counter increase by whatever the
    client asks for.  Our processes can set the counter to their own clock,
    hence allow us to resolve conflicts (unordered changes) by leaning towards
    later (more recent) object versions.
    """

    def __init__(self, counts: Dict[str, int]) -> None:
        """clocks is a dict mapping clock -> value (numeric value)."""
        self.clocks = counts.copy()

    def set_clock(self, clock: str, value: int) -> None:
        # assert increasing only
        old = self.clocks.get(clock, None)
        if not (old is None or old <= value):
            raise ValueError(f"Can't go backwards from {old} to {value}")
        self.clocks[clock] = value

    def get_clock(self, clock: str, default: Optional[int] = None) -> int:
        return self.clocks.get(clock, default)

    def compare(self, other: "VectorClock", tiebreak: bool) -> Union[int, None]:
        """Compare two clocks.

        :param other:  Vector clock to compare to.
        :param tiebreak:  If True, tiebreak two clocks that are not otherwise ordered
                          in the traditional sense of a vector clock.
        :return: -1 if self < other, 1 if self > other, 0 otherwise.
                 If tiebreak is False, 0 does not mean they are equal,
                 it means they are not ordered.
                 If tiebreak is True, 0 means they are equal.
        """
        all_keys = self.clocks.keys() | other.clocks.keys()

        # if there are keys, and every element in the vector is ==, then ==
        comp = len(all_keys) > 0
        for key in all_keys:
            if not self.clocks.get(key, 0) == other.clocks.get(key, 0):
                comp = False
                break
        if comp:
            return 0

        # if there are keys, and every element in the vector is <=, and at
        # least one is <, then <
        all_le = True
        some_lt = False
        for key in all_keys:
            val = self.clocks.get(key, 0)
            other_val = other.clocks.get(key, 0)
            if not val <= other_val:
                all_le = False
                break
            if val < other_val:
                some_lt = True
        if all_le and some_lt:
            return -1

        # if there are keys, and every element in the vector is >=, and at
        # least one is >, then >
        all_ge = True
        some_gt = False
        for key in all_keys:
            val = self.clocks.get(key, 0)
            other_val = other.clocks.get(key, 0)
            if not val >= other_val:
                all_ge = False
                break
            if val > other_val:
                some_gt = True
        if all_ge and some_gt:
            return 1

        if tiebreak:
            # If it's not <, >, or ==, then we tiebreak
            return self._compare_tiebreak(other)

        return 0

    def _compare_tiebreak(self, other):
        """Tiebreak two clocks even if they are not ordered."""

        # First, tiebreak by picking the highest clock value (to try to lean
        # towards more recency)
        vals1 = self.clocks.values()
        max_clock1 = max(vals1) if vals1 else None
        vals2 = other.clocks.values()
        max_clock2 = max(vals2) if vals2 else None
        if max_clock1 != max_clock2:
            # < is -1, > is 1
            return max_clock1 - max_clock2

        # Still tied.  Tiebreak by json dict.
        sc_str = str(self)
        oc_str = str(other)
        if sc_str < oc_str:
            return -1
        if sc_str > oc_str:
            return 1
        return 0

    # Equality is ambiguous: does it mean "the same" or simply "unordered"?
    # We are going to implement it to mean "the same".
    # So, unordered is not <, >, or ==.
    # We will implement == and !=, but not <= or >=, as that is confusing.

    def __eq__(self, other: "VectorClock") -> bool:
        return self.compare(other, True) == 0

    def __ne__(self, other: "VectorClock") -> bool:
        return self.compare(other, True) != 0

    def __lt__(self, other: "VectorClock") -> bool:
        return self.compare(other, False) < 0

    # def __le__(self, other: "VectorClock") -> bool:
    #     return self.compare(other) != 1

    def __gt__(self, other: "VectorClock") -> bool:
        return self.compare(other, False) > 0

    # def __ge__(self, other: "VectorClock") -> bool:
    #     return self.compare(other) != -1

    def __str__(self) -> str:
        return json.dumps(
            self.clocks,
            # Sorting is not needed, but let's be easy on the eyes
            sort_keys=True,
            # No whitespace: https://stackoverflow.com/a/16311587
            separators=(",", ":"),
        )

    def __repr__(self) -> str:
        return f"VectorClock({self.clocks})"

    @staticmethod
    def from_string(string: str) -> "VectorClock":
        try:
            return VectorClock(json.loads(string))
        except JSONDecodeError as err:
            raise ValueError from err
