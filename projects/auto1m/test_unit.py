#!/usr/bin/env python3
"""Unit tests for auto1m pure functions — no router needed.

Covers: split_sentences edge cases, chunk_text provenance correctness,
query_terms, rank_chunks ordering, score_facts keyword fallback,
collapse_once batching, tree_reduce budget behavior (chat mocked).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import auto1m


class TestSplitSentences(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(auto1m.split_sentences(""), [])

    def test_no_punctuation(self):
        self.assertEqual(auto1m.split_sentences("hello world"), ["hello world"])

    def test_basic(self):
        s = auto1m.split_sentences("One. Two! Three?")
        self.assertEqual(s, ["One.", "Two!", "Three?"])

    def test_newline_split(self):
        s = auto1m.split_sentences("line one\nline two")
        self.assertEqual(s, ["line one", "line two"])

    def test_cjk_punctuation(self):
        s = auto1m.split_sentences("这是第一句。第二句！")
        self.assertEqual(len(s), 2)

    def test_pathological_long_line(self):
        # >2000 chars with no sentence end -> hard split, no chunk lost
        text = "x" * 4500
        s = auto1m.split_sentences(text)
        self.assertEqual("".join(s), text)
        self.assertTrue(all(len(p) <= 2000 for p in s))

    def test_semicolon(self):
        s = auto1m.split_sentences("a; b")
        self.assertEqual(len(s), 2)


class TestChunkText(unittest.TestCase):
    def setUp(self):
        self.text = " ".join(f"Sentence number {i} about routers and facts."
                             for i in range(200))
        self.chunks = auto1m.chunk_text(self.text, source="test.md",
                                        chunk_tokens=1000, overlap_tokens=100)

    def test_chunk_count_positive(self):
        self.assertGreater(len(self.chunks), 1)

    def test_ids_sequential(self):
        ids = [c["id"] for c in self.chunks]
        self.assertEqual(ids, [f"C{i:04d}" for i in range(len(ids))])

    def test_start_id_offset(self):
        ch = auto1m.chunk_text(self.text, source="t", chunk_tokens=1000,
                               overlap_tokens=100, start_id=42)
        self.assertEqual(ch[0]["id"], "C0042")

    def test_provenance_fields(self):
        prev_start = 0
        for c in self.chunks:
            self.assertEqual(c["source"], "test.md")
            self.assertGreater(c["end"], c["start"])
            self.assertGreaterEqual(c["start"], prev_start)
            prev_start = c["start"]
            # every sentence of the chunk must appear in the raw source slice
            raw = self.text[c["start"]:c["end"]]
            for s in auto1m.split_sentences(c["text"]):
                self.assertIn(s, raw)

    def test_overlap_spans_honest(self):
        # consecutive chunk spans genuinely overlap (overlap sentences keep
        # original offsets), not synthetic duplicate text
        overlapped = any(b["start"] < a["end"]
                         for a, b in zip(self.chunks, self.chunks[1:]))
        self.assertTrue(overlapped)

    def test_budget_respected(self):
        for c in self.chunks[:-1]:
            self.assertLessEqual(auto1m.est_tokens(c["text"]), 1000 + 2000)

    def test_overlap_carried(self):
        # consecutive chunks should share trailing/leading sentences
        for a, b in zip(self.chunks, self.chunks[1:]):
            a_sents = set(auto1m.split_sentences(a["text"]))
            b_sents = set(auto1m.split_sentences(b["text"]))
            self.assertTrue(a_sents & b_sents, "overlap must repeat sentences")

    def test_empty_text(self):
        self.assertEqual(auto1m.chunk_text("", source="x"), [])


class TestQueryTerms(unittest.TestCase):
    def test_extracts_words_min3(self):
        terms = auto1m.query_terms("What are yote's hardware specs to go?")
        self.assertIn("yote", terms)
        self.assertIn("hardware", terms)
        self.assertIn("specs", terms)
        self.assertIn("are", terms)     # 3 chars: kept
        self.assertNotIn("to", terms)   # 2 chars: dropped
        self.assertNotIn("go", terms)

    def test_lowercase(self):
        terms = auto1m.query_terms("GPU RTX 3090")
        self.assertTrue(all(t == t.lower() for t in terms))


class TestRankChunks(unittest.TestCase):
    def test_most_relevant_first(self):
        chunks = [
            {"id": "C0000", "text": "the weather is nice today"},
            {"id": "C0001", "text": "yote has 16 cores and 62 GB RAM"},
            {"id": "C0002", "text": "yote runs CachyOS on an RTX 3090"},
        ]
        ordered = auto1m.rank_chunks(chunks, "yote hardware cores RAM GPU")
        self.assertEqual(ordered[0]["id"], "C0001")
        self.assertEqual(ordered[-1]["id"], "C0000")

    def test_stable_on_ties(self):
        chunks = [{"id": f"C{i:04d}", "text": "unrelated blah"} for i in range(5)]
        ordered = auto1m.rank_chunks(chunks, "zzz qqq")
        self.assertEqual([c["id"] for c in ordered],
                         [f"C{i:04d}" for i in range(5)])


class TestScoreFactsFallback(unittest.TestCase):
    def test_keyword_fallback_on_chat_failure(self):
        # chat raises -> keyword-order fallback, no router needed
        real = auto1m.chat
        auto1m.chat = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down"))
        try:
            facts = ["yote has 16 cores of CPU", "the sky is blue today"]
            out = auto1m.score_facts(facts, "yote hardware cores")
            self.assertEqual(out[0], facts[0])
            self.assertEqual(len(out), 2)
        finally:
            auto1m.chat = real

    def test_empty_facts(self):
        self.assertEqual(auto1m.score_facts([], "q"), [])


class TestCollapseReduce(unittest.TestCase):
    def fake_collapse(self, model, messages, max_tokens=1024, timeout=120):
        # deterministic collapse: return first line of batch verbatim
        content = messages[0]["content"]
        lines = [l for l in content.splitlines() if "[C" in l]
        return lines[0] if lines else "NO TAGS", 0.1

    def test_collapse_once_batches_and_collapses(self):
        real = auto1m.chat
        auto1m.chat = self.fake_collapse
        try:
            facts = [f"[C{i:04d}] fact number {i} about the fleet " + "padding " * 80
                     for i in range(40)]
            self.assertGreater(auto1m.est_tokens("\n".join(facts)),
                               auto1m.REDUCE_BUDGET)
            out = auto1m.collapse_once(facts, "fleet")
            # REDUCE_BUDGET=5000 -> several batches; fake returns 1 line each
            self.assertLess(len(out), len(facts))
            self.assertTrue(all("[C" in f for f in out))
        finally:
            auto1m.chat = real

    def test_collapse_once_small_set_untouched(self):
        real = auto1m.chat
        auto1m.chat = self.fake_collapse
        try:
            facts = ["[C0001] one", "[C0002] two"]
            self.assertEqual(auto1m.collapse_once(facts, "q"), facts)
        finally:
            auto1m.chat = real

    def test_collapse_fail_open_on_chat_error(self):
        real = auto1m.chat
        auto1m.chat = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down"))
        try:
            facts = [f"[C{i:04d}] fact {i} " + "x" * 400 for i in range(30)]
            out = auto1m.collapse_once(facts, "q")
            self.assertEqual(out, facts)  # fail-open: keep facts, never drop
        finally:
            auto1m.chat = real

    def test_tree_reduce_respects_budget(self):
        real = auto1m.chat
        calls = {"n": 0}

        def fake(model, messages, max_tokens=1024, timeout=120):
            calls["n"] += 1
            content = messages[0]["content"]
            lines = [l for l in content.splitlines() if "[C" in l]
            return lines[0] if lines else "", 0.1

        auto1m.chat = fake
        try:
            facts = [f"[C{i:04d}] fact number {i} about yote" + " padding" * 50
                     for i in range(120)]
            big = auto1m.est_tokens("\n".join(facts))
            self.assertGreater(big, auto1m.REDUCE_BUDGET)
            out = auto1m.tree_reduce(facts, "yote")
            self.assertLessEqual(auto1m.est_tokens("\n".join(out)),
                                 auto1m.REDUCE_BUDGET)
            self.assertGreater(calls["n"], 0)
        finally:
            auto1m.chat = real


class TestEstTokens(unittest.TestCase):
    def test_monotone(self):
        self.assertLess(auto1m.est_tokens("a"), auto1m.est_tokens("a" * 1000))

    def test_empty(self):
        self.assertEqual(auto1m.est_tokens(""), 1)


class TestRewriteDangling(unittest.TestCase):
    def test_valid_tag_untouched(self):
        prov = {"C0007": {}, "C0008": {}}
        fixed, d = auto1m.rewrite_dangling_citations("[C0007] fact", prov)
        self.assertEqual(fixed, "[C0007] fact")
        self.assertEqual(d, [])

    def test_fabricated_tag_rewritten_to_nearest(self):
        prov = {"C0007": {}, "C0010": {}}
        fixed, d = auto1m.rewrite_dangling_citations("[C0126] hallucinated", prov)
        self.assertEqual(d, ["C0126"])
        self.assertNotIn("C0126", fixed)
        self.assertIn(fixed, ("[C0010] hallucinated", "[C0007] hallucinated"))
        # 126 is nearer to 10 than 7 -> C0010
        self.assertEqual(fixed, "[C0010] hallucinated")

    def test_no_tags(self):
        fixed, d = auto1m.rewrite_dangling_citations("plain text", {"C0001": {}})
        self.assertEqual((fixed, d), ("plain text", []))


if __name__ == "__main__":
    unittest.main(verbosity=2)
