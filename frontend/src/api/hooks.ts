import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import type {
  AnalyticsSummary,
  ApiKey,
  ApiKeyCreated,
  AppNotification,
  Attachment,
  AuditLog,
  Connection,
  ConnectionProvider,
  CustomFieldDefinition,
  Deal,
  InboundEndpoint,
  Lead,
  LeadsOverTimePoint,
  Member,
  Note,
  Paginated,
  PipelineColumn,
  Role,
  SavedView,
  Stage,
  StageBreakdown,
  StatusCount,
  Tag,
  Task,
  WebhookDelivery,
  WebhookEndpoint,
} from "../lib/types";
import { api } from "./client";

// --- Leads -------------------------------------------------------------------

export function useLeads(
  params: {
    search?: string;
    status?: string;
    q?: string;
    tag?: number;
    ordering?: string;
  } = {},
) {
  return useQuery({
    queryKey: ["leads", params],
    queryFn: async () => {
      const { data } = await api.get<Paginated<Lead>>("/api/leads/", { params });
      return data;
    },
  });
}

export function useCreateLead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<Lead>) => {
      const { data } = await api.post<Lead>("/api/leads/", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["leads"] }),
  });
}

export function useUpdateLead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...payload }: Partial<Lead> & { id: number }) => {
      const { data } = await api.patch<Lead>(`/api/leads/${id}/`, payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["leads"] }),
  });
}

export function useDeleteLead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/api/leads/${id}/`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["leads"] }),
  });
}

// --- Pipeline / Deals --------------------------------------------------------

export function useStages() {
  return useQuery({
    queryKey: ["stages"],
    queryFn: async () => {
      const { data } = await api.get<Paginated<Stage>>("/api/stages/");
      return data.results;
    },
  });
}

export function usePipeline() {
  return useQuery({
    queryKey: ["pipeline"],
    queryFn: async () => {
      const { data } = await api.get<PipelineColumn[]>("/api/deals/pipeline/");
      return data;
    },
  });
}

export function useCreateDeal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<Deal>) => {
      const { data } = await api.post<Deal>("/api/deals/", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pipeline"] }),
  });
}

export function useMoveDeal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, stage }: { id: number; stage: number }) => {
      const { data } = await api.post<Deal>(`/api/deals/${id}/move/`, { stage });
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pipeline"] }),
  });
}

// --- Analytics ---------------------------------------------------------------

export function useSummary() {
  return useQuery({
    queryKey: ["analytics", "summary"],
    queryFn: async () => {
      const { data } = await api.get<AnalyticsSummary>("/api/analytics/summary/");
      return data;
    },
  });
}

export function useDealsByStage() {
  return useQuery({
    queryKey: ["analytics", "deals-by-stage"],
    queryFn: async () => {
      const { data } = await api.get<StageBreakdown[]>(
        "/api/analytics/deals-by-stage/",
      );
      return data;
    },
  });
}

export function useLeadsByStatus() {
  return useQuery({
    queryKey: ["analytics", "leads-by-status"],
    queryFn: async () => {
      const { data } = await api.get<StatusCount[]>(
        "/api/analytics/leads-by-status/",
      );
      return data;
    },
  });
}

export function useLeadsOverTime(days = 30) {
  return useQuery({
    queryKey: ["analytics", "leads-over-time", days],
    queryFn: async () => {
      const { data } = await api.get<LeadsOverTimePoint[]>(
        "/api/analytics/leads-over-time/",
        { params: { days } },
      );
      return data;
    },
  });
}

// --- Tasks -------------------------------------------------------------------

export function useTasks(params: { is_done?: string; priority?: string } = {}) {
  return useQuery({
    queryKey: ["tasks", params],
    queryFn: async () => {
      const { data } = await api.get<Paginated<Task>>("/api/tasks/", { params });
      return data;
    },
  });
}

export function useCreateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<Task>) => {
      const { data } = await api.post<Task>("/api/tasks/", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function useUpdateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...payload }: Partial<Task> & { id: number }) => {
      const { data } = await api.patch<Task>(`/api/tasks/${id}/`, payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function useDeleteTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/api/tasks/${id}/`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

// --- Activity (audit log) ----------------------------------------------------

