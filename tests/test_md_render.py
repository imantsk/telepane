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


def test_line_links_spans_and_url():
    line = "**b** [docs](https://x.io) end"
    links = md_render.line_links(line)
    assert len(links) == 1
    src_start, src_end, vis_start, vis_end, url = links[0]
    assert url == "https://x.io"
    assert line[src_start:src_end] == "[docs](https://x.io)"
    # preview shows "b docs end": docs occupies visual 2..6
    assert (vis_start, vis_end) == (2, 6)


def test_line_links_in_heading():
    line = "## see [docs](https://x.io)"
    links = md_render.line_links(line)
    assert len(links) == 1
    assert links[0][2] == links[0][0] - 3


def test_line_links_none():
    assert md_render.line_links("no links here") == []
