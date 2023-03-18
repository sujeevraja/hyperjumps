#!/usr/bin/env python

import argparse
import itertools
import logging
import typing

log = logging.getLogger(__name__)


class Config(typing.NamedTuple):
    """Script configuration.

    Attributes:
        nums: numbers from which sequence is to be generated.
        trip_lengths: lengths of trips to be found.
        limit_trips: whether all or a few trips should be generated.
    """
    nums: typing.List[int]
    trip_lengths: typing.List[int]
    limit_trips: bool


class Trip:
    _id_gen = itertools.count()

    def __init__(self, seq: str, nums_left: typing.List[int]):
        self.id: int = next(self._id_gen)
        self.seq: str = seq
        self.nums_left: str = nums_left

    def __repr__(self) -> str:
        return f"Trip({self.id},{self.seq},{self.nums_left})"

    @classmethod
    def reset_id(cls):
        cls._id_gen = itertools.count()

    def prefix(self, num_str: str) -> typing.Optional['Trip']:
        """Prefix num_str to self.seq."""
        nums = list(map(int, num_str))
        nums_left = [n for n in self.nums_left]
        for num in nums:
            try:
                nums_left.remove(num)
            except ValueError:
                return None

        return Trip(f"{num_str}{self.seq}", nums_left)


def build_initial_trips(nums: typing.List[int]) -> typing.List[Trip]:
    trips = []
    for n in set(nums):
        seq = f"{n}9"
        nums_left = [p for p in nums]
        nums_left.remove(n)
        trips.append(Trip(seq, nums_left))
    return trips


def can_reach(p: int, q: int, r: int) -> bool:
    if (p+q) % 10 == r or (p*q) % 10 == r:
        return True

    if p >= q:
        if ((p-q) % 10) == r:
            return True

        if p % q == 0 and p // q == r:
            return True

    return False


def find_counts(nums: typing.List[int]) -> typing.Dict[int, int]:
    num_counts = {}
    for n in nums:
        num_counts[n] = num_counts.get(n, 0) + 1
    return num_counts


class NumInfo(typing.NamedTuple):
    nums: typing.List[int] = []
    unique_nums: typing.Set[int] = {}
    num_counts: typing.Dict[int, int] = {}

    @classmethod
    def build(cls, nums: typing.List[int]) -> 'NumInfo':
        num_info = cls(
            nums=nums,
            unique_nums=set(nums),
            num_counts=find_counts(nums),
        )
        return num_info

    def counts_valid(self, given_nums: typing.List[int]) -> bool:
        counts = find_counts(given_nums)
        for n, count in counts.items():
            if n != 9 and self.num_counts[n] < count:
                return False
        return True


def num_pairs(nums: typing.List[int]) -> typing.Generator:
    for n in nums:
        yield n, 9

    for a, b in itertools.permutations(nums, 2):
        yield a, b


def compute_cab_cache(info: NumInfo) -> typing.Dict[str, typing.List[int]]:
    """
    Collect c such that c <> a == b for single-digit numbers a,b,c and
    <> in {+, - iff c > a, *, / if a divides c}.

    Store them in a dict with keys as "ab" strings.
    """
    cache = {}
    for a, b in num_pairs(info.nums):
        candidates = []
        for c in info.unique_nums:
            if ((c == a or c == b) and c not in info.num_counts):
                continue

            if can_reach(c, a, b) and info.counts_valid([a, b, c]):
                candidates.append(c)

        if candidates:
            cache[f"{a}{b}"] = candidates

    return dict(sorted(cache.items()))


