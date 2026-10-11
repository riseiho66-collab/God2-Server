"""Local research adapter. No import-time oracle loading or process startup.

After policy checks, load B's ClientCryptoOracle (or an injected test factory).
An instance belongs to one session and uses client-capsule TX/RX directions;
server-direction equivalence must be established before any socket integration.
"""

from collections.abc import Callable, Mapping
from ipaddress import ip_address
from threading import Lock
from typing import Any, Protocol


class Oracle(Protocol):
    def init_session(self, seed: bytes) -> Mapping[str, Any]: ...
    def encrypt(self, state: bytes, data: bytes) -> Mapping[str, Any]: ...
    def decrypt(self, state: bytes, data: bytes) -> Mapping[str, Any]: ...


def _hex_bytes(result: Mapping[str, Any], field: str) -> bytes:
    value = result.get(field)
    if (not isinstance(value, str) or len(value) % 2
            or any(c not in "0123456789abcdefABCDEF" for c in value)):
        raise ValueError(f"Oracle returned invalid {field}")
    return bytes.fromhex(value)


class OracleLabBackend:
    """Default-off adapter; capsule validation remains ClientCryptoOracle's job.

    endpoint is a numeric IP address, without a port or URL. It describes the
    lab endpoint; this adapter does not bind sockets or enforce a listener's IP.
    Runtime exceptions propagate, with no clean/identity fallback.
    """

    def __init__(
        self,
        capsule: Any,
        *,
        oracle_factory: Callable[[Any], Oracle] | None = None,
        endpoint: str = "127.0.0.1",
        lab_mode: bool = False,
        production: bool = True,
    ) -> None:
        if lab_mode is not True or production is not False:
            raise PermissionError("OracleLab requires lab_mode=True and production=False")
        if not isinstance(endpoint, str) or "%" in endpoint:
            raise ValueError("OracleLab endpoint must be a numeric loopback IP")
        try:
            address = ip_address(endpoint)
        except ValueError:
            raise ValueError("OracleLab endpoint must be a numeric loopback IP") from None
        if not address.is_loopback:
            raise PermissionError("OracleLab endpoint must be loopback")
        if oracle_factory is None:
            if __package__:
                from .oracle import ClientCryptoOracle
            else:
                from oracle import ClientCryptoOracle
            oracle_factory = ClientCryptoOracle
        # Factory invocation is deliberately after every policy check.
        self._oracle = oracle_factory(capsule)
        self._lock = Lock()
        self._tx: bytes | None = None
        self._rx: bytes | None = None

    @property
    def tx(self) -> bytes | None:
        with self._lock:
            return self._tx

    @property
    def rx(self) -> bytes | None:
        with self._lock:
            return self._rx

    def init_session(self, seed: bytes) -> None:
        if not isinstance(seed, bytes) or len(seed) != 16:
            raise ValueError("seed must be exactly 16 immutable bytes")
        with self._lock:
            state = _hex_bytes(self._oracle.init_session(seed), "state_after_hex")
            if len(state) != 0x255c:
                raise ValueError("Oracle returned an invalid serialized state size")
            # Immutable values may initially be equal; updates replace one lane only.
            self._tx = state
            self._rx = state

    def encrypt(self, body: bytes) -> bytes:
        return self._transform(body, encrypt=True)

    def decrypt(self, body: bytes) -> bytes:
        return self._transform(body, encrypt=False)

    def _transform(self, body: bytes, *, encrypt: bool) -> bytes:
        if not isinstance(body, bytes):
            raise TypeError("body must be immutable bytes")
        if len(body) > 4096:
            raise ValueError("Raw crypto body exceeds lab backend bounds")
        with self._lock:
            state = self._tx if encrypt else self._rx
            if state is None:
                raise RuntimeError("init_session must succeed before transforming bodies")
            operation = self._oracle.encrypt if encrypt else self._oracle.decrypt
            result = operation(state, body)
            output = _hex_bytes(result, "output_hex")
            next_state = _hex_bytes(result, "state_after_hex")
            if len(next_state) != len(state):
                raise ValueError("Oracle changed the serialized state size")
            if len(output) != len(body):
                raise ValueError("Oracle changed the raw transform length")
            # Commit only after the complete result has passed validation.
            if encrypt:
                self._tx = next_state
            else:
                self._rx = next_state
            return output
