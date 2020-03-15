from itertools import product

def comb(n, k):
    """Генерация сочетаний из `n` по `k` без повторений."""

    d = list(range(0, k))
    yield d

    while True:
        i = k - 1
        while i >= 0 and d[i] + k - i + 1 > n:
            i -= 1
        if i < 0:
            return

        d[i] += 1
        for j in range(i + 1, k):
            d[j] = d[j - 1] + 1

        yield d

def comb_sets(sets, m):
    """Генерация сочетаний из элементов множеств `sets` по `m` элементов."""

    for ci in comb(len(sets), m):
        for cj in product(*(sets[i] for i in ci)):
            yield cj

def getAllComb(massiv):
  combi = []
  for h1 in comb_sets(list(map(lambda x: str(x), massiv)), int(len(massiv)/2)):
    h1 = list(map(lambda x: int(x), h1))
    h2 = list(filter(lambda x: (x not in h1), massiv))
    line = []
    line.append(h1)
    line.append(h2)
    combi.append(line)

  return combi