__all__ = ["Json", "ArangoMetagraph", "NxId", "NxData"]

from typing import Any, Dict, Set, Tuple, Union

Json = Dict[str, Any]
ArangoMetagraph = Dict[str, Dict[str, Set[str]]]

NxId = Union[int, float, bool, str, Tuple[Any, ...]]
NxData = Dict[Any, Any]
