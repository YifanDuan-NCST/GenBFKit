from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    Iterator,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")
K = TypeVar("K")


class DuplicateKeyError(ValueError):
    pass


class NotFoundError(KeyError):
    pass


def _default_json_serializer(o: Any) -> Any:
    if is_dataclass(o):
        return asdict(o)
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")


def normalize_text(s: Any) -> str:
    if s is None:
        return ""
    s = str(s).strip()
    if s.lower() in {"nan", "none"}:
        return ""
    return s


@dataclass(frozen=True)
class RegistryStats:
    name: str
    count: int


class Registry(Generic[K, T]):
    """
    A small, explicit CRUD registry.
    - Items are keyed by a stable key (K).
    - Items are immutable by default; update() replaces the item.
    """

    def __init__(self, name: str, key_fn: Callable[[T], K]):
        self._name = name
        self._key_fn = key_fn
        self._items: Dict[K, T] = {}

    @property
    def name(self) -> str:
        return self._name

    def stats(self) -> RegistryStats:
        return RegistryStats(name=self._name, count=len(self._items))

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items.values())

    def keys(self) -> List[K]:
        return list(self._items.keys())

    def values(self) -> List[T]:
        return list(self._items.values())

    def items(self) -> List[Tuple[K, T]]:
        return list(self._items.items())

    def exists(self, key: K) -> bool:
        return key in self._items

    def get(self, key: K) -> T:
        try:
            return self._items[key]
        except KeyError as e:
            raise NotFoundError(f"{self._name}: key not found: {key!r}") from e

    def try_get(self, key: K) -> Optional[T]:
        return self._items.get(key)

    def add(self, item: T, *, overwrite: bool = False) -> K:
        key = self._key_fn(item)
        if (not overwrite) and key in self._items:
            raise DuplicateKeyError(f"{self._name}: duplicate key: {key!r}")
        self._items[key] = item
        return key

    def add_many(self, items: Iterable[T], *, overwrite: bool = False) -> int:
        n = 0
        for item in items:
            self.add(item, overwrite=overwrite)
            n += 1
        return n

    def update(self, key: K, new_item: T) -> None:
        if key not in self._items:
            raise NotFoundError(f"{self._name}: key not found: {key!r}")
        new_key = self._key_fn(new_item)
        if new_key != key:
            raise ValueError(f"{self._name}: key mismatch: {key!r} -> {new_key!r}")
        self._items[key] = new_item

    def delete(self, key: K) -> None:
        if key not in self._items:
            raise NotFoundError(f"{self._name}: key not found: {key!r}")
        del self._items[key]

    def clear(self) -> None:
        self._items.clear()

    def find(
        self,
        *,
        predicate: Callable[[T], bool],
        limit: Optional[int] = None,
    ) -> List[T]:
        out: List[T] = []
        for item in self._items.values():
            if predicate(item):
                out.append(item)
                if limit is not None and len(out) >= limit:
                    break
        return out

    def search_text(
        self,
        text: str,
        *,
        fields: Sequence[Callable[[T], str]],
        case_sensitive: bool = False,
        limit: int = 50,
    ) -> List[T]:
        q = normalize_text(text)
        if not q:
            return []
        if not case_sensitive:
            q = q.lower()

        def _match(item: T) -> bool:
            for f in fields:
                v = normalize_text(f(item))
                if not case_sensitive:
                    v = v.lower()
                if q in v:
                    return True
            return False

        return self.find(predicate=_match, limit=limit)

    def to_jsonable(self) -> List[Any]:
        return [asdict(v) if is_dataclass(v) else v for v in self._items.values()]

    def save_json(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"name": self._name, "items": self.to_jsonable()}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_default_json_serializer), encoding="utf-8")
        logger.info("Saved %s (%d items) to %s", self._name, len(self._items), path)


def compact_key(*parts: Any) -> str:
    return " | ".join([normalize_text(p) for p in parts if normalize_text(p)])

