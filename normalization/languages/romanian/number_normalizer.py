"""Romanian number normalizer (STT-oriented).

``text2num.alpha2digit`` does not support Romanian, so this module parses spelled-out
cardinals for the patterns found in transcripts:

- units, teens and tens, including the colloquial contracted teens (``cinșpe`` = 15,
  ``șaișpe`` = 16) and tens (``douăj`` = 20);
- ``X zeci și Y`` compounds (``douăzeci și cinci`` = 25);
- hundreds (``trei sute``), and the multipliers ``mie``/``mii``, ``milion``/``milioane``,
  ``miliard``/``miliarde``, with the ``de`` Romanian puts between a number from 20 up and
  its multiplier (``douăzeci de mii`` = 20000);
- ``un``/``o`` count as 1 only before ``sută``/``mie``/``milion``/``miliard``, so articles
  (``o zi``, ``un om``) stay words;
- ordinals after ``al``/``a`` (``al treilea`` = ``al 3``) and digit ordinals (``al 3-lea``,
  ``a 3-a`` → ``al 3``, ``a 3``).

A number phrase never runs across punctuation, and a unit directly after a unit starts a new
number (``doi trei`` → ``2 3``). Words are matched with and without diacritics, and the
legacy cedilla letters ş/ţ are read as ș/ț.
"""

from __future__ import annotations

import re

_UNITS: dict[str, int] = {
    "zero": 0,
    "unu": 1,
    "una": 1,
    "doi": 2,
    "două": 2,
    "doua": 2,
    "trei": 3,
    "patru": 4,
    "cinci": 5,
    "șase": 6,
    "sase": 6,
    "șapte": 7,
    "sapte": 7,
    "opt": 8,
    "nouă": 9,
    "noua": 9,
}

_TEENS: dict[str, int] = {
    "zece": 10,
    "unsprezece": 11,
    "unșpe": 11,
    "unspe": 11,
    "doisprezece": 12,
    "douăsprezece": 12,
    "douasprezece": 12,
    "doișpe": 12,
    "doispe": 12,
    "treisprezece": 13,
    "treișpe": 13,
    "treispe": 13,
    "paisprezece": 14,
    "paișpe": 14,
    "paispe": 14,
    "cincisprezece": 15,
    "cinșpe": 15,
    "cinspe": 15,
    "șaisprezece": 16,
    "saisprezece": 16,
    "șaișpe": 16,
    "saispe": 16,
    "șaptesprezece": 17,
    "saptesprezece": 17,
    "șaptișpe": 17,
    "saptispe": 17,
    "optsprezece": 18,
    "optișpe": 18,
    "optispe": 18,
    "nouăsprezece": 19,
    "nouasprezece": 19,
    "nouășpe": 19,
    "nouaspe": 19,
}

_TENS: dict[str, int] = {
    "douăzeci": 20,
    "douazeci": 20,
    "douăj": 20,  # colloquial
    "douaj": 20,
    "treizeci": 30,
    "treij": 30,
    "patruzeci": 40,
    "patruj": 40,
    "cincizeci": 50,
    "cinzeci": 50,
    "șaizeci": 60,
    "saizeci": 60,
    "șaptezeci": 70,
    "saptezeci": 70,
    "optzeci": 80,
    "nouăzeci": 90,
    "nouazeci": 90,
}

_HUNDRED: dict[str, int] = {"sută": 100, "suta": 100, "sute": 100}

_LARGE: dict[str, int] = {
    "mie": 1_000,
    "mii": 1_000,
    "milion": 1_000_000,
    "milioane": 1_000_000,
    "miliard": 1_000_000_000,
    "miliarde": 1_000_000_000,
}

_ARTICLES = {"un", "o"}

_ORDINALS: dict[str, str] = {
    "doilea": "2",
    "treilea": "3",
    "patrulea": "4",
    "cincilea": "5",
    "șaselea": "6",
    "saselea": "6",
    "șaptelea": "7",
    "saptelea": "7",
    "optulea": "8",
    "nouălea": "9",
    "noualea": "9",
    "zecelea": "10",
    "treia": "3",
    "patra": "4",
    "cincea": "5",
    "șasea": "6",
    "sasea": "6",
    "șaptea": "7",
    "saptea": "7",
    "zecea": "10",
}

