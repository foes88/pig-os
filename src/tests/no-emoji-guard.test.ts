/**
 * 이모지 회귀 가드 (R7) — 주요 화면 소스에 유니코드 picto 이모지가 없어야 한다.
 * 표준 아이콘 시스템 = lucide-react. 화살표(→)·⌘K·○ 같은 의도된 기호는 대상 아님(명시 charset만).
 *
 * 참고: 프로젝트는 vitest 러너를 사용하므로(별도 playwright e2e 미구성) 브라우저 없이
 * 소스 정적 스캔으로 회귀를 잠근다. 대시보드/record/topbar 포함 핵심 화면 커버.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

const SRC = resolve(__dirname, "..");

// 제거 대상 picto 이모지/허접 글리프 (의도된 →, ⌘, ○ 는 제외)
const BANNED = /[🐷💉🤰🐖🍼🌱🔍🔔🧠🚨⚠ℹ✓✦⊞⬡⚙💡⚡🔮🐽📊📈🎯]/u;

const FILES = [
  "app/(app)/page.tsx",
  "app/(app)/record/page.tsx",
  "app/(app)/kpi/page.tsx",
  "app/(app)/sows/[id]/page.tsx",
  "components/Topbar.tsx",
  "components/BottomNav.tsx",
  "components/ui.tsx",
  "components/AskAiDrawer.tsx",
  "app/update/page.tsx",
];

describe("emoji regression guard", () => {
  it.each(FILES)("%s has no picto emoji", (rel) => {
    const text = readFileSync(resolve(SRC, rel), "utf-8");
    const lines = text.split("\n");
    const offenders = lines
      .map((l, i) => ({ l, i: i + 1 }))
      .filter(({ l }) => BANNED.test(l))
      .map(({ l, i }) => `${rel}:${i}: ${l.trim().slice(0, 60)}`);
    expect(offenders).toEqual([]);
  });
});
