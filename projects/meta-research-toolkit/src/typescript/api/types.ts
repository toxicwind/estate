// Canonical report shapes for the meta-research toolkit.
// These mirror the Python lane (src/python/refusal_geometry/models.py and
// src/python/lottery/ev_calculator.py) so TS consumers can typecheck the
// JSON produced by either side.

/** Result of a refusal-geometry analysis run for one model. */
export interface RefusalGeometryReport {
  /** Model identifier the report was produced for. */
  model: string;
  /**
   * 0..1 routing-failure score: how often a meta-analytical query that
   * admits no admissible answer is routed to the safety-refusal direction
   * instead of the (nearly orthogonal) recognition signal.
   */
  routingFailureScore: number;
  /** True when steering/ablation shows the refusal subspace is bypassable. */
  isPorous: boolean;
  /**
   * Estimated orthogonality (0..1) between the recognition signal and the
   * refusal direction. Near 1 = nearly orthogonal (arXiv:2608.29109).
   */
  recognitionOrthogonalityEstimate: number;
  /** Recommended handling for the queried model version. */
  recommendation: "answer" | "refuse" | "escalate";
}

/** Result of a lottery scratch-off EV audit. */
export interface LotteryAudit {
  /** Game name as published by the lottery commission. */
  gameName: string;
  /** Ticket price in the game currency base unit. */
  price: number;
  /** EV at launch, from the published prize structure. */
  baselineEV: number;
  /** Current EV: baseline adjusted for remaining top prizes vs implied remaining tickets. */
  dynamicEV: number;
  /** (price - dynamicEV) / price. Negative = player edge. */
  houseEdge: number;
  /** Verdict based on dynamicEV relative to price. */
  verdict: "positive" | "neutral" | "negative";
}
