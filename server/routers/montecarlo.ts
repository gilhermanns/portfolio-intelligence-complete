import { z } from "zod";
import { router, protectedProcedure } from "../trpc";
import { db } from "../db";
 
const ASSET_PARAMS: Record<string, { mu: number; sigma: number }> = {
  equity:    { mu: 0.098, sigma: 0.170 },
  bond:      { mu: 0.035, sigma: 0.055 },
  commodity: { mu: 0.045, sigma: 0.180 },
  crypto:    { mu: 0.350, sigma: 0.700 },
  fx:        { mu: 0.020, sigma: 0.070 },
  other:     { mu: 0.060, sigma: 0.120 },
};
 
const ASSET_CLASSES = ["equity", "bond", "commodity", "crypto", "fx", "other"] as const;
 
const CORRELATION_MATRIX = [
  [ 1.00, -0.20,  0.30,  0.40,  0.10,  0.50],
  [-0.20,  1.00,  0.00, -0.10,  0.20,  0.10],
  [ 0.30,  0.00,  1.00,  0.20,  0.30,  0.20],
  [ 0.40, -0.10,  0.20,  1.00,  0.10,  0.30],
  [ 0.10,  0.20,  0.30,  0.10,  1.00,  0.10],
  [ 0.50,  0.10,  0.20,  0.30,  0.10,  1.00],
];
 
function cholesky(matrix: number[][]): number[][] {
  const n = matrix.length;
  const L: number[][] = Array.from({ length: n }, () => new Array(n).fill(0));
  for (let i = 0; i < n; i++) {
    for (let j = 0; j <= i; j++) {
      let sum = 0;
      for (let k = 0; k < j; k++) sum += L[i][k] * L[j][k];
      L[i][j] = i === j
        ? Math.sqrt(Math.max(0, matrix[i][i] - sum))
        : L[j][j] !== 0 ? (matrix[i][j] - sum) / L[j][j] : 0;
    }
  }
  return L;
}
 
function boxMuller(): [number, number] {
  const u1 = Math.max(1e-10, Math.random());
  const u2 = Math.random();
  const r = Math.sqrt(-2 * Math.log(u1));
  const theta = 2 * Math.PI * u2;
  return [r * Math.cos(theta), r * Math.sin(theta)];
}
 
function randNormals(n: number): number[] {
  const out: number[] = [];
  for (let i = 0; i < Math.ceil(n / 2); i++) {
    const [a, b] = boxMuller();
    out.push(a, b);
  }
  return out.slice(0, n);
}
 
function correlate(L: number[][], z: number[]): number[] {
  return L.map((row) => row.reduce((s, lij, k) => s + lij * z[k], 0));
}
 
function percentile(sorted: number[], p: number): number {
  return sorted[Math.min(Math.floor(p * sorted.length), sorted.length - 1)];
}
 
