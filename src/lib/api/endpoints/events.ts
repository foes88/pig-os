import { apiClient } from "@/lib/api/client";
import type {
  CreateFarrowingRequest,
  CreateMatingRequest,
  CreateReproductiveEventRequest,
  CreateWeaningRequest,
  Farrowing,
  Mating,
  ReproductiveEvent,
  Weaning,
} from "@/types/api.types";

const base = (farmId: string) => `/api/v1/farms/${farmId}/events`;

export const eventsApi = {
  matings: {
    list: (farmId: string, sowId?: string) =>
      apiClient
        .get<Mating[]>(`${base(farmId)}/matings`, { params: { sow_id: sowId } })
        .then((r) => r.data),

    create: (farmId: string, body: CreateMatingRequest) =>
      apiClient.post<Mating>(`${base(farmId)}/matings`, body).then((r) => r.data),
  },

  farrowings: {
    list: (farmId: string, sowId?: string) =>
      apiClient
        .get<Farrowing[]>(`${base(farmId)}/farrowings`, { params: { sow_id: sowId } })
        .then((r) => r.data),

    create: (farmId: string, body: CreateFarrowingRequest) =>
      apiClient.post<Farrowing>(`${base(farmId)}/farrowings`, body).then((r) => r.data),
  },

  weanings: {
    list: (farmId: string, sowId?: string) =>
      apiClient
        .get<Weaning[]>(`${base(farmId)}/weanings`, { params: { sow_id: sowId } })
        .then((r) => r.data),

    create: (farmId: string, body: CreateWeaningRequest) =>
      apiClient.post<Weaning>(`${base(farmId)}/weanings`, body).then((r) => r.data),
  },

  reproductive: {
    create: (farmId: string, body: CreateReproductiveEventRequest) =>
      apiClient
        .post<ReproductiveEvent>(`/api/v1/farms/${farmId}/events/reproductive`, body)
        .then((r) => r.data),
  },
};
