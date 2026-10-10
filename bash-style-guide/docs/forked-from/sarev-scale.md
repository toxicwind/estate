# sarev/scale

Source: https://github.com/sarev/scale

## Rule adopted

- Why-not-what comment standard. The restatement filter ("increment the
  counter") is rejected.

## Quoted text from upstream

> A comment that just narrates the line below it ("increment the counter")
> is rejected.

> Existing documentation is an input, not an obstacle: SCALE reads what is
> already there and updates it, so hand-written rationale ("we retry
> because the vendor API is flaky") is carried forward rather than
> flattened.

> The model never re-emits your code, so executable code, indentation,
> blank lines, and comments it was not asked to touch are preserved
> byte-for-byte.
