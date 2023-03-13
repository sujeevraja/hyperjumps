#!/usr/bin/env python

import itertools
import logging
import networkx as nx
import typing

log = logging.getLogger(__name__)


def get_digits(x: int, y: int) -> typing.Generator[int, None, None]:
    """Return ones digits of x <> y where <> refers to +,-,*,/.

    Note that "-" applies only if x>y and "/" applies if y divides x.
    """
    yield (x+y) % 10
    yield (x*y) % 10
    if x > y:
        yield (x-y) % 10

    # Division could end up being the hardest search for the following reason.
    # Say we know that y does not divide x. But by prefixing x with a digit
    # a, y could divide the 2-digit number ax and we cannot know this apriori.
    # Similarly, say we prefix x with 2 more digits and make it "bax". We could
    # now check for y dividing bax or xy dividing ba. The combinations start
    # increasing in this case.
    if x % y == 0:
        yield (x // y) % 10


def run(planet_nums: typing.List[int], jump_length: int):
    """
    Create a sequence of single-digit numbers with the following rules:
    - The first 2 elements of the sequence should be from `planet_nums`.
    - The sequence should end with 9.
    - The length of the sequence should be `jump_length`.
    - Starting from the third element, each number should be the ones digit of
        adding, subtracting, multiplying or dividing the previous 2 numbers.
    - Consider a sequence like a_1, a_2, a_3, ... a_k in which a_i is a single
        digit. a_{k+1} can be generated as the ones digit of a_{k-1} <> a_k
        where <> can be any of (add, subtract, multiply or divide).
    - a_{k+1} can also be generated as b <> c where b and c are formed by
        selecting a continuous subsequence starting at a_m for 1 <= m < k
        partitining it into (a_m,...,a_n), (a_{n+1},...,a_k) and concatenating
        these 2 sub-sequences to create the multi-digit numbers b and c.
    """
    log.info(f"planet numbers: {planet_nums}")
    log.info(f"sequence length {jump_length}")

    # Build jump graph with only single-digit numbers.
    g = nx.DiGraph()
    for x, y in itertools.permutations(planet_nums, 2):
        for d in get_digits(x, y):
            if d in planet_nums or d == 9:
                if not g.has_edge(x, y):
                    g.add_edge(x, y)
                if not g.has_edge(y, d):
                    g.add_edge(y, d)
                    log.info(f"added edge {x} -> {y} -> {d}")

    nodes = list(g.nodes)
    log.info(f"nodes: {nodes}")
    for node in nodes:
        log.info(f"{node} predecessors: {list(g.predecessors(node))}")


def main():
    """Initialize logging and run the script."""
    logging.basicConfig(format='%(asctime)s %(levelname)s--: %(message)s',
                        level=logging.DEBUG)
    run([8, 7, 7, 4, 8, 1, 3, 8], 6)


if __name__ == '__main__':
    main()
