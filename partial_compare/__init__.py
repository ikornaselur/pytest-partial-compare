from typing import ClassVar, Iterator, TYPE_CHECKING, Any

if TYPE_CHECKING:
    import _pytest.config

NotPresent = object()


class PartialCompareError(Exception):
    pass


class Subset:
    _internal: ClassVar[bool] = False


class DictSubset(Subset):
    """A dict subset for partial comparison

    Supports only the >= operator, all others will raise an error
    """

    items: dict

    def __init__(self, items: dict):
        self.items = items

    def __le__(self, other):
        if not isinstance(other, dict):
            return False
        return self.items == {k: other[k] for k in self.items if k in other}

    def __eq__(self, other):
        if not self._internal:
            raise PartialCompareError("Usage: data >= DictSubset({...})")
        return self.__le__(other)

    def __lt__(self, other):
        raise PartialCompareError("Usage: data >= DictSubset({...})")

    def __ge__(self, other):
        raise PartialCompareError("Usage: data >= DictSubset({...})")

    def __gt__(self, other):
        raise PartialCompareError("Usage: data >= DictSubset({...})")

    def __getitem__(self, key):
        return self.items[key]

    def __repr__(self):
        return f"DictSubset({repr(self.items)})"


class ListSubset(Subset):
    """A list subset for partial comparison

    Supports only the >= operator, all others will raise an error
    """

    items: list

    def __init__(self, items: list):
        self.items = items

    def __le__(self, other):
        if not isinstance(other, list):
            return False

        o_len, s_len = len(other), len(self)
        if o_len == s_len:
            return other == self.items

        o_idx, s_idx = 0, 0

        while s_idx < s_len:
            if other[o_idx] == self[s_idx]:
                s_idx += 1
            o_idx += 1
            if o_idx == o_len and s_idx < s_len:
                return False

        return True

    def __eq__(self, other):
        if not self._internal:
            raise PartialCompareError("Usage: data >= ListSubset([...])")
        return self.__le__(other)

    def __lt__(self, other):
        raise PartialCompareError("Usage: data >= ListSubset([...])")

    def __ge__(self, other):
        raise PartialCompareError("Usage: data >= ListSubset([...])")

    def __gt__(self, other):
        raise PartialCompareError("Usage: data >= ListSubset([...])")

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, key):
        return self.items[key]

    def __repr__(self):
        return f"ListSubset({repr(self.items)})"


def _compare_lists_subset(
    left: list, right: ListSubset, prefix: str = ""
) -> Iterator[str]:
    """Compare a list with a subset

    The elements in the subset list are expected to be present in the left
    list, in the same order, but can be separated by other elements.

    For example

        [1, 2, 3, 4, 5] <= [1, 4, 5] -> valid
        [1, 2, 3, 4, 5] <= [1, 5, 4] -> invalid
    """
    if (l_len := len(left)) < (r_len := len(right)):
        if not prefix:
            yield f"  List is too short, expected at least {r_len} elements"
        else:
            yield f"  List at key `{prefix[:-1]}` is too short, expected at least {r_len} elements"
        return

    # Compare elements until we reach the end of the subset list
    l_idx, r_idx = 0, 0
    while r_idx < r_len:
        if left[l_idx] == right[r_idx]:
            r_idx += 1
        l_idx += 1
        if l_idx == l_len:
            if not prefix:
                yield f"  List is missing elements:"
            else:
                yield f"  List at key `{prefix[:-1]}` is missing elements:"
            for element in right[r_idx:]:
                yield f"    {element}"
            return


def _compare_lists(left: list, right: list, prefix: str = "") -> Iterator[str]:
    if len(left) != len(right):
        yield f"  List `{prefix[:-1]}` has different lengths: {len(left)} != {len(right)}"
        return
    for i, (left_element, right_element) in enumerate(zip(left, right)):
        if left_element != right_element:
            if isinstance(left_element, dict) and isinstance(right_element, DictSubset):
                yield from _compare_dicts_subset(
                    left_element, right_element, prefix=f"{prefix}{i}."
                )
            elif isinstance(left_element, list) and isinstance(
                right_element, ListSubset
            ):
                yield from _compare_lists_subset(
                    left_element, right_element, prefix=f"{prefix}{i}."
                )
            elif isinstance(left_element, list) and isinstance(right_element, list):
                yield from _compare_lists(
                    left_element, right_element, prefix=f"{prefix}{i}."
                )
            else:
                yield f"  List `{prefix}{i}` has different values:"
                yield f"    {left_element} != {right_element}"


def _compare_dicts_subset(
    left: dict, right: DictSubset, prefix: str = ""
) -> Iterator[str]:
    for key in right.items:
        left_element = left.get(key, NotPresent)
        right_element = right[key]

        if left_element is NotPresent:
            yield f"  Key `{prefix}{key}` not present"
        elif left_element != right_element:
            if isinstance(left_element, list) and isinstance(right_element, list):
                yield from _compare_lists(left_element, right_element, prefix=f"{key}.")
            elif isinstance(left_element, list) and isinstance(
                right_element, ListSubset
            ):
                yield from _compare_lists_subset(
                    left_element, right_element, prefix=f"{key}."
                )
            elif isinstance(left_element, dict) and isinstance(
                right_element, DictSubset
            ):
                yield from _compare_dicts_subset(
                    left_element, right_element, prefix=f"{key}."
                )
            else:
                yield f"  Key `{prefix}{key}` has different values:"
                yield f"    {left_element} != {right_element}"


def pytest_assertrepr_compare(
    config: "_pytest.config.Config",
    op: str,
    left: Any,
    right: Any,
):
    if op != ">=":
        return
    if isinstance(left, dict) and isinstance(right, DictSubset):
        Subset._internal = True
        output = ["Dictionary is not a subset", *_compare_dicts_subset(left, right)]
    elif isinstance(left, list) and isinstance(right, ListSubset):
        Subset._internal = True
        output = ["List is not a subset", *_compare_lists_subset(left, right)]
    else:
        return

    Subset._internal = False
    return output
