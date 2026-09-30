#!/usr/bin/env node
// The Hermes skill package (.hermes/skills/) is generated from skills/ by
// scripts/build-hermes-skills.js. These tests fail if the committed copies are
// stale (ruleset drift) or if a description breaks Hermes's one-line <60 rule.

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const { NAMES, render, outPath, HERMES_DESCRIPTIONS } = require('../scripts/build-hermes-skills');
const { sourceBody } = require('../scripts/build-openclaw-skills');

for (const name of NAMES) {
  test(`${name}: committed Hermes skill matches the generator`, () => {
    const onDisk = fs.readFileSync(outPath(name), 'utf8').replace(/\r\n/g, '\n');
    assert.equal(onDisk, render(name), 'stale — run: node scripts/build-hermes-skills.js');
  });

  test(`${name}: body is the canonical skills/${name} body, verbatim`, () => {
    const onDisk = fs.readFileSync(outPath(name), 'utf8').replace(/\r\n/g, '\n');
    assert.ok(onDisk.endsWith(sourceBody(name)), 'body drifted from skills/' + name);
  });

  test(`${name}: description is one line under 60 chars`, () => {
    const d = HERMES_DESCRIPTIONS[name];
    assert.ok(d.length <= 60 && !d.includes('\n'), 'description too long or multiline');
  });
}