export function useActivity(
  params: { action?: string; target_model?: string; target_id?: number } = {},
) {
  return useQuery({
    queryKey: ["activity", params],
    queryFn: async () => {
      const { data } = await api.get<Paginated<AuditLog>>("/api/activity/", {
        params,
      });
      return data;
    },
  });
}

// --- Members -----------------------------------------------------------------

export function useMembers() {
  return useQuery({
    queryKey: ["members"],
    queryFn: async () => {
      const { data } = await api.get<Paginated<Member>>("/api/members/");
      return data.results;
    },
  });
}

export function useInviteMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      email: string;
      role: Role;
      password?: string;
    }) => {
      const { data } = await api.post<Member>("/api/members/", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["members"] }),
  });
}

export function useUpdateMemberRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, role }: { id: number; role: Role }) => {
      const { data } = await api.patch<Member>(`/api/members/${id}/`, { role });
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["members"] }),
  });
}

export function useRemoveMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/api/members/${id}/`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["members"] }),
  });
}

// --- Phase 8: tags, notes, attachments, custom fields, saved views ----------

export function useTags() {
  return useQuery({
    queryKey: ["tags"],
    queryFn: async () => {
      const { data } = await api.get<Paginated<Tag>>("/api/tags/");
      return data.results;
    },
  });
}

export function useCreateTag() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { name: string; color?: string }) => {
      const { data } = await api.post<Tag>("/api/tags/", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tags"] }),
  });
}

export function useNotes(target: { model: string; id: number }) {
  return useQuery({
    queryKey: ["notes", target],
    queryFn: async () => {
      const { data } = await api.get<Paginated<Note>>("/api/notes/", {
        params: { target_model: target.model, target_id: target.id },
      });
      return data.results;
    },
  });
}

export function useCreateNote() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      body: string;
      target_model: string;
      target_id: number;
    }) => {
      const { data } = await api.post<Note>("/api/notes/", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notes"] }),
  });
}

export function useAttachments(target: { model: string; id: number }) {
  return useQuery({
    queryKey: ["attachments", target],
    queryFn: async () => {
      const { data } = await api.get<Paginated<Attachment>>("/api/attachments/", {
        params: { target_model: target.model, target_id: target.id },
      });
      return data.results;
    },
  });
}

export function useUploadAttachment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      file,
      target_model,
      target_id,
    }: {
      file: File;
      target_model: string;
      target_id: number;
    }) => {
      const form = new FormData();
      form.append("file", file);
      form.append("target_model", target_model);
      form.append("target_id", String(target_id));
      const { data } = await api.post<Attachment>("/api/attachments/", form);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["attachments"] }),
  });
}

export function useCustomFields(entity: "lead" | "deal") {
  return useQuery({
    queryKey: ["custom-fields", entity],
    queryFn: async () => {
      const { data } = await api.get<Paginated<CustomFieldDefinition>>(
        "/api/custom-fields/",
        { params: { entity } },
      );
      return data.results;
    },
  });
}

export function useSavedViews(entity: string) {
  return useQuery({
    queryKey: ["saved-views", entity],
    queryFn: async () => {
      const { data } = await api.get<Paginated<SavedView>>("/api/saved-views/", {
        params: { entity },
      });
      return data.results;
    },
  });
}

export function useCreateSavedView() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      entity: string;
      name: string;
      params: Record<string, string>;
    }) => {
      const { data } = await api.post<SavedView>("/api/saved-views/", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["saved-views"] }),
  });
}

export function useBulkLeads() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      ids: number[];
      action: "set_status" | "set_owner" | "add_tag" | "delete";
      status?: string;
      owner?: number | null;
      tag?: number;
    }) => {
      const { data } = await api.post("/api/leads/bulk/", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["leads"] }),
  });
}

export function useImportLeads() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      const { data } = await api.post<{ created: number; errors: unknown[] }>(
        "/api/leads/import_csv/",
        form,
      );
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["leads"] }),
  });
}

// --- Phase 9: notifications -------------------------------------------------

export function useNotifications() {
  return useQuery({
    queryKey: ["notifications"],
    queryFn: async () => {
      const { data } = await api.get<Paginated<AppNotification>>(
        "/api/notifications/",
      );
      return data.results;
    },
    refetchInterval: 15_000, // poll until WebSockets (iteration 2)
  });
}

export function useUnreadCount() {
  return useQuery({
    queryKey: ["notifications", "unread"],
    queryFn: async () => {
      const { data } = await api.get<{ unread: number }>(
        "/api/notifications/unread_count/",
      );
      return data.unread;
    },
    refetchInterval: 15_000,
  });
}

export function useMarkNotificationRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.post(`/api/notifications/${id}/mark_read/`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });
}

export function useMarkAllRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await api.post("/api/notifications/mark_all_read/");
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });
}

// --- Phase 10: API keys -----------------------------------------------------

export function useApiKeys() {
  return useQuery({
    queryKey: ["api-keys"],
    queryFn: async () => {
      const { data } = await api.get<Paginated<ApiKey>>("/api/api-keys/");
      return data.results;
    },
  });
}

export function useCreateApiKey() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { name: string; scopes: string[] }) => {
      const { data } = await api.post<ApiKeyCreated>("/api/api-keys/", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["api-keys"] }),
  });
}

export function useRevokeApiKey() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/api/api-keys/${id}/`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["api-keys"] }),
  });
}

