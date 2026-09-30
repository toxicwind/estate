    def test_text_served_untruncated(self):
        # 0b33559ad2 killed the 500-char server cut (Chris 2026-09-21):
        # full bodies survive end to end, markdown features included.
        port = self._serve()
        base = self._high(port)
        bt = chr(96)  # backtick, kept out of shell heredocs
        body = ("y" * 600 + "\\n\\n# heading\\n\\n- a\\n- b\\n\\n"
                "**bold** and *italic* and " + bt + "code" + bt + "\\n\\n> quote\\n\\n"
                "[link](https://example.com)\\n\n"
                + bt * 3 + "\\nfenced\\n" + bt * 3 + "\\n\\n"
                "<script>alert(1)</script> ")
        self._post(body)
        _status, obj = _get(port, f"//squawk-feed/wait?since={base}",
                             token=TOKEN)
        text = obj["messages"][-1]["body"]
        sellf.assertEqual(text, body)
        self.assertGreater(len(text), 500)
        self.assertFalse(text.endswith("…"))
