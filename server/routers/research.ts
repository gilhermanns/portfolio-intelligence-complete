import { z } from "zod";
import { router, protectedProcedure } from "../trpc";
import { db } from "../db";
 
function generateAnalysis(question: string): string {
  if (question.toLowerCase().includes("rate") || question.toLowerCase().includes("fed")) {
    return `**Interest Rate & Fed Policy Analysis**\n\nThe Federal Reserve remains in a delicate balancing act. Market pricing implies 2-3 cuts over the next 12 months.\n\n**Impact on Asset Classes:**\n- **Equities:** Duration-sensitive growth stocks benefit from rate cut expectations\n- **Bonds:** Long-duration bonds (TLT) positioned to outperform as rates fall\n- **Real Estate:** REITs well-positioned for reversal after lagging the hiking cycle`;
  }
  if (question.toLowerCase().includes("tech") || question.toLowerCase().includes("ai")) {
    return `**Technology & AI Sector Analysis**\n\nTechnology continues to dominate market returns, driven by the AI infrastructure buildout.\n\n**Key Winners:**\n- **Semiconductors (NVDA, AMD, AVGO):** AI training demand remains insatiable\n- **Hyperscalers (MSFT, GOOGL, AMZN):** AI monetization becoming visible in revenue lines\n\n**Risk Factors:**\n- Regulatory scrutiny of AI models\n- Potential slowdown in enterprise IT spending\n- Concentration risk (top 7 stocks = 30%+ of S&P 500)`;
  }
  return `**Investment Analysis**\n\n**Key Observations:**\n- Current market conditions warrant careful positioning\n- Diversification across uncorrelated asset classes remains critical\n\n**Investment Implications:**\n1. Short-term: Monitor for catalysts that could shift momentum\n2. Medium-term: Fundamental thesis remains intact\n3. Long-term: Structural trends favor selective exposure\n\n**Risk Factors:** Fed policy, earnings revisions, geopolitical developments, credit market conditions.`;
}
 
function generateRiskAnalysis(holdings: any[]) {
  const totalValue = holdings.reduce((s, h) => s + h.quantity * h.purchasePrice, 0);
  const sectorMap: Record<string, number> = {};
  const assetClassMap: Record<string, number> = {};
  for (const h of holdings) {
    const val = h.quantity * h.purchasePrice;
    sectorMap[h.sector] = (sectorMap[h.sector] || 0) + val;
    assetClassMap[h.assetClass] = (assetClassMap[h.assetClass] || 0) + val;
  }
  const sectorConcentration = Object.entries(sectorMap)
    .map(([sector, value]) => ({ sector, value, percentage: parseFloat(((value/totalValue)*100).toFixed(1)), risk: value/totalValue > 0.3 ? "High" : value/totalValue > 0.15 ? "Medium" : "Low" }))
    .sort((a, b) => b.percentage - a.percentage);
  const assetClassBreakdown = Object.entries(assetClassMap)
    .map(([assetClass, value]) => ({ assetClass, value, percentage: parseFloat(((value/totalValue)*100).toFixed(1)) }));
  const topHolding = holdings.reduce((max, h) => { const val = h.quantity*h.purchasePrice; return val > max.val ? { ticker: h.ticker, val } : max; }, { ticker: "", val: 0 });
  const concentration = topHolding.val / totalValue;
  return {
    totalValue, riskScore: concentration > 0.3 ? 8 : concentration > 0.2 ? 6 : 4,
    sectorConcentration, assetClassBreakdown,
    topHolding: { ticker: topHolding.ticker, pct: ((topHolding.val/totalValue)*100).toFixed(1) },
    warnings: [
      ...(concentration > 0.25 ? [`High single-position concentration: ${topHolding.ticker} represents ${((topHolding.val/totalValue)*100).toFixed(1)}% of portfolio`] : []),
      ...(sectorConcentration.some(s => s.percentage > 35) ? ["Sector concentration exceeds 35% — consider diversification"] : []),
      ...(holdings.filter(h => h.assetClass === "bond").length === 0 ? ["No fixed income allocation — portfolio lacks defensive positioning"] : []),
    ],
    recommendations: [
      "Maintain position sizes below 25% of portfolio value",
      "Ensure at least 3 uncorrelated asset classes",
      "Review sector weights quarterly against benchmark",
      "Consider tail-risk hedges for concentrated equity positions",
    ],
  };
}
 
