"use client";

interface AddonCard {
  icon: string;
  name: { ko: string; en: string };
  desc: { ko: string; en: string };
  tag: "coming_soon" | "beta" | "free";
  category: string;
}

const ADDONS: AddonCard[] = [
  {
    icon: "🧠",
    name: { ko: "AI 인사이트", en: "AI Insight" },
    desc: { ko: "Rule Engine 결과를 자연어로 설명 (Claude 기반)", en: "Natural-language KPI analysis powered by Claude" },
    tag: "beta",
    category: "analytics",
  },
  {
    icon: "📋",
    name: { ko: "Task 자동배정", en: "Auto Task Assign" },
    desc: { ko: "알림 발생 시 담당자에게 Task 자동 생성 및 모바일 알림", en: "Auto-create tasks from alerts and push to staff mobile" },
    tag: "coming_soon",
    category: "ops",
  },
  {
    icon: "📦",
    name: { ko: "사료 재고 관리", en: "Feed Inventory" },
    desc: { ko: "입고/출고/재고 현황 + FCR 자동 계산", en: "Feed in/out tracking with auto FCR calculation" },
    tag: "coming_soon",
    category: "ops",
  },
  {
    icon: "🌡",
    name: { ko: "IoT 센서 연동", en: "IoT Sensor" },
    desc: { ko: "온도·습도·암모니아 실시간 모니터링 (TimescaleDB)", en: "Real-time barn environment via TimescaleDB" },
    tag: "coming_soon",
    category: "iot",
  },
  {
    icon: "📊",
    name: { ko: "Excel/PDF 리포트", en: "Excel/PDF Export" },
    desc: { ko: "월간 성적 보고서 자동 생성 및 다운로드", en: "Auto-generate monthly performance reports" },
    tag: "coming_soon",
    category: "analytics",
  },
  {
    icon: "🔗",
    name: { ko: "도축장 연동", en: "Slaughterhouse Link" },
    desc: { ko: "출하 데이터 → 도체 성적 자동 매핑 (Traceability)", en: "Link shipment data to carcass grades for traceability" },
    tag: "coming_soon",
    category: "integration",
  },
  {
    icon: "📱",
    name: { ko: "QR 소비자 투명성", en: "QR Transparency" },
    desc: { ko: "소비자가 QR로 농장 이력 조회 (B2B 프리미엄)", en: "Consumer QR scan shows farm history — B2B premium" },
    tag: "coming_soon",
    category: "integration",
  },
  {
    icon: "💹",
    name: { ko: "데이터 수익화", en: "Data Monetization" },
    desc: { ko: "익명 벤치마크 데이터 기여 → 농가 배분 프로그램", en: "Contribute anonymized benchmarks, earn revenue share" },
    tag: "coming_soon",
    category: "analytics",
  },
];

const TAG_STYLE: Record<AddonCard["tag"], string> = {
  free:        "bg-success/10 text-success border-success/20",
  beta:        "bg-blue-50 text-blue-600 border-blue-200",
  coming_soon: "bg-background text-text3 border-border",
};

const TAG_LABEL: Record<AddonCard["tag"], string> = {
  free:        "무료",
  beta:        "Beta",
  coming_soon: "출시 예정",
};

export default function AddonsPage() {
  return (
    <div className="p-7 max-w-4xl">
      {/* Header */}
      <div className="mb-2">
        <h1 className="text-[22px] font-extrabold tracking-tight">Addon 스토어</h1>
        <p className="text-xs text-text3 mt-0.5">
          PigOS 기능을 확장하는 Addon — 필요한 것만 켜세요
        </p>
      </div>

      {/* Banner */}
      <div
        className="rounded-2xl p-5 mb-8 mt-4"
        style={{ background: "linear-gradient(135deg, #0D1B3E 0%, #1e3a8a 100%)" }}
      >
        <div className="text-xs font-bold text-blue-300 uppercase tracking-widest mb-1">PigOS Strategy</div>
        <p className="text-white font-bold text-base leading-snug">
          무료 제공 → 데이터 수집 → 수익화 → 농가 배분
        </p>
        <p className="text-blue-200 text-xs mt-1.5">
          Addon을 사용할수록 농가가 더 많이 받아가는 구조
        </p>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-2 gap-3">
        {ADDONS.map((addon) => (
          <div
            key={addon.name.ko}
            className="bg-surface border border-border rounded-2xl p-5 flex flex-col gap-3"
          >
            <div className="flex items-start justify-between gap-2">
              <span className="text-2xl">{addon.icon}</span>
              <span
                className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${TAG_STYLE[addon.tag]}`}
              >
                {TAG_LABEL[addon.tag]}
              </span>
            </div>
            <div>
              <div className="font-bold text-sm text-text">{addon.name.ko}</div>
              <div className="text-xs text-text3 mt-0.5 leading-relaxed">{addon.desc.ko}</div>
            </div>
            <button
              disabled={addon.tag === "coming_soon"}
              className={`mt-auto text-xs font-semibold rounded-lg px-3 py-2 transition ${
                addon.tag === "coming_soon"
                  ? "bg-background text-text3 border border-border cursor-not-allowed"
                  : addon.tag === "beta"
                  ? "bg-primary text-white hover:bg-blue-700"
                  : "bg-success/10 text-success border border-success/20 hover:bg-success/20"
              }`}
            >
              {addon.tag === "coming_soon" ? "출시 예정" : addon.tag === "beta" ? "Beta 시작" : "무료 활성화"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
