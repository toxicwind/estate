# Functional Test Checklist (Shaping Lab)

Run this after each task that can affect runtime behavior.

## Setup

1. Install dependencies if needed: `npm install`
2. Start dev server: `npm run dev`
3. Open app in browser and confirm page renders.

## Smoke Flow

1. Confirm canvas appears and continuously updates.
2. Confirm control buttons are visible (`Reward`, `Pause`, `Reset`, `Settings`).
3. Click `Pause` and confirm movement stops; click `Resume` and confirm movement resumes.
4. Click `Reward` and confirm reward visual feedback appears.
5. Open `Settings`, change one value, close settings, and confirm app remains responsive.
6. Click `Reset` and confirm agent returns near canvas center.
7. Open `About`, then close it, and confirm no UI lock.

## Quality Gates

1. `npm run build`
2. `npm run lint` (record baseline failures separately from new failures)

## Report

Record:
- commands run
- pass/fail per step
- regressions found
- retest outcome after fixes
