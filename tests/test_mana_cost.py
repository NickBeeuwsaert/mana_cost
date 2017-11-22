import pytest

from mana_cost import ManaCost


@pytest.mark.parametrize(
    ['left', 'right'],
    [
        ('{R}', '{R}'),
        pytest.param('{R}', '{U}', marks=pytest.mark.xfail),
        ('{R/W}', '{R}'),
        ('{R/W}', '{R/W}'),
        ('{R}{R}', '{R}{W/R}')
    ]
)
def test_equal(left, right):
    assert ManaCost(left) == ManaCost(right)


@pytest.mark.parametrize(
    ['left', 'right'],
    [
        ('', '{R}'),
        ('{R}{R}', '{R}{R}{R}'),
        ('{5}{R}', '{6}{R}{R}'),
        ('{R}{R}{G}', '{R}{R}{R}{G}{G}')
    ]
)
def test_less_than_and_greater_than(left, right):
    assert ManaCost(left) < ManaCost(right)
    assert ManaCost(right) > ManaCost(left)


@pytest.mark.parametrize(
    ['left', 'right'],
    [
        ('{5000}', '{1000000}'),
        ('{R}', '{R}'),
        ('{R}{R}', '{R}{R}'),
        ('{5}{R}', '{5}{R}{R}'),
        ('{R}{R}{G}', '{R}{R}{R}{G}')
    ]
)
def test_less_than_or_equal_and_greater_than_or_equal(left, right):
    assert ManaCost(left) <= ManaCost(right)
    assert ManaCost(right) >= ManaCost(left)


@pytest.mark.parametrize(
    ['mana_cost', 'min', 'max'],
    [
        ('{R}', 1, 1),
        ('{R}{R}', 2, 2),
        ('{5}{R}', 6, 6),
        ('{5/R}{W}', 2, 6),
        ('{W/R/G/B/U/10}{W/R/G/B/U/10}', 2, 20)
    ]
)
def test_min_and_max(mana_cost, min, max):
    mana_cost = ManaCost(mana_cost)

    assert mana_cost.min_mana_cost == min
    assert mana_cost.max_mana_cost == max


@pytest.mark.parametrize(
    ['mana_cost', 'num_variations'],
    [
        ('{R}', 1),
        ('{R/R/R}', 1),
        ('{1/2/3/4}', 4),
        ('{1}{1}', 1),
        ('{R/W}{R/W}', 4)
    ]
)
def test_variations(mana_cost, num_variations):
    assert ManaCost(mana_cost).num_variations == num_variations