NUMBER_WORDS: list[str] = [*_UNITS, *_TEENS, *_TENS, *_HUNDRED, *_LARGE]
"""Every cardinal word the normalizer understands (for ``LanguageConfig.number_words``)."""

_TOKEN = re.compile(r"(\S+)")
_EDGE = re.compile(r"^([^\w]*)(.*?)([^\w]*)$", re.UNICODE)
_DIGIT_ORDINAL = re.compile(r"\b(\d+)-(?:lea|a)\b", re.IGNORECASE)
_CEDILLA = str.maketrans("şţŞŢ", "șțȘȚ")


def _fold(word: str) -> str:
    return word.translate(_CEDILLA).casefold()


class RomanianNumberNormalizer:
    """Replace spelled-out Romanian numbers with digits, keeping surrounding punctuation."""

    def __call__(self, text: str) -> str:
        text = _DIGIT_ORDINAL.sub(r"\1", text)
        tokens = _TOKEN.findall(text)
        if not tokens:
            return text
        parts = [_EDGE.match(token).groups() for token in tokens]  # type: ignore[union-attr]
        cores = [_fold(core) for _, core, _ in parts]
        output: list[str] = []
        i = 0
        while i < len(tokens):
            lead, _, trail = parts[i]
            if cores[i] in _ORDINALS and i > 0 and cores[i - 1] in ("al", "a"):
                output.append(f"{lead}{_ORDINALS[cores[i]]}{trail}")
                i += 1
                continue
            # A number phrase may not run across punctuation between its words.
            limit = i + 1
            while (
                limit < len(tokens) and not parts[limit - 1][2] and not parts[limit][0]
            ):
                limit += 1
            parsed = self._parse(cores[i:limit])
            if parsed:
                value, length = parsed
                output.append(f"{lead}{value}{parts[i + length - 1][2]}")
                i += length
            else:
                output.append(tokens[i])
                i += 1
        return " ".join(output)

    @staticmethod
    def _kind(word: str, following: str | None) -> tuple[str, int] | None:
        if word in _UNITS:
            return "unit", _UNITS[word]
        if word in _TEENS:
            return "teen", _TEENS[word]
        if word in _TENS:
            return "ten", _TENS[word]
        if word in _HUNDRED:
            return "hundred", 100
        if word in _LARGE:
            return "large", _LARGE[word]
        if word in _ARTICLES and following in (*_HUNDRED, *_LARGE):
            return "unit", 1
        return None

    def _parse(self, words: list[str]) -> tuple[int, int] | None:
        """Longest well-formed number phrase at the start of ``words``: (value, words used).

        Grammar: ``[unit sute] [ten [și unit] | teen | unit]`` with the large multipliers,
        ``de`` before a multiplier from 20 up, and ``o``/``un`` as 1 only before a hundred or a
        multiplier.
        """
        total = current = 0
        previous: str | None = None
        used = i = 0
        while i < len(words):
            word = words[i]
            following = words[i + 1] if i + 1 < len(words) else None
            if word in ("și", "si"):
                if (
                    previous == "ten"
                    and following is not None
                    and _UNITS.get(following, 0) > 0
                ):
                    previous, i = "și", i + 1
                    continue
                break
            if word == "de":
                if current >= 20 and following in _LARGE:
                    i += 1
                    continue
                break
            kind = self._kind(word, following)
            if kind is None:
                break
            name, number = kind
            after = (
                (None, "și", "hundred", "large")
                if name == "unit"
                else (None, "hundred", "large")
            )
            if name in ("unit", "teen", "ten") and previous in after:
                current += number
            elif name == "hundred" and previous == "unit" and 0 < current < 10:
                current *= 100
            elif name == "large" and previous not in (None, "large") and current > 0:
                total, current = total + current * number, 0
            else:
                break
            previous, i = name, i + 1
            used = i
        return (total + current, used) if used else None
