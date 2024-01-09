# pytest-partial-compare

> [!WARNING]
> This is just a proof of concept, do not try to use this

A pytest plugin that lets you partially compare dictionaries and lists.

When you have a complex dictionary and lists and you only care about partially
validating, it can be bothersome to do multiple asserts, one for each value.

By using a `DictSubset` and `ListSubset` you can write the subset of the
dictionary or list that you want to be present, and get clear assertion errors
if there is any values missing or not matching

## DictSubset

```python
# A complex dictionary
def main():
    return {
        "first_name": "John",
        "last_name": "Doe",
        "age": 30,
        "address": {
            "street_address": "1st Street",
            "city": "New York",
            "state": "NY",
            "postal_code": "10000",
        },
        "phone_numbers": [
            {"type": "home", "number": "212 555-1234"},
            {"type": "fax", "number": "646 555-4567"},
        ],
        "spouse": None,
        "children": [],
        "pets": [
            {"type": "dog", "name": "Fido"},
            {"type": "cat", "name": "Felix"},
        ],
    }
```

and you only want to compare few values, it could be done individually like this:

```python
data = main()

assert data["first_name"] == "Jane"
assert data["last_name"] == "Doe"
assert data["children"] == []
pets = data["pets"]
assert len(pets) == 2
assert pets[0]["type"] == "cat"
assert pets[1]["name"] == "Sylvester"
```

which produces the following errors:

```
   data = main()

>  assert data["first_name"] == "Jane"
E  AssertionError: assert 'John' == 'Jane'
E    - Jane
E    + John
```

which works fine, but in this case only shows the first assertion error hit.

Using `DictSubset` from the plugin you can define the subset you want to check
for, like this:

```python
from partial_compare import DictSubset as DS

data = main()

# Assert that data is a superset of the DictSubset
assert data >= DS({
    "first_name": "Jane",
    "last_name": "Doe",
    "children": [],
    "pets": [
        DS({"type": "cat", "name": "Fido"}),
        DS({"name": "Sylvester"}),
    ],
})
```

and with the error output from this specific comparison being:

```
>  assert data >= DS(
       {
           "first_name": "Jane",
           "last_name": "Doe",
           "children": [],
           "pets": [
               DS({"type": "cat", "name": "Fido"}),
               DS({"name": "Sylvester"}),
           ],
       }
   )
E  AssertionError: assert Comparing dict with a sub set:
E      Key `first_name` has different values:
E        John != Jane
E      Key `pets.0.type` has different values:
E        dog != cat
E      Key `pets.1.name` has different values:
E        Felix != Sylvester
```

## ListSubset

A list subset is similary to a dict subset, by checking that the elements are
found in the data being compared, in the same order but not necessarily
consequitive.

For example, you may have a list of events and you just want to validate that
within those events are specific events, in a specific order. If the order
doesn't matter, presence in a set can be used instead.

```python
from partial_compare import ListSubset as LS

data = [1, 2, 3, 4]

# Assert that data is a superset of the DictSubset
assert data >= LS([2, 3])  # passes
assert data >= LS([1, 4])  # passes
assert data >= LS([1, 5])  # fails
```

The last assert produces the following error output:

```
>  assert data >= LS([1, 5])
E  assert List is not a subset
E      List is missing elements:
E        5
```

## Combining DictSubset and ListSubset

You can combine the two types for more complex checks:

```python
assert data >= DS({
    "first_name": "Jane",
    "last_name": "Doe",
    "children": [],
    "pets": LS([
        {"type": "dog", "name": "Fido"},
        DS({"name": "Sylvester"}),  # There's no animal with that name, no matter the type
    ]),
})
```

which produces the following error

```
E  AssertionError: assert Dictionary is not a subset
E      Key `first_name` has different values:
E        John != Jane
E      Key `pets.1.name` has different values:
E        Felix != Sylvester
E      List at key `pets` is missing elements:
E        DictSubset({'name': 'Sylvester'})
```

## Known issues

There are likely heaps of issues with this approach, but here are some of the
ones I'm aware of:

- [ ] Can't use ListSubset inside another list
