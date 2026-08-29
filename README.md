# 201yams

A probability calculator for the dice game Yams (Yahtzee). Given the current
value of up to five dice (`0` for any die not yet thrown) and a target
combination, it computes the percentage chance of completing that combination
once the remaining dice are rolled.

Recognized combinations (`A`/`B` are digits 1-6):

| Pattern         | Meaning                                    |
|-----------------|---------------------------------------------|
| `pair_A`        | at least a pair of `A`                       |
| `three_A`       | three of a kind of `A`                       |
| `four_A`        | four of a kind of `A`                        |
| `full_A_B`      | full house: three `A` + pair `B`             |
| `straight_A`    | a straight ending on `A` (`A` must be 5 or 6)|
| `yams_A`        | five of a kind (Yams) of `A`                 |

## Build

This is a plain Python 3 script (`#!/usr/bin/python3`), not a compiled C
binary — there is nothing to build. Run it directly with an interpreter.

- **Windows note:** the file has no `.py` extension, so double-clicking or
  running it directly won't work; invoke it explicitly:
  ```
  python 201yams 0 0 0 0 0 yams_4
  ```
  (or `py 201yams ...` if the `py` launcher is installed).
- On Linux/macOS/WSL/Git Bash it is already executable and can be run as
  `./201yams ...` since the shebang points at `python3`.

## Usage

```
./201yams d1 d2 d3 d4 d5 c
```
`d1`-`d5` are die values 0-6 (0 = not thrown yet), `c` is the target
combination pattern described above. Passing a malformed set of arguments
exits with status `84`.

Examples:
```
$ ./201yams -h
USAGE
        201yams d1 d2 d3 d4 d5 c
...

$ ./201yams 0 0 0 0 0 yams_4
chances to get a 4 yams:  0.01%

$ ./201yams 1 2 3 4 5 four_4
chances to get a 4 four-of-a-kind:  1.62%

$ ./201yams 2 2 5 4 6 straight_6
chances to get a 6 straight:  16.67%

$ ./201yams 2 3 2 3 2 full_2_3
chances to get a 2 full of 3:  100.00%
```

## How it works

`argument_parsing_find_error` validates the die values and matches the
combination string against the known templates. `main` then dispatches to one
of three probability routines:

- `deduce_probability` handles `pair`/`three`/`four`/`yams`: it counts how
  many of the already-thrown dice already match the target face, then uses
  the binomial formula (`binomiale`, built on `a_among_b` i.e. n-choose-k) to
  sum the probability of rolling enough additional matches (each unthrown die
  is an independent 1/6 trial) among the remaining dice.
- `deduce_probability_full` handles `full_A_B` by counting existing matches
  of both target faces and combining `a_among_b` counts for the missing three
  and missing pair over `6^remaining`.
- `deduce_probability_straight` handles `straight_A` by checking how many of
  the 5 consecutive values ending at `A` are already present, then computing
  the probability that the remaining dice each land on one of the still
  needed values (`5! / 6^remaining` for the fully-ordered case).

## Tests

`test.sh` exercises the CLI: it prints the help text and runs a handful of
representative combinations (`yams_4`, `four_4`, `straight_6`, and both a
failing and a satisfied `full_2_3`) to sanity-check the output.

`test_201yams.py` is a pytest suite (run with `python -m pytest
test_201yams.py -v`) that invokes the script as a subprocess and covers the
README examples above, boundary die/combination values, and malformed input
(missing args, out-of-range dice, bad combination strings).

### Fixed bug

`argument_parsing_find_error` accepted `0` as a valid combination face digit
(e.g. `pair_0`, `full_0_2`), even though `0` is reserved to mean "die not
thrown yet" and the documented pattern range is 1-6. This let `pair_0` (and
similarly `three_0`/`four_0`/`yams_0`/`full_0_B`) slip past validation and
print a nonsensical result like `chances to get a 0 pair:  100.00%`. Fixed
by requiring the combination's face digit(s) to be in `1-6` instead of
`0-6`.

### Known issue (not fixed)

`full_A_B` accepts `A == B` (e.g. `full_2_2`), a combination that's
impossible in real Yams (a full house needs two *different* face values),
and still computes a spurious non-zero probability for it instead of
rejecting the input. Fixing this requires deciding new validation semantics
(reject `A == B`) that aren't specified anywhere in the existing code, so it
is left as a known issue — see the `xfail`-marked test in
`test_201yams.py`.
