import sys


def solve(data: str) -> None:
    tokens = data.split()
    if not tokens:
        return
    print(tokens[0])


if __name__ == "__main__":
    solve(sys.stdin.read())
