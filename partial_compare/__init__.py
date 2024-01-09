from typing import Iterator, TYPE_CHECKING, Any

if TYPE_CHECKING:
    import _pytest.config

NotPresent = object()


class DictSubset:
    def __init__(self, items: dict):
        self.items = items

    def __eq__(self, other):
        return self.items == {k: other[k] for k in self.items if k in other}

    def __getitem__(self, key):
        return self.items[key]

    def __repr__(self):
        return f"DictSubset({repr(self.items)})"


def _compare_lists(left: list, right: list, prefix: str = "") -> Iterator[str]:
    if len(left) != len(right):
        yield f"  List `{prefix[:-1]}` has different lengths: {len(left)} != {len(right)}"
        return
    for i, (left_element, right_element) in enumerate(zip(left, right)):
        if left_element != right_element:
            if isinstance(left_element, dict) and isinstance(right_element, DictSubset):
                yield from _compare_values(
                    left_element, right_element, prefix=f"{prefix}{i}."
                )
            elif isinstance(left_element, list) and isinstance(right_element, list):
                yield from _compare_lists(
                    left_element, right_element, prefix=f"{prefix}{i}."
                )
            else:
                yield f"  List `{prefix}{i}` has different values:"
                yield f"    {left_element} != {right_element}"


def _compare_values(left: dict, right: DictSubset, prefix: str = "") -> Iterator[str]:
    for key in right.items:
        left_element = left.get(key, NotPresent)
        right_element = right[key]

        if left_element is NotPresent:
            yield f"  Key `{prefix}{key}` not present"
        elif left_element != right_element:
            if isinstance(left_element, list) and isinstance(right_element, list):
                yield from _compare_lists(
                    left_element, right_element, prefix=f"{key}."
                )
            elif isinstance(left_element, dict) and isinstance(right_element, DictSubset):
                yield from _compare_values(
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
    if not (isinstance(left, dict) and isinstance(right, DictSubset) and op == "=="):
        return

    return ["Comparing dict with a sub set:", *_compare_values(left, right)]
