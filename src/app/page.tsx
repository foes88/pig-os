import { Sidebar } from "@/components/Sidebar";
import { Stat, AIBubble, AIAction, Card, PipeItem } from "@/components/ui";

export default function Dashboard() {
  return (
    <div className="min-h-screen">
      <Sidebar />
      <main className="ml-[220px] p-7">
        {/* Header */}
        <div className="flex items-center justify-between mb-7">
          <div>
            <h1 className="text-[22px] font-extrabold tracking-tight flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse shadow-[0_0_8px_var(--color-primary)]" />
              AI Dashboard
            </h1>
            <p className="text-xs text-text3">Wiselake Farm · 680 sows · AI analyzing in real-time</p>
          </div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-primary-light text-primary border border-primary/20 rounded-full text-xs font-semibold">
            🧠 AI Active
          </span>
        </div>

        {/* Alert */}
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-5 flex items-start gap-3.5">
          <span className="text-xl flex-shrink-0">🚨</span>
          <div className="flex-1">
            <div className="text-[13px] font-bold text-danger mb-1">
              AI Alert: #A-042 Farrowing Overdue (D115) — Immediate Action Required
            </div>
            <div className="text-xs text-text2">
              AI detected abnormal gestation length. 87% probability of complications. Recommended: veterinary check within 2 hours.
            </div>
          </div>
          <button className="flex-shrink-0 bg-primary text-white px-4 py-2 rounded-lg text-xs font-semibold hover:shadow-lg transition">
            Take Action
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-3 mb-6">
          <Stat label="PSY (AI Predicted)" value="24.3" sub="▲ +1.2 · Next month forecast: 24.8" subType="up" />
          <Stat label="Revenue This Month" value="₩298M" sub="▲ +8.2% · AI saved ₩840K in feed" subType="up" valueColor="var(--color-gold)" />
          <Stat label="AI Actions Today" value="7" sub="3 critical · 2 high · 2 insight" subType="ai" valueColor="var(--color-purple)" />
          <Stat label="Mortality Risk" value="2.1%" sub="▲ Up from 1.5% — PRRS suspected" subType="down" valueColor="var(--color-danger)" />
        </div>

        {/* Pipeline */}
        <div className="flex gap-1 mb-6">
          <PipeItem icon="💉" count={12} name="Breeding" aiIcon />
          <span className="flex items-center text-text3 text-xs">→</span>
          <PipeItem icon="🔍" count={8} name="Preg Check" />
          <span className="flex items-center text-text3 text-xs">→</span>
          <PipeItem icon="🤰" count={218} name="Gestation" active aiIcon />
          <span className="flex items-center text-text3 text-xs">→</span>
          <PipeItem icon="🐖" count={5} name="Farrowing" aiIcon aiDanger />
          <span className="flex items-center text-text3 text-xs">→</span>
          <PipeItem icon="🍼" count={85} name="Lactation" />
          <span className="flex items-center text-text3 text-xs">→</span>
          <PipeItem icon="🌱" count={3} name="Weaning" />
        </div>

        {/* Two Column */}
        <div className="grid grid-cols-2 gap-4">
          {/* Left: AI Actions */}
          <div>
            <Card title="🧠 AI Recommended Actions" badge="7 actions" badgeColor="purple" className="mb-4" children={<></>} />

            <AIAction
              priority="critical"
              title="#A-042 Farrowing — Overdue D115"
              desc="Gestation exceeds normal range. AI predicts 87% complication risk. Veterinary intervention recommended within 2 hours."
              impact="Risk: High"
              impactNegative
              actionLabel="Record Farrowing"
            />
            <AIAction
              priority="critical"
              title="PRRS Suspected — Satellite Farm"
              desc="Mortality pattern matches PRRS signature (87% AI confidence). 3 deaths in 48h. Isolation + PCR testing recommended."
              impact="Potential loss: ₩150M+"
              impactNegative
              actionLabel="Execute Protocol"
            />
            <AIAction
              priority="high"
              title="Optimal Breeding Window — 12 Sows Today"
              desc="AI analyzed WEI patterns. Optimal breeding time: 14:30~16:00 today. Expected conception rate: 92% (vs 85% random)."
              impact="+7% conception rate"
              actionLabel="Start Breeding"
            />
            <AIAction
              priority="high"
              title="Ship Pen F-01 by Mar 22"
              desc="Market price trending up ₩5,140/kg (+2.3%). AI predicts 5-7 more days of increase, then seasonal dip."
              impact="+₩1.2M extra revenue"
              actionLabel="Schedule Shipment"
            />
            <AIAction
              priority="medium"
              title="Feed Adjustment — Barn A Gestating"
              desc="FCR analysis: Barn A gestating sows overfed by 8%. Current 2.8kg/day → AI recommends 2.6kg/day."
              impact="Save ₩840K/month"
              actionLabel="Apply"
            />
            <AIAction
              priority="insight"
              title="Farrowing Forecast — 23 Sows in 14 Days"
              desc="Expected avg litter: 12.4. 3 high-risk sows (P7+). Pre-assign foster mothers for #A-055, #A-078."
              impact="~285 piglets expected"
              actionLabel="View Schedule"
            />
          </div>

          {/* Right */}
          <div>
            <AIBubble label="AI Daily Briefing">
              <p>
                Your farm PSY reached <strong className="text-primary">24.3</strong> — now in the{" "}
                <strong className="text-primary">national top 35%</strong>. Main driver: breeding efficiency improved 12% since January protocol change.
                Key risk today: <strong className="text-primary">#A-042 overdue farrowing</strong> and{" "}
                <strong className="text-primary">satellite farm PRRS suspicion</strong>.
                Feed optimization is saving <strong className="text-primary">₩840K/month</strong>.
                Next month PSY forecast: <strong className="text-primary">24.8 (▲)</strong>.
              </p>
            </AIBubble>

            <Card title="Herd Status" className="mb-4">
              <table className="w-full">
                <tbody className="text-xs">
                  {[
                    { label: "Gestating", value: "218", tag: "Normal", tagColor: "green" as const },
                    { label: "Lactating", value: "85", tag: "Avg D14", tagColor: "green" as const },
                    { label: "Open / NPD", value: "42", tag: "8 over 30d", tagColor: "yellow" as const, valueColor: "var(--color-warning)" },
                    { label: "Finisher", value: "340", tag: "58 ship ready", tagColor: "green" as const },
                    { label: "Critical", value: "3", tag: "Action needed", tagColor: "red" as const, valueColor: "var(--color-danger)" },
                  ].map((row, i) => (
                    <tr key={i} className="border-b border-border">
                      <td className="py-2.5">{row.label}</td>
                      <td className="py-2.5 text-right font-mono font-bold" style={row.valueColor ? { color: row.valueColor } : {}}>
                        {row.value}
                      </td>
                      <td className="py-2.5 text-right">
                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${
                          row.tagColor === "green" ? "bg-green-50 text-success" :
                          row.tagColor === "yellow" ? "bg-amber-50 text-warning" :
                          "bg-red-50 text-danger"
                        }`}>{row.tag}</span>
                      </td>
                    </tr>
                  ))}
                  <tr className="border-t-2 border-border">
                    <td className="py-2.5 font-bold">Total</td>
                    <td className="py-2.5 text-right font-mono font-extrabold text-base">680</td>
                    <td></td>
                  </tr>
                </tbody>
              </table>
            </Card>

            <Card title="💰 AI Revenue Impact (This Month)" className="border-gold/20">
              <table className="w-full text-xs">
                <tbody>
                  {[
                    { label: "Feed optimization", value: "+₩840K saved" },
                    { label: "Breeding timing", value: "+7% conception" },
                    { label: "Shipment timing", value: "+₩1.2M pending" },
                    { label: "Disease prevention", value: "₩150M+ at risk" },
                  ].map((row, i) => (
                    <tr key={i} className="border-b border-border">
                      <td className="py-2.5">{row.label}</td>
                      <td className="py-2.5 text-right font-mono font-bold text-success">{row.value}</td>
                    </tr>
                  ))}
                  <tr className="border-t-2 border-border">
                    <td className="py-2.5 font-bold text-gold">Total AI Value</td>
                    <td className="py-2.5 text-right font-mono font-extrabold text-sm text-gold">₩152M+ impact</td>
                  </tr>
                </tbody>
              </table>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
