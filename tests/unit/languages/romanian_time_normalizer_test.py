import pytest

from normalization.languages.romanian.time_normalizer import RomanianTimeNormalizer


@pytest.fixture
def normalizer() -> RomanianTimeNormalizer:
    return RomanianTimeNormalizer()


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # Half past: formal and informal
        ("la ora opt și jumătate", "la ora 8:30"),
        ("la opt jumate", "la 8:30"),
        ("e opt și jumate", "e 8:30"),
        # Quarter past, including the elided "și-un"
        ("la opt și un sfert", "la 8:15"),
        ("la opt și-un sfert", "la 8:15"),
        # Quarter to and minutes to: the hour before
        ("la opt fără un sfert", "la 7:45"),
        ("la opt fără zece", "la 7:50"),
        ("la unu fără un sfert", "la 12:45"),
        # Minutes after "la"/"ora"
        ("la ora opt și zece", "la ora 8:10"),
        ("la șapte patruzeci și cinci", "la 7:45"),
        ("la ora douăzeci și unu treizeci", "la ora 21:30"),
        # Digits for the hour, and times written with a dot
        ("la 8 jumate", "la 8:30"),
        ("la ora 8.30", "la ora 8:30"),
        # Punctuation after the time is kept
        ("Ne vedem la opt și jumătate.", "Ne vedem la 8:30."),
    ],
)
def test_spoken_times_become_clock_times(
    normalizer: RomanianTimeNormalizer, text: str, expected: str
) -> None:
    assert normalizer(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "mai am trei și jumătate",  # a quantity, no time cue
        "e opt și zece",  # minute numbers only after "la"/"ora"
        "la ora opt",  # an hour alone stays for the number normalizer
        "la ion acasă",
        "am plătit la trei oameni",
        "costă 8.30 lei",  # a dotted number without a time cue
    ],
)
def test_other_phrases_are_left_alone(
    normalizer: RomanianTimeNormalizer, text: str
) -> None:
    assert normalizer(text) == text
