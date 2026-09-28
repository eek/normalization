"""Romanian spoken and dotted clock times to H:MM.

Romanian says times with words, usually after ``la``, ``ora`` or ``e``:

- ``la opt și jumătate``, ``la opt jumate`` → ``la 8:30``
- ``la opt și un sfert``, ``la opt și-un sfert`` → ``la 8:15``
- ``la opt fără un sfert`` → ``la 7:45``; ``la opt fără zece`` → ``la 7:50``
- ``la ora opt și zece`` → ``la ora 8:10``; ``la șapte patruzeci și cinci`` → ``la 7:45``
- ``la ora 8.30`` (written with a dot) → ``la ora 8:30``

This runs before the time-colon protection, so the result is kept exactly like a written
``8:30``. Only phrases right after ``la``/``ora``/``e`` are read as times, and plain minute
numbers (``opt zece``, ``opt și zece``) only after ``la``/``ora``, so quantities such as
``trei și jumătate`` are left to the number normalizer (``3,5``). Whether ``opt și
jumătate`` means 8:30 or 20:30 cannot be told from the words; it becomes 8:30.
"""

from __future__ import annotations

import re

from normalization.languages.romanian.number_normalizer import RomanianNumberNormalizer

_CUES = {"la", "ora", "e"}
_MINUTE_CUES = {"la", "ora"}
_AND = {"și", "si"}
_WITHOUT = {"fără", "fara"}
_HALF = {"jumătate", "jumatate", "jumate"}
_QUARTER = "sfert"
_AND_A = {"și-un", "si-un"}
_ROUND_MINUTES = {5, 10, 20, 25}

_TOKEN = re.compile(r"(\S+)")
_EDGE = re.compile(r"^([^\w]*)(.*?)([^\w-]*)$", re.UNICODE)
_DOTTED = re.compile(r"\b(la|ora)\s+(\d{1,2})\.([0-5]\d)\b", re.IGNORECASE)
_CEDILLA = str.maketrans("şţŞŢ", "șțȘȚ")


class RomanianTimeNormalizer:
    def __init__(self) -> None:
        self._numbers = RomanianNumberNormalizer()

    def __call__(self, text: str) -> str:
        text = _DOTTED.sub(
            lambda m: (
                f"{m.group(1)} {int(m.group(2))}:{m.group(3)}"
                if int(m.group(2)) <= 24
                else m.group(0)
            ),
            text,
        )
        tokens = _TOKEN.findall(text)
        parts = [_EDGE.match(token).groups() for token in tokens]  # type: ignore[union-attr]
        words = [core.translate(_CEDILLA).casefold() for _, core, _ in parts]
        output: list[str] = []
        i = 0
        while i < len(tokens):
            output.append(tokens[i])
            if words[i] in _CUES and not parts[i][2] and i + 1 < len(tokens):
                end = i + 1
                while (
                    end < len(tokens)
                    and not parts[end][0]
                    and (end == i + 1 or not parts[end - 1][2])
                ):
                    end += 1
                found = self._time(words[i + 1 : end], words[i] in _MINUTE_CUES)
                if found:
                    hour, minute, used = found
                    output.append(f"{hour}:{minute:02d}{parts[i + used][2]}")
                    i += used + 1
                    continue
            i += 1
        return " ".join(output)

    def _number(self, words: list[str]) -> tuple[int, int] | None:
        if words and words[0].isdigit():
            return int(words[0]), 1
        return self._numbers.parse(words)

    def _time(self, words: list[str], minute_cue: bool) -> tuple[int, int, int] | None:
        """(hour, minute, words used) for a time phrase at the start of ``words``."""
        parsed = self._number(words)
        if parsed is None or not 0 <= parsed[0] <= 24:
            return None
        hour, j = parsed
        rest = words[j:]

        def at(k: int) -> str:
            return rest[k] if k < len(rest) else ""

        if at(0) in _HALF:
            return hour, 30, j + 1
        if at(0) in _AND and at(1) in _HALF:
            return hour, 30, j + 2
        if at(0) in _AND_A and at(1) == _QUARTER:
            return hour, 15, j + 2
        if at(0) in _AND and at(1) == _QUARTER:
            return hour, 15, j + 2
        if at(0) in _AND and at(1) == "un" and at(2) == _QUARTER:
            return hour, 15, j + 3
        if at(0) in _WITHOUT:
            before = (hour - 1) % 24 or (12 if hour == 1 else 0)
            if at(1) == "un" and at(2) == _QUARTER:
                return before, 45, j + 3
            if at(1) == _QUARTER:
                return before, 45, j + 2
            minutes = self._number(rest[1:])
            if minutes and minutes[0] in _ROUND_MINUTES:
                return before, 60 - minutes[0], j + 1 + minutes[1]
            return None
        if not minute_cue:
            return None
        if at(0) in _AND:
            minutes = self._number(rest[1:])
            if minutes and minutes[0] in _ROUND_MINUTES:
                return hour, minutes[0], j + 1 + minutes[1]
            return None
        minutes = self._number(rest)
        if minutes and 10 <= minutes[0] <= 59 and not rest[0].isdigit():
            return hour, minutes[0], j + minutes[1]
        return None
