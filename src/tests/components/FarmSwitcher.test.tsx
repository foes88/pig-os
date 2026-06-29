import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, fireEvent } from "@testing-library/react";

import { renderWithClient } from "../test-utils";

const h = vi.hoisted(() => ({
  activeFarmId: "f1" as string | null,
  setActiveFarmId: vi.fn(),
  farms: [
    { id: "f1", name: "Green Farm" },
    { id: "f2", name: "Blue Farm" },
  ] as { id: string; name: string }[],
}));

vi.mock("@/store/auth.store", () => ({
  useAuthStore: (sel: (s: { activeFarmId: string | null; setActiveFarmId: (id: string) => void }) => unknown) =>
    sel({ activeFarmId: h.activeFarmId, setActiveFarmId: h.setActiveFarmId }),
}));
vi.mock("@/lib/api/endpoints/farms", () => ({
  farmsApi: { list: vi.fn(() => Promise.resolve(h.farms)) },
}));

import { FarmSwitcher } from "@/components/FarmSwitcher";

describe("FarmSwitcher (멀티팜 전환)", () => {
  beforeEach(() => {
    h.activeFarmId = "f1";
    h.setActiveFarmId.mockClear();
    h.farms = [{ id: "f1", name: "Green Farm" }, { id: "f2", name: "Blue Farm" }];
  });

  it("접근 가능 농장 여러 개면 드롭다운에 모두 표시", async () => {
    renderWithClient(<FarmSwitcher />);
    const select = await screen.findByTestId("farm-switcher");
    expect(select).toBeInTheDocument();
    expect(screen.getByText("Green Farm")).toBeInTheDocument();
    expect(screen.getByText("Blue Farm")).toBeInTheDocument();
  });

  it("다른 농장 선택 시 setActiveFarmId 호출", async () => {
    renderWithClient(<FarmSwitcher />);
    const select = await screen.findByTestId("farm-switcher");
    fireEvent.change(select, { target: { value: "f2" } });
    expect(h.setActiveFarmId).toHaveBeenCalledWith("f2");
  });

  it("농장 1개면 드롭다운 없이 이름만 표시", async () => {
    h.farms = [{ id: "f1", name: "Solo Farm" }];
    renderWithClient(<FarmSwitcher />);
    expect(await screen.findByText("Solo Farm")).toBeInTheDocument();
    expect(screen.queryByTestId("farm-switcher")).not.toBeInTheDocument();
  });
});
