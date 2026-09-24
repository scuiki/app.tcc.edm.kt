# summarize_cleaned_submissions deriva as 4 contagens de visão geral sobre o stream canônico.

from __future__ import annotations

from api.classroom_import.domain.services.import_summary import summarize_cleaned_submissions


def test_build_summary_a439_mini(a439_mini):
    s = summarize_cleaned_submissions(a439_mini)

    assert s["n_students"] == 3  # S1, S2, S_long
    assert s["n_assignments"] == 1  # tudo no A439
    assert s["n_problems"] == 3  # problemas 1, 2, 3
    assert s["n_submissions"] == len(a439_mini)

