import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";

import { renderWithClient } from "../test-utils";

vi.mock("next-intl", () => ({ useTranslations: () => (k: string) => k }));
vi.mock("next/link", () => ({ default: ({ children }: { children: React.ReactNode }) => <>{children}</> }));
vi.mock("@/store/auth.store", () => ({
  useAuthStore: (sel: (s: { activeFarmId: string | null }) => unknown) => sel({ activeFarmId: "farm-1" }),
}));
vi.mock("@/lib/api/endpoints/tasks", () => ({
  tasksApi: {
    list: vi.fn().mockResolvedValue([]),
    generate: vi.fn().mockResolvedValue({ created: 0, closed: 0, open_total: 0 }),
    update: vi.fn().mockResolvedValue({}),
  },
}));

import TasksPage from "@/app/(app)/tasks/page";

describe("TasksPage", () => {
  it("renders the page title", () => {
    renderWithClient(<TasksPage />);
    expect(screen.getByText("pageTitle")).toBeInTheDocument();
  });

  it("shows the all-clear empty state after load", async () => {
    renderWithClient(<TasksPage />);
    expect(await screen.findByText("allClear")).toBeInTheDocument();
  });
});
