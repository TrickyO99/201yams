"""
Automated test suite for 201yams (Yams/Yahtzee combination probability calculator).

Invokes the script as a subprocess, exactly as a real user would run it,
and asserts on stdout / exit code.
"""
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent / "201yams"


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# Help / usage
# ---------------------------------------------------------------------------

def test_help_flag_prints_usage_and_exits_zero():
    result = run("-h")
    assert result.returncode == 0
    assert "USAGE" in result.stdout
    assert "201yams" in result.stdout


def test_help_long_flag():
    result = run("--help")
    assert result.returncode == 0
    assert "USAGE" in result.stdout


# ---------------------------------------------------------------------------
# Documented happy-path examples (straight from the README)
# ---------------------------------------------------------------------------

def test_readme_example_yams_from_scratch():
    result = run("0", "0", "0", "0", "0", "yams_4")
    assert result.returncode == 0
    assert result.stdout.strip() == "chances to get a 4 yams:  0.01%"


def test_readme_example_four_of_a_kind():
    result = run("1", "2", "3", "4", "5", "four_4")
    assert result.returncode == 0
    assert result.stdout.strip() == "chances to get a 4 four-of-a-kind:  1.62%"


def test_readme_example_straight():
    result = run("2", "2", "5", "4", "6", "straight_6")
    assert result.returncode == 0
    assert result.stdout.strip() == "chances to get a 6 straight:  16.67%"


def test_readme_example_full_house_complete():
    result = run("2", "3", "2", "3", "2", "full_2_3")
    assert result.returncode == 0
    assert result.stdout.strip() == "chances to get a 2 full of 3:  100.00%"


# ---------------------------------------------------------------------------
# Edge cases: boundary values
# ---------------------------------------------------------------------------

def test_combination_already_complete_is_100_percent():
    """All five dice already match the target -> guaranteed (100%)."""
    result = run("4", "4", "4", "4", "4", "yams_4")
    assert result.returncode == 0
    assert "100.00%" in result.stdout


def test_die_value_upper_boundary_six_accepted():
    result = run("6", "6", "6", "6", "6", "yams_6")
    assert result.returncode == 0
    assert "100.00%" in result.stdout


def test_die_value_zero_means_not_thrown_and_is_accepted():
    result = run("0", "1", "2", "3", "4", "pair_1")
    assert result.returncode == 0


def test_straight_requires_five_or_six_not_lower_face():
    """README: straight_A requires A to be 5 or 6."""
    result = run("1", "2", "3", "4", "5", "straight_4")
    assert result.returncode == 84


def test_straight_five_is_a_valid_boundary():
    result = run("1", "2", "3", "4", "5", "straight_5")
    assert result.returncode == 0
    assert "100.00%" in result.stdout


# ---------------------------------------------------------------------------
# Bad input: should fail gracefully (exit 84), never an unhandled traceback
# ---------------------------------------------------------------------------

def test_missing_arguments_fails_gracefully():
    result = run("0", "0", "0", "0", "0")
    assert result.returncode == 84
    assert "Traceback" not in result.stderr


def test_no_arguments_fails_gracefully():
    result = run()
    assert result.returncode == 84
    assert "Traceback" not in result.stderr


def test_die_value_out_of_range_fails_gracefully():
    result = run("7", "0", "0", "0", "0", "yams_4")
    assert result.returncode == 84
    assert "Traceback" not in result.stderr


def test_negative_die_value_fails_gracefully():
    result = run("-1", "0", "0", "0", "0", "yams_4")
    assert result.returncode == 84
    assert "Traceback" not in result.stderr


def test_non_numeric_die_value_fails_gracefully():
    result = run("a", "0", "0", "0", "0", "yams_4")
    assert result.returncode == 84
    assert "Traceback" not in result.stderr


def test_malformed_combination_fails_gracefully():
    result = run("0", "0", "0", "0", "0", "nonsense")
    assert result.returncode == 84
    assert "Traceback" not in result.stderr


def test_extra_arguments_fail_gracefully():
    result = run("0", "0", "0", "0", "0", "yams_4", "extra")
    assert result.returncode == 84
    assert "Traceback" not in result.stderr


# ---------------------------------------------------------------------------
# Bug fix regression test: combination face digit 0 used to be accepted
# (e.g. "pair_0"), producing a nonsensical result ("chances to get a 0
# pair: 100.00%") since 0 is reserved to mean "die not yet thrown", not a
# real face value. Fixed in argument_parsing_find_error to require 1-6.
# ---------------------------------------------------------------------------

def test_combination_face_zero_is_rejected():
    result = run("0", "0", "0", "0", "0", "pair_0")
    assert result.returncode == 84
    assert "Traceback" not in result.stderr


def test_full_house_face_zero_is_rejected():
    result = run("0", "0", "0", "0", "0", "full_0_2")
    assert result.returncode == 84


# ---------------------------------------------------------------------------
# Known issue (documented, not fixed): full_A_B accepts A == B (e.g.
# "full_2_2"), a combination that is impossible in real Yams (a full
# house needs two *different* face values), but the script still computes
# and prints a spurious non-zero probability for it instead of rejecting
# the input. The fix would require deciding new validation semantics
# (reject A == B) that isn't specified anywhere in the current code or
# README, so it is left as a documented known issue rather than "fixed".
# ---------------------------------------------------------------------------

@pytest.mark.xfail(
    reason="Known issue: full_A_B with A == B (e.g. full_2_2) is accepted "
           "and produces a spurious non-zero probability for an "
           "impossible combination instead of being rejected.",
    strict=True,
)
def test_full_house_same_face_twice_should_be_rejected():
    result = run("2", "2", "0", "0", "0", "full_2_2")
    assert result.returncode == 84
