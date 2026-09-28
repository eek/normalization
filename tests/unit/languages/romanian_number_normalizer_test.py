import pytest

from normalization.languages.romanian.number_normalizer import RomanianNumberNormalizer


@pytest.fixture
def normalizer() -> RomanianNumberNormalizer:
    return RomanianNumberNormalizer()


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # Units, teens, tens
        ("zero", "0"),
        ("nouă", "9"),
        ("zece", "10"),
        ("unsprezece", "11"),
        ("nouăsprezece", "19"),
        ("douăzeci", "20"),
        ("nouăzeci", "90"),
        # Colloquial contracted forms
        ("cinșpe", "15"),
        ("șaișpe", "16"),
        ("douăj", "20"),
        # Compounds with "și"
        ("douăzeci și cinci", "25"),
        ("nouăzeci și nouă", "99"),
        # Hundreds
        ("o sută", "100"),
        ("trei sute cincizeci și doi", "352"),
        # Multipliers, with the "de" used from 20 up
        ("o mie", "1000"),
        ("două mii", "2000"),
        ("douăzeci de mii", "20000"),
        ("o sută de mii", "100000"),
        ("două milioane cinci sute de mii", "2500000"),
        ("un miliard", "1000000000"),
        # Without diacritics, and with the legacy cedilla letters
        ("douazeci si cinci", "25"),
        ("şase", "6"),
        ("şaptezeci", "70"),
        # Numbers inside sentences keep their surroundings
        ("douăzeci și cinci de lei", "25 de lei"),
        ("am plătit trei sute de lei", "am plătit 300 de lei"),
        # Punctuation and a unit after a unit start new numbers
        ("zece, unsprezece", "10, 11"),
        ("doi trei oameni", "2 3 oameni"),
        # Ordinals after "al"/"a", spelled or with digits
        ("al treilea", "al 3"),
        ("a patra", "a 4"),
        ("al 3-lea", "al 3"),
        ("a 3-a", "a 3"),
    ],
)
def test_spelled_numbers_become_digits(
    normalizer: RomanianNumberNormalizer, text: str, expected: str
) -> None:
    assert normalizer(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "un om",  # article, not a number
        "o zi",
        "am o casă",
        "mii de oameni",  # bare multiplier
        "și ea",
        "treilea",  # ordinal without "al"/"a"
    ],
)
def test_articles_and_bare_words_stay_words(
    normalizer: RomanianNumberNormalizer, text: str
) -> None:
    assert normalizer(text) == text


def test_empty_text(normalizer: RomanianNumberNormalizer) -> None:
    assert normalizer("") == ""
