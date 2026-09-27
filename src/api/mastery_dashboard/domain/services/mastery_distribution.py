# A distribuição em dez faixas de 10 pontos, para o professor ler a forma e não um rótulo.

from __future__ import annotations

HISTOGRAM_BINS = 10


def mean_and_histogram(values: list[float]) -> tuple[float, list[int]]:
    # Devolve (média, contagem por faixa); 1,0 cai na última faixa, não numa décima primeira.
    histogram = [0] * HISTOGRAM_BINS
    for value in values:
        histogram[min(int(value * HISTOGRAM_BINS), HISTOGRAM_BINS - 1)] += 1
    mean = sum(values) / len(values) if values else 0.0
    return mean, histogram
