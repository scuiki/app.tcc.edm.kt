"""A taxa de parse do javalang: as quatro classes de snapshot e o denominador sem os sem-código."""

from __future__ import annotations

import pytest

from api.model_training.infrastructure.implementations import java_parse_rate


def test_classify_parse_three_way(java_snippets, cache_config):
    assert java_parse_rate.classify_parse(java_snippets.bad, cache_config) == "parse_failed"
    assert java_parse_rate.classify_parse(java_snippets.ok_a, cache_config) == "com_paths"
    assert java_parse_rate.classify_parse("   ", cache_config) == "no_code"
    assert java_parse_rate.classify_parse(java_snippets.empty_class, cache_config) == "parsed_sem_paths"


def test_parse_rate_excludes_no_code_from_denominator(cache_code_states, cache_config):
    # c_ok1/c_ok2=com_paths, c_empty=parsed_sem_paths, c_bad=parse_failed, c_blank=no_code.
    rate = java_parse_rate.compute_java_parse_rate(list(cache_code_states.values()), cache_config)
    # denominator = 4 (excludes c_blank); numerator = com_paths + parsed_sem_paths = 3.
    assert rate == pytest.approx(3 / 4)


# --- no-leak invariant: train-only vocab still OOV on held-out ----
