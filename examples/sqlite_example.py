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
import io

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


def _print_results(cursor):
    columns = [
        name
        for name, *_ in cursor.description
    ]
    column_widths = [len(column_name) for column_name in columns]
    rows = cursor.fetchall()
    row_widths = [
        max(len(str(cell)) for cell in column)
        for column in zip(*rows)
    ]

    widths = [max(pair) for pair in zip(column_widths, row_widths)]

    row_separator = '+-{}-+'.format(
        '-+-'.join('-'*width for width in widths)
    )
    header_separator = '+={}=+'.format(
        '=+='.join('='*width for width in widths)
    )

    def format_row(row):
        return '| {} |'.format(
            ' | '.join(
                str(cell).ljust(width) for cell, width in zip(row, widths)
            )
        )

    print(header_separator)
    print(format_row(columns))
    print(header_separator)

    for row in rows:
        print(format_row(row))
        print(row_separator)

    print('Fetched {} row(s) in {:.4f}s'.format(len(rows), cursor.timing))


def timed(fn):
    @functools.wraps(fn)
    def wrapped(cursor, *args, **kwargs):
        elapsed = -time.perf_counter()
        try:
            return fn(cursor, *args, **kwargs)
        finally:
            elapsed += time.perf_counter()
            cursor.timing = elapsed

    return wrapped


class TimedCursor(sqlite3.Cursor):
    execute = timed(sqlite3.Cursor.execute)
    executemany = timed(sqlite3.Cursor.executemany)
    executescript = timed(sqlite3.Cursor.executescript)


class InteractiveConsole:
    def __init__(self, connection):
        self._connection = connection
        self.buffer = io.StringIO()

    def resetbuffer(self):
        self.buffer.seek(0, io.SEEK_SET)
        self.buffer.truncate(0)

    def run(self, command):
        if not sqlite3.complete_statement(command):
            return True

        cursor = self._connection.cursor(TimedCursor)
        try:
            cursor.execute(command)

        # According to PEP-0249 and the python sqlite3 module documentation
        # Things like syntax errors should be a ProgrammingError
        # But for whatever reason, sqlite3 raises a OperationalError for
        # syntax errors
        except (sqlite3.OperationalError, sqlite3.ProgrammingError) as e:
            # Just show the error to the user
            print(e)
        else:
            if cursor.description:
                _print_results(cursor)
        finally:
            cursor.close()

        return False

    def interact(self, banner=None):
        more = False

        if banner is not None:
            print(banner)

        while True:
            prompt = "sqlite> " if not more else "   ...> "

            try:
                line = input(prompt)
            except EOFError:
                print('')
                if more:
                    more = False
                    self.resetbuffer()
                    print("Press again to exit")
                else:
                    break
            else:
                more = self.push(line)

    def push(self, line):
        self.buffer.write(line + '\n')

        more = self.run(self.buffer.getvalue())

        if not more:
            self.resetbuffer()

        return more


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

    if args.query is None:
        try:
            import readline
        except ImportError:
            # Readline support couldnt be enabled
            pass
        repl = InteractiveConsole(connection)
        repl.interact('{}\n\nCtrl+D to exit'.format(__doc__))
    else:
        cursor = connection.cursor(TimedCursor)
        cursor.execute(args.query)
        if cursor.description:
            _print_results(cursor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument('db', type=sqlite3.connect)
    subparsers = parser.add_subparsers(dest='subcommand')
    subparsers.required = True

    import_parser = subparsers.add_parser('import')
    import_parser.add_argument('card_data', type=argparse.FileType('r'))
    import_parser.set_defaults(func=import_data)

    query_parser = subparsers.add_parser('query')
    query_parser.add_argument(
        'query',
        nargs='?',
        help="Query to execute, if empty a interactive session will be created"
    )
    query_parser.set_defaults(func=query)

    args = parser.parse_args()
    args.func(args)