// --- Phase 11: webhooks -----------------------------------------------------

export function useWebhooks() {
  return useQuery({
    queryKey: ["webhooks"],
    queryFn: async () => {
      const { data } = await api.get<Paginated<WebhookEndpoint>>("/api/webhooks/");
      return data.results;
    },
  });
}

export function useCreateWebhook() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      url: string;
      events: string[];
      description?: string;
    }) => {
      const { data } = await api.post<WebhookEndpoint>("/api/webhooks/", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["webhooks"] }),
  });
}

export function useDeleteWebhook() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/api/webhooks/${id}/`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["webhooks"] }),
  });
}

export function useWebhookDeliveries() {
  return useQuery({
    queryKey: ["webhook-deliveries"],
    queryFn: async () => {
      const { data } = await api.get<Paginated<WebhookDelivery>>(
        "/api/webhook-deliveries/",
      );
      return data.results;
    },
    refetchInterval: 10_000,
  });
}

export function useReplayDelivery() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.post(`/api/webhook-deliveries/${id}/replay/`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["webhook-deliveries"] }),
  });
}

// --- Phase 11.6: inbound webhooks -------------------------------------------

export function useInboundEndpoints() {
  return useQuery({
    queryKey: ["inbound-endpoints"],
    queryFn: async () => {
      const { data } = await api.get<Paginated<InboundEndpoint>>(
        "/api/inbound-endpoints/",
      );
      return data.results;
    },
  });
}

export function useCreateInboundEndpoint() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { source: string; action: string }) => {
      const { data } = await api.post<InboundEndpoint>(
        "/api/inbound-endpoints/",
        payload,
      );
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["inbound-endpoints"] }),
  });
}

export function useDeleteInboundEndpoint() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/api/inbound-endpoints/${id}/`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["inbound-endpoints"] }),
  });
}

// --- Phase 12: connections / integrations -----------------------------------

export function useConnectionProviders() {
  return useQuery({
    queryKey: ["connection-providers"],
    queryFn: async () => {
      const { data } = await api.get<ConnectionProvider[]>(
        "/api/connections/providers/",
      );
      return data;
    },
  });
}

export function useConnections() {
  return useQuery({
    queryKey: ["connections"],
    queryFn: async () => {
      const { data } = await api.get<Paginated<Connection>>("/api/connections/");
      return data.results;
    },
  });
}

export function useAuthorizeConnection() {
  return useMutation({
    mutationFn: async (payload: { provider: string; redirect_uri: string }) => {
      const { data } = await api.post<{ authorize_url: string }>(
        "/api/connections/authorize/",
        payload,
      );
      return data;
    },
  });
}

export function useCompleteOAuth() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { state: string; code: string }) => {
      const { data } = await api.post<Connection>(
        "/api/connections/callback/",
        payload,
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["connections"] });
      qc.invalidateQueries({ queryKey: ["connection-providers"] });
    },
  });
}

export function useDisconnect() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/api/connections/${id}/`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["connections"] });
      qc.invalidateQueries({ queryKey: ["connection-providers"] });
    },
  });
}
