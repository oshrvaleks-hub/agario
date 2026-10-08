"""Entry point: `python3 agar.py [--frames N]`."""
import argparse
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description="agar.io clone")
    parser.add_argument("--frames", type=int, default=None,
                        help="run N frames of the main loop, then exit (headless checks)")
    args = parser.parse_args(argv)
    from agario.game import run
    return run(args.frames)


if __name__ == "__main__":
    sys.exit(main())
