#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
import logging
from typing import Final, Optional

try:
    from ddtrace import tracer  # type: ignore
except Exception:
    tracer = None  # type: ignore[assignment]

DD_TRACE_ID: Final[str] = "dd.trace_id"
DD_SPAN_ID:  Final[str] = "dd.span_id"
_ZERO: Final[str] = "0"


class DatadogTraceInjectionFilter(logging.Filter):
    """
    Inject Datadog correlation fields into each LogRecord.

    Adds top-level decimal-string fields:
      - dd.trace_id: current trace id or "0"
      - dd.span_id:  current span id or "0"
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # If already populated by another filter or logs injection, keep going.
        if getattr(record, DD_TRACE_ID, None) is not None and getattr(record, DD_SPAN_ID, None) is not None:
            return True

        trace_id: str = _ZERO
        span_id: str = _ZERO

        if tracer is not None:
            span = tracer.current_span()  # type: Optional[object]
            if span is not None:
                tid = getattr(span, "trace_id", None)
                sid = getattr(span, "span_id", None)
                if tid is not None:
                    trace_id = str(tid)
                if sid is not None:
                    span_id = str(sid)

        setattr(record, DD_TRACE_ID, trace_id)
        setattr(record, DD_SPAN_ID, span_id)
        return True
