# fork auto-select timer

Goal ID: goal_a9c13f3592f4
Goal slug: fork-auto-select-timer

## Description
Standing mechanism for Chris's 3-minute rule: when the fork-unblind skill presents a top repo pick and Chris doesn't respond within 3 minutes, a one-shot runonce timer (stable id `fork-autoselect`) auto-selects the most emergent pick and proceeds with fork+clone+unblind. If he replies in time, the timer is removed and his reply rules. Owns all fork-autoselect timers.
