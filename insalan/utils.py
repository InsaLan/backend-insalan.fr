from collections.abc import Sequence
from typing import Required, TypeAlias, TypedDict

from django_stubs_ext import StrOrPromise


class FieldOpts(TypedDict, total=False):
    fields: Required[Sequence[str | Sequence[str]]]
    classes: Sequence[str]
    description: StrOrPromise


FieldSets: TypeAlias = list[tuple[StrOrPromise | None, FieldOpts]] | tuple[
    tuple[StrOrPromise | None, FieldOpts], ...
] | tuple[()]
