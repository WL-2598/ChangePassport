"""Allow ``python -m changepassport`` as an alternative to the console script."""

from changepassport.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
