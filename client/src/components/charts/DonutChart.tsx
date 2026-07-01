interface Slice { label: string; value: number; color: string; }
interface DonutChartProps { data: Slice[]; size?: number; thickness?: number; centerLabel?: string; centerSubLabel?: string; }
export function DonutChart({ data, size=180, thickness=32, centerLabel, centerSubLabel }: DonutChartProps) {
  const total = data.reduce((s,d)=>s+d.value,0);
  if (total === 0) return null;
  const cx=size/2, cy=size/2, r=(size-thickness)/2, circumference=2*Math.PI*r;
  let cumPct=0;
  const slices=data.map((d)=>{ const pct=d.value/total; const offset=cumPct*circumference; const dashLen=pct*circumference-2; cumPct+=pct; return {...d,offset,dashLen}; });
  return (
    <div className="flex items-center gap-6">
      <svg width={size} height={size} className="flex-shrink-0" style={{transform:"rotate(-90deg)"}}>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="hsl(var(--muted))" strokeWidth={thickness} />
        {slices.map((s,i)=><circle key={i} cx={cx} cy={cy} r={r} fill="none" stroke={s.color} strokeWidth={thickness} strokeDasharray={`${Math.max(0,s.dashLen)} ${circumference}`} strokeDashoffset={-s.offset} strokeLinecap="butt" />)}
        {centerLabel && <g style={{transform:`rotate(90deg)`,transformOrigin:`${cx}px ${cy}px`}}><text x={cx} y={cy-4} textAnchor="middle" dominantBaseline="middle" style={{fontSize:18,fontWeight:700,fill:"hsl(var(--foreground))"}}>{centerLabel}</text>{centerSubLabel&&<text x={cx} y={cy+16} textAnchor="middle" dominantBaseline="middle" style={{fontSize:11,fill:"hsl(var(--muted-foreground))"}}>{centerSubLabel}</text>}</g>}
      </svg>
      <div className="flex flex-col gap-2 min-w-0">
        {data.map((d)=><div key={d.label} className="flex items-center gap-2 min-w-0"><span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{background:d.color}} /><span className="text-xs text-muted-foreground truncate">{d.label}</span><span className="text-xs font-medium text-foreground ml-auto pl-2">{((d.value/total)*100).toFixed(1)}%</span></div>)}
      </div>
    </div>
  );
}
