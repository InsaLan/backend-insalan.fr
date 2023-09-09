# Deletion Cascades

The following behaviours are enforced:
 - Deleting a `User` deletes its:
    - `Player`
    - `Manager`
 - Deleting an `Event` deletes:
    - `Tournament`s that refer to it
 - Deleting a `Game` deletes:
    - `Tournaments` that refer to it
 - Deleting a `Tournament`:
    - sets the `.tournament` field of all `Team`s on it to `None`
 - Deleting a `Team` deletes:
    - `Player`s on it
    - `Manager`s on it
 - Deleting a `Tree` deletes:
    - `Match`es on it
