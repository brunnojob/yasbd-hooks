"""Shared in-place boundary insertion."""
from collections.abc import Iterable

from ._types import HookContext


def _add(ctx: HookContext, offsets: Iterable[int]) -> None:
    ctx['boundaries'][:] = sorted(set(ctx['boundaries']).union(offsets))
