interface PercentilePaths { p5:number[];p25:number[];p50:number[];p75:number[];p95:number[]; }
interface SimulationChartProps { samplePaths:number[][];percentilePaths:PercentilePaths;initialValue:number;timeHorizonMonths:number;width?:number;height?:number; }
const PAD={top:20,right:24,bottom:44,left:72};
function fmt(v:number):string{if(v>=1_000_000)return`$${(v/1_000_000).toFixed(1)}M`;if(v>=1_000)return`$${(v/1_000).toFixed(0)}K`;return`$${v.toFixed(0)}`;}
export function SimulationChart({samplePaths,percentilePaths,initialValue,timeHorizonMonths,width=760,height=340}:SimulationChartProps){
  const plotW=width-PAD.left-PAD.right,plotH=height-PAD.top-PAD.bottom,steps=timeHorizonMonths;
  const allVals=[...percentilePaths.p5,...percentilePaths.p95];
  const yMin=Math.min(...allVals)*0.95,yMax=Math.max(...allVals)*1.05;
  const xScale=(t:number)=>PAD.left+(t/steps)*plotW;
  const yScale=(v:number)=>PAD.top+plotH-((v-yMin)/(yMax-yMin))*plotH;
  const toPath=(values:number[])=>values.map((v,t)=>`${t===0?"M":"L"}${xScale(t).toFixed(1)},${yScale(v).toFixed(1)}`).join(" ");
  const toBand=(upper:number[],lower:number[])=>{
    const fwd=upper.map((v,t)=>`${xScale(t).toFixed(1)},${yScale(v).toFixed(1)}`).join(" ");
    const back=lower.map((v,t)=>`${xScale(lower.length-1-t).toFixed(1)},${yScale(lower[lower.length-1-t]).toFixed(1)}`).join(" ");
    return`M ${fwd} L ${back} Z`;
  };
  const xLabels:any[]=[]; for(let t=0;t<=steps;t+=12)xLabels.push({t,label:t===0?"Now":`Y${t/12}`});
  const yLabels=Array.from({length:5},(_,i)=>({v:yMin+((yMax-yMin)*i)/4,y:yScale(yMin+((yMax-yMin)*i)/4)}));
  const initialY=yScale(initialValue);
  return(
    <div className="w-full overflow-x-auto">
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" style={{maxWidth:width,display:"block"}}>
        {yLabels.map(({y},i)=><line key={i} x1={PAD.left} x2={width-PAD.right} y1={y} y2={y} stroke="hsl(var(--border))" strokeWidth="0.5" strokeDasharray="4 3"/>)}
        <line x1={PAD.left} x2={width-PAD.right} y1={initialY} y2={initialY} stroke="hsl(var(--muted-foreground))" strokeWidth="1" strokeDasharray="6 3"/>
        <text x={PAD.left+4} y={initialY-5} fontSize="9" fill="hsl(var(--muted-foreground))">Initial: {fmt(initialValue)}</text>
        {samplePaths.map((p,i)=><path key={i} d={toPath(p)} fill="none" stroke="hsl(var(--accent))" strokeWidth="0.6" opacity="0.12"/>)}
        <path d={toBand(percentilePaths.p95,percentilePaths.p5)} fill="hsl(var(--accent))" opacity="0.07"/>
        <path d={toBand(percentilePaths.p75,percentilePaths.p25)} fill="hsl(var(--accent))" opacity="0.14"/>
        <path d={toPath(percentilePaths.p50)} fill="none" stroke="hsl(var(--accent))" strokeWidth="2.5" strokeLinecap="round"/>
        <path d={toPath(percentilePaths.p5)} fill="none" stroke="hsl(var(--accent))" strokeWidth="1" opacity="0.4" strokeDasharray="3 2"/>
        <path d={toPath(percentilePaths.p95)} fill="none" stroke="hsl(var(--accent))" strokeWidth="1" opacity="0.4" strokeDasharray="3 2"/>
        {yLabels.map(({v,y},i)=><text key={i} x={PAD.left-6} y={y+4} fontSize="10" fill="hsl(var(--muted-foreground))" textAnchor="end">{fmt(v)}</text>)}
        {xLabels.map(({t,label}:any)=><text key={t} x={xScale(t)} y={height-10} fontSize="10" fill="hsl(var(--muted-foreground))" textAnchor="middle">{label}</text>)}
        <g transform={`translate(${PAD.left+8},${PAD.top+8})`}>
          <rect width="100" height="52" rx="4" fill="hsl(var(--card))" opacity="0.85"/>
          <rect x="8" y="10" width="12" height="3" rx="1" fill="hsl(var(--accent))"/>
          <text x="24" y="14" fontSize="9" fill="hsl(var(--muted-foreground))">Median</text>
          <rect x="8" y="24" width="12" height="6" rx="1" fill="hsl(var(--accent))" opacity="0.2"/>
          <text x="24" y="29" fontSize="9" fill="hsl(var(--muted-foreground))">25–75%</text>
          <rect x="8" y="38" width="12" height="6" rx="1" fill="hsl(var(--accent))" opacity="0.1"/>
          <text x="24" y="43" fontSize="9" fill="hsl(var(--muted-foreground))">5–95%</text>
        </g>
        <line x1={PAD.left} x2={PAD.left} y1={PAD.top} y2={height-PAD.bottom} stroke="hsl(var(--border))" strokeWidth="1"/>
       <line x1={PAD.left} x2={width-PAD.right} y1={height-PAD.bottom} y2={height-PAD.bottom} stroke="hsl(var(--border))" strokeWidth="1"/>
      </svg>
    </div>
  );
}
