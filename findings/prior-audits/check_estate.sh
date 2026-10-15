#!/bin/bash
/usr/bin/git -C /home/toxic/estate branch -vv
/usr/bin/git -C /home/toxic/estate rev-list --left-right --count HEAD...@{u} 2>/dev/null || echo "no upstream"