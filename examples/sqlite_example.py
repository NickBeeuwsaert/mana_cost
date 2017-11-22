#!/usr/bin/env python3
"""Example showing mana_cost with a database

This example registers the functions 'mana_le', 'mana_lt',
'mana_gt', 'mana_ge', 'mana_min', and 'mana_max' with a SQLite3
database for querying.

This example uses a subclass of the `mana_cost.ManaCost` class
that uses a lru cache and reifies the `combinations` method. This
functionality is not included in the base ManaCost class since
users might have different needs for memoizing ManaCost instances.
As an example: If you wanted to use ManaCost from PostgreSQL using
the PL/Python extension, your caching strategy might need to use the
SD or GD objects provided by PostgreSQL.

Additionally, if you were to plug this function into a database,
you should be careful about letting users send potentially malicious
queries. For instance: If a user were to send a query asking for
all cards that match {1/2/3/4/5}{1/2/3/4/5}{1/2/3/4/5}{1/2/3/4/5}, then
your database might take an exceeding long time to complete a query
since it could potentially test 5**4 or 625 different mana variations
against each card.

Example Usage:
# Importing data from the MTGJSJON project:
sqlite_example.py my_database.sqlite3 import AllCards.json

# querying cards
$ sqlite_example.py my_database.sqlite3 \\
> query "SELECT * FROM cards WHERE mana_lt('{50000}', mana_cost)
$ sqlite_example.py my_database.sqlite3 \\
> query "SELECT * FROM cards WHERE mana_lt('{5/W}', mana_cost)
"""
import argparse
import sqlite3
import json
import time
import functools

from mana_cost import ManaCost as ManaCostBase
import mana_cost


class reify:
    """Acts similar to a property, except the result will be
    set as an attribute on the instance instead of recomputed
    each access

    inspired by pyramids `pyramid.decorators.reify` decorator
    """

    def __init__(self, fn):
        self.fn = fn

    def __get__(self, instance, owner):
        if instance is None:
            return self

        fn = self.fn
        val = fn(instance)

        setattr(instance, fn.__name__, val)

        return val


@functools.lru_cache()
class ManaCost(ManaCostBase):
    @reify
    def combinations(self):
        return list(super().combinations)


def import_data(args):
    connection = args.db
    connection.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            name TEXT,
            mana_cost TEXT,
            cmc INT
        );
    ''')

    for card in json.load(args.card_data).values():
        connection.execute(
            'INSERT INTO cards (name, mana_cost, cmc) VALUES(?, ?, ?)',
            (card['name'], card.get('manaCost', ''), card.get('cmc', 0))
        )
    connection.commit()


def query(args):
    connection = args.db

    connection.create_function(
        'mana_eq', 2,
        lambda left, right: ManaCost(left) == ManaCost(right)
    )
    connection.create_function(
        'mana_lt', 2,
        lambda left, right: ManaCost(left) < ManaCost(right)
    )
    connection.create_function(
        'mana_gt', 2,
        lambda left, right: ManaCost(left) > ManaCost(right)
    )
    connection.create_function(
        'mana_le', 2,
        lambda left, right: ManaCost(left) <= ManaCost(right)
    )
    connection.create_function(
        'mana_ge', 2,
        lambda left, right: ManaCost(left) >= ManaCost(right)
    )
    connection.create_function(
        'mana_min', 1,
        lambda arg: ManaCost(arg).min_mana_cost
    )
    connection.create_function(
        'mana_max', 1,
        lambda arg: ManaCost(arg).max_mana_cost
    )

    elapsed = -time.perf_counter()
    cursor = connection.execute(args.query)
    results = cursor.fetchall()
    elapsed += time.perf_counter()
    result_widths = tuple(
        max(len(str(value)) for value in col)
        for col in zip(*results)
    )

    separator = '+{}+'.format(
        "+".join("-"*(width+2) for width in result_widths)
    )

    print(separator)
    for row in results:
        print('| {} |'.format(
            ' | '.join(
                str(data).ljust(width)
                for data, width in zip(row, result_widths)
            )
        ))
        print(separator)
    print(f"Fetched {len(results)} rows in {elapsed:.4} seconds.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument('db', type=sqlite3.connect)
    subparsers = parser.add_subparsers(dest='subcommand')
    subparsers.required = True

    import_parser = subparsers.add_parser('import')
    import_parser.add_argument('card_data', type=argparse.FileType('r'))
    import_parser.set_defaults(func=import_data)

    query_parser = subparsers.add_parser('query')
    query_parser.add_argument('query')
    query_parser.set_defaults(func=query)

    args = parser.parse_args()
    args.func(args)
