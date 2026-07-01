interface HistogramData{min:number;max:number;binWidth:number;counts:number[];lossThreshold:number;}
interface HistogramChartProps{data:HistogramData;width?:number;height?:number;}
const PAD={top:16,right:16,bottom:36,left:56};
function fmt(v:number):string{if(v>=1_000_000)return`$${(v/1_000_000).toFixed(1)}M`;if(v>=1_000)return`$${(v/1_000).toFixed(0)}K`;return`$${v.toFixed(0)}`;}
export function HistogramChart({data,width=640,height=220}:HistogramChartProps){
  const{min,binWidth,counts,lossThreshold}=data;
  const plotW=width-PAD.left-PAD.right,plotH=height-PAD.top-PAD.bottom,maxCount=Math.max(...counts,1),barW=plotW/counts.length;
  const xScale=(bin:number)=>PAD.left+bin*barW,yScale=(count:number)=>PAD.top+plotH-(count/maxCount)*plotH,binValue=(bin:number)=>min+bin*binWidth;
  const labelStep=Math.max(1,Math.floor(counts.length/6)),xLabels=counts.map((_,i)=>i).filter((i)=>i%labelStep===0||i===counts.length-1);
  const yTicks=[0,0.25,0.5,0.75,1].map((p)=>({count:Math.round(p*maxCount),y:PAD.top+plotH-p*plotH}));
  return(
    <div className="w-full overflow-x-auto">
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" style={{maxWidth:width,display:"block"}}>
        {yTicks.map(({y})=><line key={y} x1={PAD.left} x2={width-PAD.right} y1={y} y2={y} stroke="hsl(var(--border))" strokeWidth="0.5" strokeDasharray="4 3"/>)}
        {counts.map((count,bin)=>{const x=xScale(bin),y=yScale(count),bH=plotH-(y-PAD.top),value=binValue(bin);return<rect key={bin} x={x+0.5} y={y} width={Math.max(0,barW-1)} height={bH} fill={value+binWidth<lossThreshold?"rgba(239,68,68,0.55)":value>=lossThreshold?"rgba(74,222,128,0.55)":"hsl(var(--accent))"} rx="1"/>;})}
        {lossThreshold>=data.min&&lossThreshold<=data.max&&(()=>{const thX=PAD.left+((lossThreshold-min)/(data.max-min))*plotW;return<g><line x1={thX} x2={thX} y1={PAD.top} y2={height-PAD.bottom} stroke="hsl(var(--muted-foreground))" strokeWidth="1.5" strokeDasharray="4 3"/><text x={thX+4} y={PAD.top+12} fontSize="9" fill="hsl(var(--muted-foreground))">Break-even</text></g>})()}
        {xLabels.map((bin)=><text key={bin} x={xScale(bin)+barW/2} y={height-8} fontSize="9" fill="hsl(var(--muted-foreground))" textAnchor="middle">{fmt(binValue(bin))}</text>)}
        {yTicks.map(({count,y})=><text key={count} x={PAD.left-4} y={y+3} fontSize="9" fill="hsl(var(--muted-foreground))" textAnchor="end">{count}</text>)}
        <line x1={PAD.left} x2={PAD.left} y1={PAD.top} y2={height-PAD.bottom} stroke="hsl(var(--border))" strokeWidth="1"/>
        <line x1={PAD.left} x2={width-PAD.right} y1={height-PAD.bottom} y2={height-PAD.bottom} stroke="hsl(var(--border))" strokeWidth="1"/>
        <g transform={`translate(${width-PAD.right-120},${PAD.top+4})`}><rect x="0" y="0" width="12" height="10" rx="2" fill="rgba(239,68,68,0.55)"/><text x="16" y="9" fontSize="9" fill="hsl(var(--muted-foreground))">Loss</text><rect x="50" y="0" width="12" height="10" rx="2" fill="rgba(74,222,128,0.55)"/><text x="66" y="9" fontSize="9" fill="hsl(var(--muted-foreground))">Gain</text></g>
      </svg>
    </div>
  );
}
