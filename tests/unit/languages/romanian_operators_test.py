import pytest

from normalization.languages.registry import get_language_registry
from normalization.languages.romanian.operators import RomanianOperators
from normalization.pipeline.loader import load_pipeline


@pytest.fixture
def operators() -> RomanianOperators:
    return RomanianOperators()


def test_romanian_is_registered() -> None:
    assert "ro" in get_language_registry()


def test_romanian_registry_produces_romanian_operators() -> None:
    instance = get_language_registry()["ro"]()
    assert isinstance(instance, RomanianOperators)


def test_config_code(operators: RomanianOperators) -> None:
    assert operators.config.code == "ro"


def test_word_replacements(operators: RomanianOperators) -> None:
    assert operators.get_word_replacements()["okay"] == "ok"


def test_fillers_never_collide_with_words(operators: RomanianOperators) -> None:
    # "ă" and "îî" fold to "a" and "ii", which are real words ("a", "îi").
    assert "a" not in operators.config.filler_words
    assert "ii" not in operators.config.filler_words


def test_expand_written_numbers(operators: RomanianOperators) -> None:
    assert operators.expand_written_numbers("douăzeci și cinci de lei") == "25 de lei"


@pytest.fixture(scope="module")
def pipeline():
    return load_pipeline("gladia-3", language="ro")


def test_diacritics_fold_but_colloquial_spellings_stay_distinct(pipeline) -> None:
    assert (
        pipeline.normalize("Acuma e acum, aicea nu e aici.")
        == "acuma e acum aicea nu e aici"
    )


def test_spoken_and_written_numbers_agree(pipeline) -> None:
    assert pipeline.normalize("25%") == pipeline.normalize("douăzeci și cinci la sută")
    assert pipeline.normalize("Kubiș al treilea") == pipeline.normalize(
        "Kubis al 3-lea"
    )


def test_fillers_are_removed_but_words_that_look_like_fillers_stay(pipeline) -> None:
    assert pipeline.normalize("Ăă, okay, mm, gata.") == "ok gata"
    assert pipeline.normalize("Îi spun ceva.") == "ii spun ceva"
