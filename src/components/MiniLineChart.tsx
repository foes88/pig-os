"use client";

// 리포트 공용 인라인 SVG 라인차트 — 외부 차트 라이브러리 없음.
// null 값은 선을 끊어 표시(연속 구간만 polyline). benchmark 지정 시 점선 기준선 병기.
export function MiniLineChart({
  points,
  benchmark,
  color,
  label,
}: {
  points: { x: string; y: number | null }[];
  benchmark?: number | null;
  color: string;
  label: string;
}) {
  const W = 320, H = 120, padX = 8, padTop = 12, padBottom = 20;
  const vals = points.map((p) => p.y).filter((v): v is number => v != null);
  const withBench = benchmark != null ? [...vals, benchmark] : vals;
  if (vals.length === 0) {
    return <div className="h-[120px] flex items-center justify-center text-xs text-text3">—</div>;
  }
  const lo = Math.min(...withBench), hi = Math.max(...withBench);
  const span = hi - lo || 1;
  const plotH = H - padTop - padBottom;
  const stepX = points.length > 1 ? (W - padX * 2) / (points.length - 1) : 0;
  const xAt = (i: number) => padX + stepX * i;
  const yAt = (v: number) => padTop + plotH * (1 - (v - lo) / span);

  const segments: string[] = [];
  let cur: string[] = [];
  points.forEach((p, i) => {
    if (p.y == null) { if (cur.length) { segments.push(cur.join(" ")); cur = []; } return; }
    cur.push(`${xAt(i).toFixed(1)},${yAt(p.y).toFixed(1)}`);
  });
  if (cur.length) segments.push(cur.join(" "));

  // x축 라벨 과밀 방지: 점이 많으면 일부만 표기
  const labelEvery = Math.ceil(points.length / 8);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-[120px]" role="img" aria-label={label}>
      {benchmark != null && (
        <>
          <line x1={padX} x2={W - padX} y1={yAt(benchmark)} y2={yAt(benchmark)}
            stroke="var(--color-warning, #d97706)" strokeWidth="1" strokeDasharray="4 3" opacity="0.7" />
          <text x={W - padX} y={yAt(benchmark) - 3} textAnchor="end" className="fill-warning" fontSize="9">{benchmark}</text>
        </>
      )}
      {segments.map((pts, i) => (
        <polyline key={i} points={pts} fill="none" stroke={color} strokeWidth="2"
          strokeLinejoin="round" strokeLinecap="round" />
      ))}
      {points.map((p, i) => p.y != null && (
        <g key={i}>
          <circle cx={xAt(i)} cy={yAt(p.y)} r="3" fill={color} />
          {points.length <= 8 && (
            <text x={xAt(i)} y={yAt(p.y) - 6} textAnchor="middle" fontSize="9" className="fill-text2 font-mono">{p.y}</text>
          )}
        </g>
      ))}
      {points.map((p, i) => (i % labelEvery === 0 || i === points.length - 1) && (
        <text key={`x${i}`} x={xAt(i)} y={H - 6} textAnchor="middle" fontSize="8" className="fill-text3 font-mono">
          {p.x}
        </text>
      ))}
    </svg>
  );
}