function runSimulation(params: {
  assetBuckets: { assetClass: string; value: number }[];
  timeHorizonMonths: number;
  numSimulations: number;
}) {
  const { assetBuckets, timeHorizonMonths, numSimulations } = params;
  const dt = 1 / 12;
  const steps = timeHorizonMonths;
  const totalValue = assetBuckets.reduce((s, b) => s + b.value, 0);
 
  const buckets = assetBuckets.map((b) => {
    const ac = b.assetClass in ASSET_PARAMS ? b.assetClass : "other";
    const { mu, sigma } = ASSET_PARAMS[ac];
    return { value: b.value, mu, sigma, classIdx: ASSET_CLASSES.indexOf(ac as any) };
  });
 
  const L = cholesky(CORRELATION_MATRIX);
  const allFinalValues: number[] = [];
  const samplePaths: number[][] = [];
  const sampleStep = Math.max(1, Math.floor(numSimulations / 40));
  const columns: number[][] = Array.from({ length: steps + 1 }, () => []);
 
  for (let sim = 0; sim < numSimulations; sim++) {
    const bucketValues = buckets.map((b) => b.value);
    const path: number[] = [totalValue];
 
    for (let t = 0; t < steps; t++) {
      const eps = correlate(L, randNormals(6));
      for (let bi = 0; bi < buckets.length; bi++) {
        const { mu, sigma, classIdx } = buckets[bi];
        bucketValues[bi] *= Math.exp((mu - 0.5*sigma*sigma)*dt + sigma*Math.sqrt(dt)*eps[classIdx]);
      }
      const pv = bucketValues.reduce((s, v) => s + v, 0);
      path.push(pv);
      columns[t + 1].push(pv);
    }
 
    columns[0].push(totalValue);
    allFinalValues.push(path[steps]);
    if (sim % sampleStep === 0) samplePaths.push(path);
  }
 
  const sortedFinals = [...allFinalValues].sort((a, b) => a - b);
 
  const percentilePaths = {
    p5:  columns.map((col) => percentile([...col].sort((a,b)=>a-b), 0.05)),
    p25: columns.map((col) => percentile([...col].sort((a,b)=>a-b), 0.25)),
    p50: columns.map((col) => percentile([...col].sort((a,b)=>a-b), 0.50)),
    p75: columns.map((col) => percentile([...col].sort((a,b)=>a-b), 0.75)),
    p95: columns.map((col) => percentile([...col].sort((a,b)=>a-b), 0.95)),
  };
 
  const var95  = percentile(sortedFinals, 0.05);
  const var99  = percentile(sortedFinals, 0.01);
  const n95    = Math.max(1, Math.floor(0.05 * numSimulations));
  const n99    = Math.max(1, Math.floor(0.01 * numSimulations));
  const cvar95 = sortedFinals.slice(0, n95).reduce((s,v)=>s+v,0) / n95;
  const cvar99 = sortedFinals.slice(0, n99).reduce((s,v)=>s+v,0) / n99;
  const mean   = sortedFinals.reduce((s,v)=>s+v,0) / numSimulations;
  const medianFinal = percentile(sortedFinals, 0.5);
  const annualizedReturn = (Math.pow(medianFinal / totalValue, 12 / steps) - 1) * 100;
 
  const binCount = 40;
  const histMin = sortedFinals[0], histMax = sortedFinals[sortedFinals.length-1];
  const binWidth = (histMax - histMin) / binCount;
  const histCounts = new Array(binCount).fill(0);
  for (const v of sortedFinals) histCounts[Math.min(binCount-1, Math.floor((v-histMin)/binWidth))]++;
 
  return {
    initialValue: totalValue,
    samplePaths: samplePaths.slice(0, 40),
    percentilePaths,
    histogram: { min: histMin, max: histMax, binWidth, counts: histCounts, lossThreshold: totalValue },
    statistics: {
      initialValue:     parseFloat(totalValue.toFixed(2)),
      median:           parseFloat(medianFinal.toFixed(2)),
      mean:             parseFloat(mean.toFixed(2)),
      var95:            parseFloat(var95.toFixed(2)),
      var99:            parseFloat(var99.toFixed(2)),
      cvar95:           parseFloat(cvar95.toFixed(2)),
      cvar99:           parseFloat(cvar99.toFixed(2)),
      probLoss:         parseFloat((sortedFinals.filter(v=>v<totalValue).length/numSimulations*100).toFixed(1)),
      probGain20:       parseFloat((sortedFinals.filter(v=>v>totalValue*1.2).length/numSimulations*100).toFixed(1)),
      probDouble:       parseFloat((sortedFinals.filter(v=>v>totalValue*2).length/numSimulations*100).toFixed(1)),
      bestCase:         parseFloat(sortedFinals[sortedFinals.length-1].toFixed(2)),
      worstCase:        parseFloat(sortedFinals[0].toFixed(2)),
      annualizedReturn: parseFloat(annualizedReturn.toFixed(2)),
      lossAtVar95:      parseFloat((totalValue - var95).toFixed(2)),
      lossAtCvar95:     parseFloat((totalValue - cvar95).toFixed(2)),
    },
    params: { timeHorizonMonths, numSimulations },
  };
}
 
export const montecarloRouter = router({
  run: protectedProcedure
    .input(z.object({
      portfolioId: z.number(),
      timeHorizonMonths: z.number().min(1).max(360).default(60),
      numSimulations: z.number().min(100).max(10000).default(1000),
    }))
    .mutation(({ input }) => {
      const holdings = db.getHoldingsByPortfolioId(input.portfolioId);
      if (holdings.length === 0) throw new Error("No holdings found");
      const bucketMap: Record<string, number> = {};
      for (const h of holdings) {
        const ac = h.assetClass in ASSET_PARAMS ? h.assetClass : "other";
        bucketMap[ac] = (bucketMap[ac] ?? 0) + h.quantity * h.purchasePrice;
      }
      return runSimulation({
        assetBuckets: Object.entries(bucketMap).map(([assetClass, value]) => ({ assetClass, value })),
        timeHorizonMonths: input.timeHorizonMonths,
        numSimulations: input.numSimulations,
      });
    }),
  runCustom: protectedProcedure
    .input(z.object({
      assetBuckets: z.array(z.object({ assetClass: z.string(), value: z.number().positive() })),
      timeHorizonMonths: z.number().min(1).max(360).default(60),
      numSimulations: z.number().min(100).max(10000).default(1000),
    }))
    .mutation(({ input }) => runSimulation(input)),
});
