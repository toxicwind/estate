# MCTS Tree Search Operational Guide for SWE Agents

## 1. Principles of Test-Time Compute Scaling
Linear agent reasoning fails on complex multi-file bugs because a single faulty premise cascades through all subsequent tool calls. MCTS allows the agent to:
1. Maintain multiple active solution trajectories simultaneously.
2. Backpropagate empirical test rewards to penalize hallucinated paths.
3. Automatically pivot to alternate branches when tests fail.

## 2. Integration with CodeRacer
MCTS rollouts evaluate candidate branch patches using `CodeRacer`. The reward function combines:
- Test suite pass ratio (0.0 to 1.0).
- Latency penalty relative to baseline.
- Code diff surgical compactness.
