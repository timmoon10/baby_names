import argparse
import csv
import collections
import heapq
import pathlib
import functools

import matplotlib.pyplot as plt


_all_states: list[str] = [
    "AK", "AL", "AR", "AZ", "CA", "CO", "CT", "DC", "DE", "FL",
    "GA", "HI", "IA", "ID", "IL", "IN", "KS", "KY", "LA", "MA",
    "MD", "ME", "MI", "MN", "MO", "MS", "MT", "NC", "ND", "NE",
    "NH", "NJ", "NM", "NV", "NY", "OH", "OK", "OR", "PA", "RI",
    "SC", "SD", "TN", "TX", "UT", "VA", "VT", "WA", "WI", "WV",
    "WY",
]


@functools.cache
def root_dir() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent.resolve()


def load_state_data_(
    state: str,
    gender: str,
    year_name_counts: dict[int, dict[str, int]],
    name_year_counts: dict[str, dict[int, int]],
) -> None:
    data_file = root_dir() / "namesbystate" / f"{state}.TXT"
    with open(data_file, mode="r") as f:
        for row in csv.reader(f):
            if row[1] != gender:
                continue
            year = int(row[2])
            name = row[3].lower()
            count = int(row[4])
            if count <= 0:
                continue
            year_name_counts[year][name] += count
            name_year_counts[name][year] += count


def sort_year_name_counts(
    year_name_counts: dict[int, dict[str, int]],
) -> dict[int, dict[str, int]]:
    year_start = min(year_name_counts.keys())
    year_end = max(year_name_counts.keys()) + 1
    result = collections.OrderedDict()
    for year in range(year_start, year_end):
        items = [(count, name) for name, count in year_name_counts[year].items()]
        items.sort(reverse=False)
        result[year] = collections.OrderedDict((name, count) for count, name in items)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default=None)
    parser.add_argument("--gender", default="M")
    parser.add_argument("--states", nargs="+")
    args = parser.parse_args()
    print("\n".join(f"{key}: {val}" for key, val in vars(args).items()))
    print()
    return args


def main() -> None:

    # Command-line arguments
    args = parse_args()
    gender = args.gender.upper()
    states = _all_states if args.states is None else args.states
    states = [state.upper() for state in states]

    # Load name data from file
    year_name_counts: dict[int, dict[str, int]] = collections.defaultdict(
        lambda: collections.defaultdict(lambda: 0)
    )
    name_year_counts: dict[str, dict[int, int]] = collections.defaultdict(
        lambda: collections.defaultdict(lambda: 0)
    )
    for state in states:
        load_state_data_(state, gender, year_name_counts, name_year_counts)

    # Postprocess data
    year_name_counts = sort_year_name_counts(year_name_counts)
    year_total_counts = {
        year: sum(name_counts.values())
        for year, name_counts in year_name_counts.items()
    }

    if args.name is not None:
        name = args.name.lower()
        if name not in name_year_counts:
            raise RuntimeError(f"Could not find {name} in data")

        counts = {}
        count_fractions = {}
        ranks = {}
        year_counts = name_year_counts[name]
        for year, total_count in year_total_counts.items():
            if year not in year_counts:
                continue
            counts[year] = year_counts[year]
            count_fractions[year] = year_counts[year] / total_count
            ranks[year] = next(
                idx for idx, n in enumerate(year_name_counts[year].keys())
                if n == name
            )  ### TODO Fix

        # Plot
        fig, ax = plt.subplots()
        line, = ax.plot(list(count_fractions.keys()), list(count_fractions.values()))
        ax.set(xlabel="Year", ylabel="Count")
        plt.show()


if __name__ == "__main__":
    main()
