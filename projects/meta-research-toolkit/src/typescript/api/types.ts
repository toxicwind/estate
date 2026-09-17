export interface RefusalGeometryReport {
  model: string;
  routingFailureScore: number;
  isPorous: boolean;
  recognitionOrthogonalityEstimate: number;
  recommendation: "answer" | "refuse" | "escalate";
}

export interface LotteryAudit {
  gameName: string;
  price: number;
  baselineEV: number;
  dynamicEV: number;
  houseEdge: number;
  verdict: "positive" | "neutral" | "negative";
}
