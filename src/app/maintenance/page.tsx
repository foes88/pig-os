export default function MaintenancePage() {
  return (
    <div className="min-h-screen flex items-center justify-center text-center px-6"
      style={{ background: "linear-gradient(170deg,#0D1B3E,#16264f)" }}>
      <div className="max-w-sm">
        <div className="text-5xl mb-6">🔧</div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight mb-3">잠시 점검 중이에요</h1>
        <p className="text-base text-white/70 leading-relaxed mb-6">
          더 나은 서비스를 위해 시스템을 업데이트하고 있어요.
        </p>
        <div className="inline-flex items-center gap-2 bg-white/10 border border-white/15 rounded-full px-5 py-2.5 font-mono text-sm text-white mb-8">
          <span className="w-2 h-2 rounded-full bg-green-400 inline-block" />
          예상 완료 04:00 KST
        </div>
        <p className="text-xs text-white/40 leading-relaxed">
          현장 입력은 오프라인으로 계속 가능하며,<br />점검 완료 후 자동 동기화됩니다.
        </p>
      </div>
    </div>
  );
}
