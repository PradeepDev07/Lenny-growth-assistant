import pytest
from ingestion.chunker import chunk_transcript
from backend.app.retrieval.vector_store import vector_store


def test_chunk_transcript_sliding_window():
    episode = {
        "episode_id": "test-ep-1",
        "title": "Test Title",
        "guest": "Test Guest",
        "url": "https://test.com",
        "transcript": "Paragraph 1 is about growth.\n\nParagraph 2 is about retention.\n\nParagraph 3 is about referral."
    }
    chunks = chunk_transcript(episode, max_chars=80, overlap_chars=20)
    assert len(chunks) >= 1
    for c in chunks:
        assert c["episode_id"] == "test-ep-1"
        assert "content" in c
        assert c["guest"] == "Test Guest"


def test_retrieval_elena_verna_activation():
    results = vector_store.search("How should we measure activation metrics in B2B PLG?", top_k=3)
    assert len(results) > 0
    top_hit = results[0]
    # Elena Verna's episode should be the top match
    assert "Elena Verna" in top_hit["guest"] or "Elena Verna" in top_hit["source_title"]
    assert top_hit["score"] > 0.05


def test_retrieval_brian_balfour_loops():
    results = vector_store.search("Why do growth loops beat traditional marketing funnels?", top_k=3)
    assert len(results) > 0
    top_hit = results[0]
    assert "Brian Balfour" in top_hit["guest"] or "loops" in top_hit["content"].lower()
    assert top_hit["score"] > 0.05


def test_retrieval_shreyas_doshi_metrics():
    results = vector_store.search("What is the LNO framework for high agency PMs?", top_k=3)
    assert len(results) > 0
    top_hit = results[0]
    assert "Shreyas Doshi" in top_hit["guest"] or "lno" in top_hit["content"].lower()
    assert top_hit["score"] > 0.05


def test_retrieval_empty_query():
    results = vector_store.search("", top_k=3)
    assert results == []
