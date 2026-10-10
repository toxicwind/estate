#!/bin/bash
# example: violations of the estate conventions. Do not copy.
# (Written without strict mode on purpose -- this file is a negative example.)

function foo {
  # narrates the line below it -- violation of R-1001
  x=$1
  # unquoted expansion -- violation of R-601
  echo $x
  # bare arithmetic -- violation of R-901
  let x++
  # unnecessary semicolon -- violation of R-502
  echo done;
}

# non-ASCII section divider -- violation of R-1301
# ==============================================

foo "hello world"
