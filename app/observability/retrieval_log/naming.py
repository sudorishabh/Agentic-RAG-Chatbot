"""What a query's directory is called.

A trace is worth having only if its file can be found, and a uuid finds nothing:
``query_2ec073092d744bd8ab3cf492079a5147`` tells a reader neither which question
it was nor when it was asked. So the directory is named after the question and
the local time it was asked at::

    tell me about carbon sequestration by seaweed - 2026-08-27 10-51-10 IST

Two constraints shape the exact spelling, and both are Windows':

* ``| < > : " / \\ ? *`` are illegal in a path component. The requested
  ``[query] | [date & time]`` therefore becomes ``[query] - [date time TZ]`` —
  the pipe and the colons are the two characters a Windows path cannot hold.
* A path component is bounded (and the whole path more tightly still), so the
  question is truncated to :data:`MAX_QUESTION_CHARS`.

The name is for reading; the ``request_id`` inside the trace remains the
identifier that correlates events, so nothing depends on the name being unique.
Uniqueness is still guaranteed — see :func:`app.observability.retrieval_log.sink`
— because two identical questions in the same second must not overwrite each
other.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

#: The zone used for the directory layout when the configured one cannot be
#: loaded, and the label put on the folder name. India Standard Time: the
#: deployment and its operators are there, and a log read by a person should be
#: in the reader's own clock rather than UTC.
FALLBACK_OFFSET = timedelta(hours=5, minutes=30)
FALLBACK_LABEL = "IST"

#: Characters no Windows path component may contain, plus the separators. Each
#: is replaced rather than dropped, so two different questions cannot collapse
#: onto one name.
_ILLEGAL = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

#: Runs of whitespace become single spaces: a question typed across two lines is
#: still one question, and a newline cannot go in a file name.
_SPACES = re.compile(r"\s+")

#: How much of the question the name carries. Long enough to recognise the
#: question, short enough that the timestamp and the path around it still fit
#: inside Windows' 260-character limit.
MAX_QUESTION_CHARS = 80

#: Names Windows reserves whatever the extension. A question is very unlikely to
#: slugify to one, and a directory that cannot be created is worth avoiding.
_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def local_zone(name: str | None = None) -> Any:
    """The display timezone: the configured zone, or a fixed +05:30 fallback.

    ``zoneinfo`` needs a timezone database, which Windows does not ship — it
    comes from the ``tzdata`` package. Rather than make a log directory's name
    depend on that being installed, an unloadable zone degrades to the fixed
    offset, which is right for IST (it has no daylight saving) and honest for
    anything else.
    """
    if name is None:
        try:
            from app.config import get_settings

            name = getattr(get_settings(), "retrieval_log_timezone", "") or ""
        except Exception:  # pragma: no cover - unreadable settings
            name = ""
    if name:
        try:
            from zoneinfo import ZoneInfo

            return ZoneInfo(name)
        except Exception:
            logger.debug("Timezone %r unavailable; using the fixed offset.", name,
                         exc_info=True)
    return timezone(FALLBACK_OFFSET, FALLBACK_LABEL)


def local_now(zone: Any = None) -> datetime:
    """Now, in the display timezone."""
    return datetime.now(timezone.utc).astimezone(zone or local_zone())


def zone_label(moment: datetime) -> str:
    """A short zone name for the folder: ``IST``, ``UTC``, else ``+0530``."""
    name = moment.tzname() or ""
    # tzname() gives "IST" where the database has an abbreviation and something
    # like "+0530" where it does not; either is fine in a path, but a name with
    # illegal characters (some zones return "+05:30") is not.
    return _ILLEGAL.sub("", name).strip() or moment.strftime("%z")


def slug(question: str, *, limit: int = MAX_QUESTION_CHARS) -> str:
    """``question`` as a path component: legal, bounded, and still readable.

    Deliberately *not* a conventional slug — no lower-casing, no collapsing to
    hyphens. The point of the name is that a person recognises the question in
    it, and "tell me about carbon sequestration by seaweed" reads better than
    "tell-me-about-carbon-sequestration-by-seaweed".
    """
    text = _SPACES.sub(" ", question or "").strip()
    # A trailing "?" is illegal on Windows and distinguishes nothing — almost
    # every question ends with one — so it is dropped rather than turned into an
    # underscore, which would put "how many reports_" on every folder.
    text = text.rstrip("?!. ").strip()
    text = _ILLEGAL.sub("_", text)
    # Trailing dots and spaces are silently stripped by Windows, which would
    # make the name on disk differ from the name we think we wrote.
    text = text.rstrip(". ").strip()
    if len(text) > limit:
        # ASCII, because this name is read back by shells and editors of every
        # encoding; it sits mid-name, so Windows will not strip it.
        text = text[:limit].rstrip(". ") + "..."
    if not text:
        return "(empty question)"
    if text.split(".")[0].upper() in _RESERVED:
        text = f"_{text}"
    return text


def folder_name(question: str, moment: datetime) -> str:
    """The directory name for one query: the question, then when it was asked.

    ``tell me about carbon sequestration by seaweed - 2026-08-27 10-51-10 IST``
    """
    stamp = moment.strftime("%Y-%m-%d %H-%M-%S")
    label = zone_label(moment)
    return f"{slug(question)} - {stamp}{f' {label}' if label else ''}"


def day(moment: datetime) -> str:
    """The date directory a query belongs to, in the display timezone.

    Local rather than UTC so that the day folder and the timestamp in the query
    folder's own name agree — a query at 02:00 IST otherwise filed itself under
    the previous day while naming itself with today's date.
    """
    return moment.strftime("%Y-%m-%d")
