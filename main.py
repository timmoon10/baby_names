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
    data_file = root_dir() / "data" / "namesbystate" / f"{state}.TXT"
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
    year_min = min(year_name_counts.keys())
    year_max = max(year_name_counts.keys())
    result = collections.OrderedDict()
    for year in range(year_min, year_max+1):
        items = [(count, name) for name, count in year_name_counts[year].items()]
        items.sort(reverse=True)
        result[year] = collections.OrderedDict((name, count) for count, name in items)
    return result


def sort_name_year_counts(
    name_year_counts: dict[str, dict[int, int]],
) -> dict[str, dict[int, int]]:
    result = {}
    for name, year_counts in name_year_counts.items():
        year_min = min(year_counts.keys())
        year_max = max(year_counts.keys())
        result[name] = collections.OrderedDict(
            (year, year_counts[year]) for year in range(year_min, year_max+1)
        )
    return result


def plot_trends_for_name(
    name: str,
    year_name_counts: dict[int, dict[str, int]],
    name_year_counts: dict[str, dict[int, int]],
    year_total_counts: dict[int, int],
):

    # Check name
    if name not in name_year_counts:
        raise RuntimeError(f"Could not find {name} in data")

    # Year bounds
    year_min = min(name_year_counts[name].keys())
    year_max = max(name_year_counts[name].keys())

    # Compute trends
    counts = name_year_counts[name]
    frequencies = collections.OrderedDict(
        (year, count / year_total_counts[year])
        for year, count in counts.items()
    )
    ranks = collections.OrderedDict()
    for year in range(year_min, year_max+1):
        if counts[year] > 0:
            ranks[year] = next(
                idx + 1 for idx, n in enumerate(year_name_counts[year].keys())
                if n == name
            )

    # Plot
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1)
    fig.suptitle(name)
    ax1.plot(list(counts.keys()), list(counts.values()))
    ax1.set_title("Total count")
    ax1.set(ylabel="Count")
    ax1.set_xlim(year_min, year_max)
    ax1.set_yscale("log")
    ax2.plot(list(frequencies.keys()), list(frequencies.values()))
    ax2.set_title("Frequency")
    ax2.set(ylabel="Frequency")
    ax2.set_xlim(year_min, year_max)
    ax2.set_yscale("log")
    ax3.plot(list(ranks.keys()), list(ranks.values()))
    ax3.set_title("Rank")
    ax3.set(ylabel="Rank")
    ax3.set_xlim(year_min, year_max)
    ax3.set_yscale("log")
    ax3.yaxis.set_inverted(True)


def show_top_names(
    num_names: int,
    year: int,
    year_name_counts: dict[int, dict[str, int]],
    year_total_counts: dict[int, int],
) -> None:
    print("Name frequencies")
    print("----------------")
    total_count = year_total_counts[year]
    for idx, (name, count) in enumerate(year_name_counts[year].items()):
        if idx >= num_names:
            break
        print(f"{name}: {count / total_count}")
    print()


def is_name_frequency_above_threshold(
    name,
    min_frequency: float,
    year_min: int,
    year_max: int,
    year_name_counts: dict[int, dict[str, int]],
    year_total_counts: dict[int, int],
) -> bool:
    for year in range(year_min, year_max+1):
        name_counts = year_name_counts[year]
        if name not in name_counts:
            return False
        if name_counts[name] / year_total_counts[year] < min_frequency:
            return False
    return True


def is_name_frequency_falling(
    name,
    year_min: int,
    year_max: int,
    year_name_counts: dict[int, dict[str, int]],
    year_total_counts: dict[int, int],
    tolerance: float = 0.25,
) -> bool:
    year_mid = year_min + (year_max - year_min + 2) // 2
    name_count1 = 0
    name_count2 = 0
    total_count1 = 0
    total_count2 = 0
    for year in range(year_min, year_mid):
        name_count1 += year_name_counts[year][name]
        total_count1 += year_total_counts[year]
    for year in range(year_mid, year_max+1):
        name_count2 += year_name_counts[year][name]
        total_count2 += year_total_counts[year]
    frequency1 = name_count1 / total_count1
    frequency2 = name_count2 / total_count2
    return frequency1 > (1 + tolerance) * frequency2


def show_filtered_top_names(
    num_candidates: int,
    year: int,
    year_name_counts: dict[int, dict[str, int]],
    year_total_counts: dict[int, int],
) -> None:

    # Candidate names
    names = []
    for idx, name in enumerate(year_name_counts[year].keys()):
        if idx >= num_candidates:
            break
        names.append(name)
    min_frequency = year_name_counts[year][names[-1]] / year_total_counts[year]

    # Filter function
    def keep_name(name) -> bool:
        if not is_name_frequency_above_threshold(
            name,
            min_frequency,
            year - 50 + 1,
            year,
            year_name_counts,
            year_total_counts,
        ):
            # Name has not maintained popularity for 50 years
            return False
        if is_name_frequency_falling(
            name,
            year - 10 + 1,
            year,
            year_name_counts,
            year_total_counts,
        ):
            # Name frequency is falling within 10-year timeframe
            return False
        if is_name_frequency_falling(
            name,
            year - 20 + 1,
            year,
            year_name_counts,
            year_total_counts,
        ):
            # Name frequency is falling within 20-year timeframe
            return False
        if is_name_frequency_falling(
            name,
            year - 50 + 1,
            year,
            year_name_counts,
            year_total_counts,
        ):
            # Name frequency is falling within 50-year timeframe
            return False
        return True

    # Apply filter
    names = filter(keep_name, names)

    # Print filtered names and frequencies
    print("Filtered name frequencies")
    print("-------------------------")
    total_count = year_total_counts[year]
    for name in names:
        print(f"{name}: {year_name_counts[year][name] / total_count}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gender", default="M", type=str)
    parser.add_argument("--states", nargs="+")
    parser.add_argument("--year", default=None, type=int)
    parser.add_argument("--name", default=None, type=str, help="Show trends for a name")
    parser.add_argument("--top", default=None, type=int, help="Show top names")
    parser.add_argument("--filter-top", default=None, type=int, help="Show filtered top names")
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
    name_year_counts = sort_name_year_counts(name_year_counts)
    year_total_counts = {
        year: sum(name_counts.values())
        for year, name_counts in year_name_counts.items()
    }
    year_min = min(year_total_counts.keys())
    year_max = max(year_total_counts.keys())
    target_year = year_max if args.year is None else args.year

    # Plot trends for a name
    if args.name is not None:
        name = args.name.lower()

        # Print statistics
        year = target_year
        count = year_name_counts[year].get(name, 0)
        frequency = count / year_total_counts[year]
        rank = -1
        if name in year_name_counts[year]:
            rank = next(
                idx + 1 for idx, n in enumerate(year_name_counts[year].keys())
                if n == name
            )
        print(f"{year} statistics for {name}")
        print(f"Total count: {count}")
        print(f"Frequency: {frequency}")
        print(f"Rank: {rank}")

        # Plot trends
        plot_trends_for_name(name, year_name_counts, name_year_counts, year_total_counts)
        plt.show()

    # Show top names
    if args.top is not None:
        show_top_names(args.top, target_year, year_name_counts, year_total_counts)

    # Show filtered top names
    if args.filter_top is not None:
        show_filtered_top_names(
            args.filter_top,
            target_year,
            year_name_counts,
            year_total_counts,
        )


if __name__ == "__main__":
    main()