def compute_cdab_cache(
    info: NumInfo, cab_cache: typing.Dict[str, typing.List[int]]
) -> typing.Dict[str, typing.List[str]]:
    """
    Collect d,c such that d <> c == a and (dc - a == b or dc / a == b) for
    single-digit numbers a,b,c,d and <> in
    {+, - iff c > a, *, / if a divides dc}.

    Store them in a dict with keys as "ab" strings.
    """
    cache = {}
    for a, b in num_pairs(info.nums):
        candidates = []

        for d in info.unique_nums:
            cs = cab_cache.get(f"{d}{a}", [])
            for c in cs:
                # here, c is a digit such that c <> d == a.
                # select cd such that cd - a == b or cd // a == b.
                cd = (10*c) + d

                # Note that the d > a case is covered in the "cab" cache itself.
                # Specifically, given cdab with c <> d == a, cd - a == b and
                # d > a, we could generate the same sequence by finding d in
                # the "cab" cache values for "ab" and looking for c in the
                # values of "da". This avoid some duplicate trips.
                valid = d < a and (cd - a) % 10 == b
                valid = valid or (cd % a == 0 and (cd // a) % 10 == b)
                valid = valid and info.counts_valid([a, b, c, d])
                if valid:
                    candidates.append(f"{c}{d}")

        if candidates:
            cache[f"{a}{b}"] = candidates

    return cache


def build_jump_cache(info: NumInfo) -> typing.Dict[str, typing.List[str]]:
    cache1 = compute_cab_cache(info)
    cache2 = compute_cdab_cache(info, cache1)
    cache = {}
    for ab, cs in cache1.items():
        if ab not in cache:
            cache[ab] = []
        for c in cs:
            cache[ab].append(str(c))

    for ab, cds in cache2.items():
        if ab not in cache:
            cache[ab] = []
        cache[ab].extend(cds)

    return cache


def find_trips(
        nums: typing.List[int],
        jump_lengths: typing.List[int] = [6, 7, 8, 9]
) -> typing.Dict[int, typing.Set[str]]:
    """
    Algorithm to find trips of specific length using a given list of
    single-digit numbers.

    Rules to create a trip:
    - All numbers in the trip should be in the given list of numbers, except
        the last one, which should be 9.
    - The first 2 numbers can be any pair.
    - Starting from the third element, each number should be the ones digit of
        adding, subtracting, multiplying or dividing the previous 2 numbers.
    - Consider a trip like (...a,b,c,d,...) in which a,b,c,d are single digits.
        The d can be generated as the ones digit of b <> c where <> is
        (+ mod 10, - if valid, * mod 10, / if c divides b). We can also
        generate d by concatenating a and b into the 2-digit number ab and then
        using (ab - c) or (ab // c if c divides ab).

    Examples:
        valid trips for [4,5,1,2,7,3,3,6]:
            413369 (4+1=3, 1*3=3, 3+3=6, 3+6=9)
            331459 (3/3=1, 3+1=4, 1+4=5, 4+5=9)
            431239 (4-3=1, 3-1=2, 1+2=3, 12-3=9)
    """
    cache = build_jump_cache(NumInfo.build(nums))
    log.info("jump cache")
    num_jumps = 0
    for ab, jumps in cache.items():
        log.info(f"\t{ab}: {jumps}")
        num_jumps += len(jumps)
    log.info(f"num jumps found: {num_jumps}")

    trips_by_length = {l: set() for l in jump_lengths}
    trips = build_initial_trips(nums)
    while trips:
        trip = trips.pop()
        ab: str = trip.seq[:2]
        for jump in cache.get(ab, []):
            ext = trip.prefix(jump)
            if ext:
                trips.append(ext)
                if len(ext.seq) in trips_by_length:
                    trips_by_length[len(ext.seq)].add(ext.seq)

    log.info(f"num trips: {next(Trip._id_gen)}")
    return trips_by_length


def run(cfg: Config):
    trips_by_length = find_trips(cfg.nums, cfg.trip_lengths)
    for length, trips in trips_by_length.items():
        log.info(f"{len(trips)} trips of length {length}")
        if cfg.limit_trips:
            trips = list(trips)[:(10-length)]
        for trip in trips:
            log.info(f"\t{trip}")


def handle_command_line():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    with open("planet_numbers.txt", "r") as infile:
        default_nums = next(infile)
    parser.add_argument("-n", "--nums", type=str, default=default_nums,
                        help="digits from which trips are to be found")

    default_trip_lengths = [6, 7, 8, 9]
    parser.add_argument("-t", "--trip_lengths", type=int, nargs='+',
                        default=default_trip_lengths,
                        help="lenths of trips to find")

    parser.add_argument("-l", "--limit", action="store_true",
                        help="limit number of sequences generated")

    args = parser.parse_args()
    return Config(
        nums=[int(c) for c in args.nums],
        trip_lengths=args.trip_lengths,
        limit_trips=args.limit)


def main():
    """Initialize logging and run the script."""
    logging.basicConfig(format='%(asctime)s %(levelname)s--: %(message)s',
                        level=logging.DEBUG)
    cfg = handle_command_line()
    run(cfg)


if __name__ == '__main__':
    main()
