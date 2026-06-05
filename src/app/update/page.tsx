export default function UpdatePage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-6">
      <div className="bg-surface border border-border rounded-2xl shadow-xl p-10 w-full max-w-md text-center">
        <div className="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center mx-auto mb-6">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 12a9 9 0 1 1-6.2-8.6"/><path d="M21 3v6h-6"/>
          </svg>
        </div>
        <h1 className="text-2xl font-extrabold text-text tracking-tight mb-2">새 버전이 출시됐어요</h1>
        <p className="text-sm text-text2 leading-relaxed mb-1">원활한 이용을 위해 최신 버전으로<br/>업데이트가 필요합니다.</p>
        <p className="text-xs text-text3 font-mono mb-6">v2.4.0 · 필수 업데이트</p>
        <div className="bg-background rounded-xl p-4 text-left mb-6">
          <p className="text-xs font-bold text-text3 mb-3">업데이트 내용</p>
          {["음성 입력 기능 추가", "AI 손실 감지 정확도 개선", "오프라인 동기화 안정화"].map((x, i) => (
            <div key={i} className="flex items-center gap-2 py-1.5 text-sm text-text2">
              <span className="text-success font-bold">✓</span>{x}
            </div>
          ))}
        </div>
        <button className="w-full bg-navy text-white py-4 rounded-xl text-base font-bold hover:opacity-90 transition">
          지금 업데이트
        </button>
      </div>
    </div>
  );
}
