#!/usr/bin/env node
// skills/honey-chat/COMPACT.md is pasted verbatim into web custom-instruction
// fields (ChatGPT enforces 1,500 characters). Guard the limit so an edit can't
// silently make the file unpasteable. (#56)

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');

test('compact chat edition fits a 1,500-character field', () => {
  const text = fs.readFileSync(path.join(__dirname, '..', 'skills', 'honey-chat', 'COMPACT.md'), 'utf8').trim();
  assert.ok(text.length <= 1500, `COMPACT.md is ${text.length} chars — must stay ≤ 1500`);
});
