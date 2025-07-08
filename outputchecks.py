"""Wrapper module calling sanity checks implemented in outputchecks_generated.py"""

from outputchecks_generated import run_sanity_checks

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run sanity checks on statement csvs")
    parser.add_argument("data_dir", help="Directory containing statement csv files")
    args = parser.parse_args()

    run_sanity_checks(args.data_dir)