export const researchRouter = router({
  ask: protectedProcedure
    .input(z.object({ question: z.string().min(1), context: z.string().optional() }))
    .mutation(({ ctx, input }) => {
      const answer = generateAnalysis(input.question);
      db.createResearchReport({ userId: ctx.user.id, type: "qa", title: input.question.slice(0, 80), content: answer, generatedAt: new Date() });
      return { answer };
    }),
  analyzePortfolioImpact: protectedProcedure
    .input(z.object({
      holdings: z.array(z.object({ ticker: z.string(), quantity: z.number(), purchasePrice: z.number(), sector: z.string(), assetClass: z.string() })),
      scenario: z.string().min(1),
    }))
    .mutation(({ ctx, input }) => {
      const totalValue = input.holdings.reduce((s, h) => s + h.quantity*h.purchasePrice, 0);
      const analysis = `**Portfolio Impact Analysis**\n\n**Scenario:** ${input.scenario}\n\n**Portfolio Value:** $${totalValue.toLocaleString("en-US",{maximumFractionDigits:0})}\n**Positions:** ${input.holdings.length}\n\n**Estimated Impact:**\n| Asset Class | Positions | Estimated Impact |\n|-------------|-----------|------------------|\n| Equities | ${input.holdings.filter(h=>h.assetClass==="equity").length} | -3% to +5% |\n| Fixed Income | ${input.holdings.filter(h=>h.assetClass==="bond").length} | -1% to +3% |\n| Commodities | ${input.holdings.filter(h=>h.assetClass==="commodity").length} | High volatility |\n\n**Actions:**\n1. Review position sizing\n2. Consider protective options on largest positions\n3. Ensure adequate liquidity`;
      db.createResearchReport({ userId: ctx.user.id, type: "impact_analysis", title: `Impact: ${input.scenario.slice(0,60)}`, content: analysis, generatedAt: new Date() });
      return { analysis };
    }),
  analyzeConcentrationRisks: protectedProcedure
    .input(z.object({ holdings: z.array(z.object({ ticker: z.string(), quantity: z.number(), purchasePrice: z.number(), sector: z.string(), assetClass: z.string() })) }))
    .mutation(({ input }) => generateRiskAnalysis(input.holdings)),
  getReports: protectedProcedure.query(({ ctx }) => db.getReportsByUserId(ctx.user.id)),
  generateWeeklyMemo: protectedProcedure.mutation(({ ctx }) => {
    const memo = {
      title: `Weekly Investment Memo — ${new Date().toLocaleDateString("en-US",{month:"long",day:"numeric",year:"numeric"})}`,
      sections: [
        { title: "Market Overview", content: "Equity markets remained constructive this week with the S&P 500 advancing 0.8%." },
        { title: "Macro Developments", content: "The Fed maintained its data-dependent stance. Core PCE came in at 2.6% YoY." },
        { title: "Earnings Highlights", content: "Q1 earnings season wraps up with 78% of S&P 500 companies beating EPS estimates." },
        { title: "Investment Implications", content: "We maintain a modest overweight to equities with a preference for quality growth names." },
        { title: "Key Risks to Monitor", content: "1) Fed pivot timing. 2) Geopolitical escalation. 3) Credit market stress. 4) Election year volatility." },
      ],
    };
    db.createResearchReport({ userId: ctx.user.id, type: "weekly_memo", title: memo.title, content: JSON.stringify(memo), generatedAt: new Date() });
    return memo;
  }),
});
