"""
Retry-with-backoff exponencial para llamadas a la API de Anthropic.

Decisión deliberada: NO se reintenta en errores 4xx (request inválido,
permission, not_found). Solo reintentamos en 429 (rate_limit),
5xx (api_error, overloaded_error) y errores de red.

Uso:
    from lib.retry import retry_api

    @retry_api(max_attempts=4)
    def crear_agente(client, ...):
        return client.beta.agents.create(...)
"""
from __future__ import annotations
import functools
import logging
import random
import time
from typing import Any, Callable, TypeVar

import anthropic
import httpx

LOG = logging.getLogger("retry")

F = TypeVar("F", bound=Callable[..., Any])

# Errores que MERECEN reintento
_RETRYABLE_HTTP_STATUS = {408, 429, 500, 502, 503, 504, 529}
_RETRYABLE_API_TYPES = {"rate_limit_error", "api_error", "overloaded_error"}


def _es_reintentable(exc: BaseException) -> bool:
    """Determina si una excepción justifica reintento."""
    # Errores de red
    if isinstance(exc, (httpx.ConnectError, httpx.ReadTimeout,
                         httpx.WriteTimeout, httpx.PoolTimeout,
                         httpx.RemoteProtocolError)):
        return True

    # Errores del SDK Anthropic
    if isinstance(exc, anthropic.RateLimitError):
        return True
    if isinstance(exc, anthropic.InternalServerError):
        return True
    if isinstance(exc, anthropic.APIConnectionError):
        return True
    if isinstance(exc, anthropic.APITimeoutError):
        return True
    if isinstance(exc, anthropic.APIStatusError):
        if getattr(exc, "status_code", None) in _RETRYABLE_HTTP_STATUS:
            return True
        # Inspeccionar tipo de error si lo expone
        body = getattr(exc, "body", None)
        if isinstance(body, dict):
            err = body.get("error") or {}
            if err.get("type") in _RETRYABLE_API_TYPES:
                return True

    return False


def retry_api(
    *,
    max_attempts: int = 4,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter: float = 0.25,
) -> Callable[[F], F]:
    """Decorador que aplica retry-with-backoff exponencial.

    Args:
        max_attempts: número máximo de intentos (incluye el primero).
            4 por defecto = primer intento + 3 reintentos.
        base_delay: segundos de espera base entre reintentos.
        max_delay: tope superior de la espera (segundos).
        jitter: fracción de jitter aleatorio para evitar tormentas.

    NO reintenta errores 4xx (excepto 408/429): un BadRequestError
    significa que el código está mal, no que la red sea inestable.
    """
    def decorador(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            ultimo_error: BaseException | None = None
            for intento in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except BaseException as exc:
                    if not _es_reintentable(exc):
                        # Error no transitorio: no reintentamos
                        raise
                    ultimo_error = exc
                    if intento >= max_attempts:
                        break
                    espera = min(
                        base_delay * (2 ** (intento - 1)),
                        max_delay,
                    )
                    espera *= 1 + random.uniform(-jitter, jitter)
                    LOG.warning(
                        "retry %s/%s tras error transitorio (%s): "
                        "esperando %.1fs antes de reintentar",
                        intento, max_attempts, type(exc).__name__, espera,
                    )
                    time.sleep(espera)
            assert ultimo_error is not None
            raise ultimo_error
        return wrapper  # type: ignore[return-value]
    return decorador
