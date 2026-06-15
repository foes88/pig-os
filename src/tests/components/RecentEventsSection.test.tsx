import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";

import { renderWithClient } from "../test-utils";

vi.mock("next-intl", () => ({ useTranslations: () => (k: string) => k }));
vi.mock("@/lib/api/endpoints/events", () => ({
  eventsApi: {
    matings: { list: vi.fn().mockResolvedValue([]) },
    farrowings: { list: vi.fn().mockResolvedValue([]) },
    weanings: { list: vi.fn().mockResolvedValue([]) },
  },
}));

import { RecentEventsSection } from "@/components/RecentEventsSection";

describe("RecentEventsSection", () => {
  it("renders the section title", () => {
    renderWithClient(<RecentEventsSection farmId="f1" sowId="s1" />);
    expect(screen.getByText("title")).toBeInTheDocument();
  });

  it("shows the empty state when there are no events", async () => {
    renderWithClient(<RecentEventsSection farmId="f1" sowId="s1" />);
    expect(await screen.findByText("empty")).toBeInTheDocument();
  });
});
