const NOTICES = [
  { tag: "업데이트", tagColor: "text-primary bg-blue-50 border-blue-100", title: "AI 신호 정확도 개선 + 음성 입력 추가", body: "분만 기록을 음성으로 입력할 수 있게 되었습니다. AI 손실 감지 정확도가 12% 향상되었습니다.", date: "2026-05-28", pinned: true },
  { tag: "점검", tagColor: "text-warning bg-amber-50 border-amber-100", title: "정기 점검 안내", body: "정기 서버 점검이 진행됩니다. 해당 시간 입력은 오프라인 저장 후 자동 동기화됩니다.", date: "2026-05-25", pinned: false },
  { tag: "이벤트", tagColor: "text-success bg-green-50 border-green-100", title: "AI 번들 30일 무료 체험 연장", body: "AI 번들 무료 체험 기간이 30일로 연장됩니다.", date: "2026-05-10", pinned: false },
];

export default function AnnouncementsPage() {
  return (
    <div className="max-w-3xl mx-auto px-7 py-6">
      <h1 className="text-xl font-extrabold tracking-tight mb-5">공지사항</h1>
      <div className="space-y-3">
        {NOTICES.map((n, i) => (
          <div key={i} className="bg-surface border border-border rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-3">
              {n.pinned && <span className="text-sm">📌</span>}
              <span className={`text-[11px] font-bold font-mono px-2 py-0.5 rounded-md border ${n.tagColor}`}>{n.tag}</span>
              <span className="text-[11px] text-text3 font-mono ml-auto">{n.date}</span>
            </div>
            <div className="text-sm font-bold text-text mb-2">{n.title}</div>
            <p className="text-sm text-text2 leading-relaxed">{n.body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
