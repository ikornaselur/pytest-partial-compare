# pytest-partial-compare

A pytest plugin that lets you partially compare dictionaries and lists.

When you have a complex dictionary and you only care about partially
validating, it can be bothersome to do multiple asserts, one for each value.

By using a `DictSubset` you can write the subset of the dictionary that you
want to be present, and get clear assertion errors if there is any values
missing or not matching

## Example

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

assert data == DS({
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
>  assert data == DS(
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
