import math

import pytest

from app.embeddings.embedder import (
    EMBED_DIM,
    cosine,
    embed_many,
    embed_text,
)


def _norm(v):
    return math.sqrt(sum(x * x for x in v))


def test_dimension_is_embed_dim():
    assert len(embed_text("attendance policy")) == EMBED_DIM


def test_deterministic_same_input_same_output():
    a = embed_text("Students must maintain 75% attendance")
    b = embed_text("Students must maintain 75% attendance")
    assert a == b


def test_unit_length_when_non_empty():
    v = embed_text("attendance policy")
    assert abs(_norm(v) - 1.0) < 1e-9


def test_empty_string_returns_zero_vector():
    v = embed_text("")
    assert v == [0.0] * EMBED_DIM


def test_none_returns_zero_vector():
    v = embed_text(None)
    assert v == [0.0] * EMBED_DIM


def test_case_and_punctuation_insensitive():
    a = embed_text("Attendance Policy!")
    b = embed_text("attendance policy")
    assert a == b


def test_cosine_identical_vectors_is_one():
    v = embed_text("attendance")
    assert abs(cosine(v, v) - 1.0) < 1e-9


def test_cosine_with_zero_vector_is_zero():
    z = [0.0] * EMBED_DIM
    v = embed_text("attendance")
    assert cosine(z, v) == 0.0


def test_cosine_length_mismatch_raises():
    with pytest.raises(ValueError):
        cosine([1.0, 0.0], [1.0, 0.0, 0.0])


def test_different_text_gives_different_vectors():
    a = embed_text("attendance policy")
    b = embed_text("library hours")
    assert a != b


def test_embed_many_matches_embed_text():
    texts = ["attendance policy", "library hours"]
    many = embed_many(texts)
    assert many == [embed_text(t) for t in texts]
