#!/usr/bin/env python3
import re
from itertools import product
from functools import reduce, total_ordering
import collections
import operator


__all__ = [
    'ManaCost',
]

base_mana_re = r'(?:[RUBGWCPX]|\d+)'
mana_list_re = re.compile(r'\{{({base_mana_re}(?:/{base_mana_re})*)\}}'.format(
    base_mana_re=base_mana_re
))


class ComparableCounter(collections.Counter):
    def __lt__(self, rhs):
        return all(v < rhs[k] for k, v in self.items())

    def __le__(self, rhs):
        return all(v <= rhs[k] for k, v in self.items())


@total_ordering
class ManaCost:
    def __init__(self, mana_cost):
        self._mana_cost = mana_cost
        self._parsed_mana = [
            list(set(mana.split('/')))
            for mana in mana_list_re.findall(mana_cost)
        ]

    def __repr__(self):
        return self._mana_cost

    @property
    def num_variations(self):
        return reduce(operator.mul, map(len, self._parsed_mana))

    @property
    def min_mana_cost(self):
        return sum(
            min(
                int(variation) if variation.isdigit() else 1
                for variation in mana
                # Skip 'P' and 'X' variations since they are not actually mana
                # although `combinations` treats them like mana
                # for the purposes of searching
                if variation not in ('P', 'X')
            )
            for mana in self._parsed_mana
        )

    @property
    def max_mana_cost(self):
        return sum(
            max(
                int(variation) if variation.isdigit() else 1
                for variation in mana
                if variation not in ('P', 'X')
            )
            for mana in self._parsed_mana
        )

    @property
    def combinations(self):
        for mana_combo in product(*self._parsed_mana):
            counter = ComparableCounter()

            for mana in mana_combo:
                try:
                    counter['GENERIC'] += int(mana)
                except ValueError:
                    counter[mana] += 1

            # Don't remove phyrexian mana and 'X' mana,
            # even though they aren't mana, since it's useful
            # to search for cards that contain phyrexian mana or just 'X' mana
            # counter.pop('P', None)
            # counter.pop('X', None)

            yield counter

    def __eq__(self, rhs):
        return any(
            left == right
            for left in self.combinations
            for right in rhs.combinations
        )

    def __lt__(self, rhs):
        return any(
            left < right
            for left in self.combinations
            for right in rhs.combinations
        )

    def __le__(self, rhs):
        return any(
            left <= right
            for left in self.combinations
            for right in rhs.combinations
        )
