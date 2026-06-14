import { apiClient } from "@/lib/api/client";
import type {
  CreateFarrowingRequest,
  CreateMatingRequest,
  CreatePigletEventRequest,
  CreateReproductiveEventRequest,
  CreateWeaningRequest,
  Farrowing,
  Mating,
  PigletEventRecord,
  ReproductiveEvent,
  UpdateFarrowingRequest,
  UpdateMatingRequest,
  UpdateWeaningRequest,
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

    update: (farmId: string, id: string, body: UpdateMatingRequest) =>
      apiClient.patch<Mating>(`${base(farmId)}/matings/${id}`, body).then((r) => r.data),

    remove: (farmId: string, id: string) =>
      apiClient.delete(`${base(farmId)}/matings/${id}`).then(() => undefined),
  },

  farrowings: {
    list: (farmId: string, sowId?: string) =>
      apiClient
        .get<Farrowing[]>(`${base(farmId)}/farrowings`, { params: { sow_id: sowId } })
        .then((r) => r.data),

    create: (farmId: string, body: CreateFarrowingRequest) =>
      apiClient.post<Farrowing>(`${base(farmId)}/farrowings`, body).then((r) => r.data),

    update: (farmId: string, id: string, body: UpdateFarrowingRequest) =>
      apiClient.patch<Farrowing>(`${base(farmId)}/farrowings/${id}`, body).then((r) => r.data),

    remove: (farmId: string, id: string) =>
      apiClient.delete(`${base(farmId)}/farrowings/${id}`).then(() => undefined),
  },

  weanings: {
    list: (farmId: string, sowId?: string) =>
      apiClient
        .get<Weaning[]>(`${base(farmId)}/weanings`, { params: { sow_id: sowId } })
        .then((r) => r.data),

    create: (farmId: string, body: CreateWeaningRequest) =>
      apiClient.post<Weaning>(`${base(farmId)}/weanings`, body).then((r) => r.data),

    update: (farmId: string, id: string, body: UpdateWeaningRequest) =>
      apiClient.patch<Weaning>(`${base(farmId)}/weanings/${id}`, body).then((r) => r.data),

    remove: (farmId: string, id: string) =>
      apiClient.delete(`${base(farmId)}/weanings/${id}`).then(() => undefined),
  },

  reproductive: {
    create: (farmId: string, body: CreateReproductiveEventRequest) =>
      apiClient
        .post<ReproductiveEvent>(`/api/v1/farms/${farmId}/events/reproductive`, body)
        .then((r) => r.data),
  },

  pigletEvents: {
    list: (farmId: string, sowId?: string, farrowingId?: string) =>
      apiClient
        .get<PigletEventRecord[]>(`${base(farmId)}/piglet_events`, {
          params: { sow_id: sowId, farrowing_id: farrowingId },
        })
        .then((r) => r.data),

    create: (farmId: string, body: CreatePigletEventRequest) =>
      apiClient
        .post<PigletEventRecord>(`${base(farmId)}/piglet_events`, body)
        .then((r) => r.data),
  },
};
