"""Compose hooks callback factory."""


from ._types import Hook, HookContext


def compose_hooks(*hooks: Hook) -> Hook:
    """Run callbacks in order on the same context; exceptions propagate."""
    if not all(callable(hook) for hook in hooks):
        raise TypeError('Every hook must be callable')

    def apply(ctx: HookContext) -> None:
        for hook in hooks:
            hook(ctx)
    return apply
