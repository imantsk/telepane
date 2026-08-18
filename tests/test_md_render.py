from telepane.widgets import md_render


def test_fence_map_complete_pair():
    lines = ["```php", "phpinfo();", "```", "after"]
    fences = md_render.fence_map(lines)
    assert fences == {0: "php", 2: None}
    assert md_render.fence_interior(fences) == {1}


def test_fence_map_unclosed_reverts_to_plain():
    fences = md_render.fence_map(["```php", "phpinfo();"])
    assert fences == {}
    assert md_render.fence_interior(fences) == set()


def test_fence_map_backspaced_last_backtick():
    fences = md_render.fence_map(["```php", "x", "``"])
    assert fences == {}


def test_transform_bold_and_underline():
    text = md_render.transform_line("**bold** __underline__")
    assert text is not None
    assert text.plain == "bold underline"
    spans = {(s.start, s.end) for s in text.spans}
    assert (0, 4) in spans


def test_transform_incomplete_bold_is_none():
    assert md_render.transform_line("**bold") is None
    assert md_render.transform_line("plain text") is None


def test_transform_heading_conceals_marker():
    text = md_render.transform_line("## Heading 2")
    assert text is not None
    assert text.plain == "Heading 2"


def test_transform_link_hides_url():
    text = md_render.transform_line("see [docs](https://example.com) now")
    assert text is not None
    assert text.plain == "see docs now"


def test_transform_inline_code():
    text = md_render.transform_line("run `ls -la` here")
    assert text is not None
    assert text.plain == "run ls -la here"


def test_hrule_detection():
    assert md_render.is_hrule("---")
    assert md_render.is_hrule("*****")
    assert not md_render.is_hrule("--- separator ---")


def test_rule_text_with_label():
    text = md_render.rule_text(20, "php")
    assert "php" in text.plain
    assert len(text.plain) == 20
    assert md_render.rule_text(10).plain == md_render.RULE_CHAR * 10
