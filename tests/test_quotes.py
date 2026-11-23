from check_quotes import norm


def test_norm_ignores_case_punctuation_and_whitespace():
    assert norm("  Only Admins   can create API-tokens. ") == "only admins can create api tokens"


def test_norm_keeps_non_latin_text():
    assert "契約" in norm("契約後 に開示")   # regression: the checker once stripped all non-ASCII
