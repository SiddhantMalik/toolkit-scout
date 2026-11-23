from norm import access_cls, auth_set
from score import _score_field, wilson


def test_wilson_interval_brackets_the_point_estimate():
    low, high = wilson(16, 20)
    assert low < 80 < high


def test_wilson_handles_empty_sample():
    assert wilson(0, 0) == (0, 0)


def test_correct_unknown_counts_as_correct():
    gold = {1: {"verdict": "unknown"}}
    assert _score_field({1: {"verdict": "unknown"}}, gold, "verdict")["correct"] == 1


def test_abstention_is_counted_and_not_correct():
    gold = {1: {"mcp_official": True}}
    result = _score_field({1: {"mcp_official": None}}, gold, "mcp_official")
    assert (result["correct"], result["abstained"], result["n"]) == (0, 1, 1)


def test_gold_without_a_label_is_skipped():
    assert _score_field({1: {"access": "self"}}, {1: {"verdict": "easy"}}, "access")["n"] == 0


def test_vocabulary_collapsing():
    assert auth_set(["api_key", "token", "oauth2"]) == ["key", "oauth2"]
    assert access_cls("kyc_verification") == "gated" and access_cls("self_trial") == "self"
