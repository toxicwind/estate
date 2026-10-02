# Runtime Checklist

Run these checks while app is served locally.

## Server and Load

1. Start dev server with explicit host/port.
2. Confirm HTTP 200 on root page.
3. Confirm main script and CSS assets load.

## Core Interactions

1. Confirm control buttons render (`Reward`, `Pause`, `Reset`, `Settings`, `Docs`, `About`).
2. Open and close Settings.
3. Open and close Docs.
4. Open and close About.
5. Toggle Pause/Resume and verify simulation state changes.
6. Press Reward and verify feedback appears.
7. Press Reset and verify agent/session reset behavior.

## Responsive Spot Check

1. Confirm no obvious overlap at desktop width.
2. Confirm no obvious overlap at mobile width (~390px) if viewport tooling is available.

## Exit Criteria

- Fail if any core control is broken, unresponsive, or throws runtime errors.
- Fail if quality gate regresses beyond known baseline.
