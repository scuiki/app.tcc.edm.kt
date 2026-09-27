# As dez faixas cobrem [0, 1] sem buraco nem faixa a mais.

from __future__ import annotations

import pytest

from api.mastery_dashboard.domain.services.mastery_distribution import mean_and_histogram


def test_the_edges_fall_in_the_right_bins():
    mean, histogram = mean_and_histogram([0.0, 0.09, 0.4, 0.7, 1.0])

    assert histogram == [2, 0, 0, 0, 1, 0, 0, 1, 0, 1]
    assert sum(histogram) == 5
    assert mean == pytest.approx(0.438)


def test_an_empty_list_gives_an_empty_histogram():
    assert mean_and_histogram([]) == (0.0, [0] * 10)
