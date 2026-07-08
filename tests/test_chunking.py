from natal_reader.utils.chunking import chunk_markdown

SAMPLE_DOC = """# Robert Hand's Guide

Introductory material about the book's scope and approach to astrology.

## Mars

General remarks about Mars as a planetary archetype and its symbolism.

### Mars in the 10th House

""" + ("Mars in the 10th House brings driven, assertive energy to career and public life. " * 40) + """

## Venus

### Venus in the 7th House

""" + ("Venus in the 7th House brings harmony-seeking, relationship-oriented values to partnerships. " * 40)


def test_chunks_are_nonempty_and_bounded():
    chunks = chunk_markdown(SAMPLE_DOC, "robert-hand.md")
    assert chunks
    for chunk in chunks:
        assert chunk["text"].strip()
        assert len(chunk["text"]) <= 1700


def test_heading_path_prepended_to_every_chunk():
    chunks = chunk_markdown(SAMPLE_DOC, "robert-hand.md")
    mars_chunks = [c for c in chunks if "Mars in the 10th House brings driven" in c["text"]]
    assert mars_chunks
    for chunk in mars_chunks:
        assert "robert-hand.md > Robert Hand's Guide > Mars > Mars in the 10th House" in chunk["text"]
        assert chunk["heading"] == "Robert Hand's Guide > Mars > Mars in the 10th House"


def test_delineation_never_emitted_without_its_heading():
    chunks = chunk_markdown(SAMPLE_DOC, "robert-hand.md")
    for chunk in chunks:
        if "Venus in the 7th House brings harmony-seeking" in chunk["text"]:
            assert "Venus in the 7th House" in chunk["heading"]


def test_source_present_in_payload():
    chunks = chunk_markdown(SAMPLE_DOC, "robert-hand.md")
    assert all(c["source"] == "robert-hand.md" for c in chunks)


def test_empty_content_returns_no_chunks():
    assert chunk_markdown("   \n  ", "empty.md") == []


def test_content_with_no_headings_still_chunks():
    chunks = chunk_markdown("Just plain text with no headings at all.", "plain.md")
    assert len(chunks) == 1
    assert chunks[0]["heading"] == ""
    assert chunks[0]["text"].startswith("plain.md\n\n")
