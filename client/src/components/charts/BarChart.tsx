interface Bar { label: string; value: number; color?: string; }
export function HBarChart({ data, formatValue=(v:number)=>String(v), maxValue }: { data: Bar[]; formatValue?: (v:number)=>string; maxValue?: number }) {
  const max = maxValue ?? Math.max(...data.map((d)=>d.value), 1);
  return (
    <div className="space-y-3">
      {data.map((bar)=>(
        <div key={bar.label}>
          <div className="flex justify-between text-xs mb-1"><span className="text-muted-foreground truncate max-w-[60%]">{bar.label}</span><span className="text-foreground font-medium">{formatValue(bar.value)}</span></div>
          <div className="h-2 bg-muted rounded-full overflow-hidden"><div className="h-full rounded-full transition-all duration-500" style={{width:`${Math.min((bar.value/max)*100,100)}%`,background:bar.color??"hsl(var(--accent))"}}/></div>
        </div>
      ))}
    </div>
  );
}
export function MiniSparkline({ values, width=80, height=28, color }: { values: number[]; width?: number; height?: number; color?: string }) {
  if (values.length < 2) return null;
  const min=Math.min(...values),max=Math.max(...values),range=max-min||1;
  const pts=values.map((v,i)=>`${(i/(values.length-1))*width},${height-((v-min)/range)*(height-4)-2}`);
  const positive=values[values.length-1]>=values[0];
  return <svg width={width} height={height}><polyline points={pts.join(" ")} fill="none" stroke={color??(positive?"#4ade80":"#f87171")} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>;
}
