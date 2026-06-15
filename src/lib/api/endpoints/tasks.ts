import { apiClient } from "@/lib/api/client";
import type {
  Task,
  TaskGenerateResult,
  TaskStatus,
  TaskUpdateRequest,
} from "@/types/api.types";

const base = (farmId: string) => `/api/v1/farms/${farmId}/tasks`;

export const tasksApi = {
  list: (farmId: string, status: TaskStatus = "OPEN") =>
    apiClient
      .get<Task[]>(base(farmId), { params: { status } })
      .then((r) => r.data),

  generate: (farmId: string) =>
    apiClient.post<TaskGenerateResult>(`${base(farmId)}/generate`).then((r) => r.data),

  update: (farmId: string, taskId: string, body: TaskUpdateRequest) =>
    apiClient.patch<Task>(`${base(farmId)}/${taskId}`, body).then((r) => r.data),
};
