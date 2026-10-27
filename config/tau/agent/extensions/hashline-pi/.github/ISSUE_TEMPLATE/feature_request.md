---
name: Feature request
about: Suggest a change to the patch language, extension behavior, or docs
title: '[feature] '
labels: enhancement
---

## Problem

What are you trying to do that hashline-pi doesn't currently let you
do (or lets you do only awkwardly)? Include the concrete scenario, not
just the abstract capability.

## Proposal

What would the smallest possible change to the tool, grammar, or docs
look like? If this touches the grammar, remember the vendored core
tracks the upstream
[`@oh-my-pi/hashline`](https://github.com/can1357/oh-my-pi/tree/main/packages/hashline)
package — grammar-level changes should ideally land upstream first.

## Alternatives considered

Any workarounds you've already tried or non-obvious alternatives you
rejected.

## Backward compatibility

Would this change break existing patches, snapshot-store consumers,
or extension embedders? If yes, describe the migration story.
