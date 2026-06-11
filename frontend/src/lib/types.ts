// API types mirroring the DRF serializers.

export type Role = "owner" | "admin" | "manager" | "sales_rep" | "viewer";

export const ROLE_LEVEL: Record<Role, number> = {
  owner: 4,
  admin: 3,
  manager: 2,
  sales_rep: 1,
  viewer: 0,
};

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface Tenant {
  id: number;
  name: string;
  slug: string;
  is_active: boolean;
  created_at: string;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  date_joined: string;
}

export type LeadStatus =
  | "new"
  | "contacted"
  | "qualified"
  | "unqualified"
  | "converted";

export interface Lead {
  id: number;
  name: string;
  email: string;
  phone: string;
  company: string;
  source: string;
  status: LeadStatus;
  notes: string;
  owner: number | null;
  owner_email: string | null;
  is_stale: boolean;
  created_at: string;
  updated_at: string;
}

export interface Stage {
  id: number;
  name: string;
  order: number;
  is_won: boolean;
  is_lost: boolean;
}

export interface Deal {
  id: number;
  title: string;
  value: string;
  stage: number;
  stage_name: string;
  lead: number | null;
  owner: number | null;
  expected_close_date: string | null;
  closed_at: string | null;
  is_closed: boolean;
  created_at: string;
  updated_at: string;
}

export interface PipelineColumn {
  stage: Stage;
  deals: Deal[];
}

export type Priority = "low" | "medium" | "high";

export interface Task {
  id: number;
  title: string;
  description: string;
  due_date: string | null;
  is_done: boolean;
  priority: Priority;
  assigned_to: number | null;
  lead: number | null;
  deal: number | null;
  created_at: string;
  updated_at: string;
}

export type AuditAction = "created" | "updated" | "deleted";

export interface AuditLog {
  id: number;
  action: AuditAction;
  actor: number | null;
  actor_email: string | null;
  target_model: string | null;
  target_id: number | null;
  target_repr: string;
  changes: Record<string, [unknown, unknown]>;
  created_at: string;
}

export interface Member {
  id: number; // membership id
  email: string;
  full_name: string;
  role: Role;
  created_at: string;
}

export interface AnalyticsSummary {
  leads_total: number;
  leads_stale: number;
  open_deals: number;
  open_pipeline_value: number;
  won_deals: number;
  won_value: number;
  win_rate: number;
}

export interface StageBreakdown {
  stage: string;
  is_won: boolean;
  is_lost: boolean;
  count: number;
  value: number;
}

export interface StatusCount {
  status: LeadStatus;
  count: number;
}

export interface LeadsOverTimePoint {
  day: string;
  count: number;
}
