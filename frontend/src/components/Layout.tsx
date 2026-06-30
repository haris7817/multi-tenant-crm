import {
  Activity,
  Blocks,
  CheckSquare,
  CreditCard,
  KanbanSquare,
  KeyRound,
  LayoutDashboard,
  LogOut,
  Search,
  Users,
  UsersRound,
  Webhook,
  type LucideIcon,
} from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

import { useNotificationSocket } from "../api/useNotificationSocket";
import { useAuth } from "../auth/AuthContext";
import AIAssistantButton from "./AIAssistantButton";
import NotificationBell from "./NotificationBell";

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  end?: boolean;
  adminOnly?: boolean;
}

const NAV: { section: string; items: NavItem[] }[] = [
  {
    section: "Overview",
    items: [{ to: "/", label: "Dashboard", icon: LayoutDashboard, end: true }],
  },
  {
    section: "Workspace",
    items: [
      { to: "/leads", label: "Leads", icon: Users },
      { to: "/pipeline", label: "Pipeline", icon: KanbanSquare },
      { to: "/tasks", label: "Tasks", icon: CheckSquare },
      { to: "/activity", label: "Activity", icon: Activity },
    ],
  },
  {
    section: "Team",
    items: [{ to: "/members", label: "Members", icon: UsersRound, adminOnly: true }],
  },
  {
    section: "Developers",
    items: [
      { to: "/api-keys", label: "API Keys", icon: KeyRound, adminOnly: true },
      { to: "/webhooks", label: "Webhooks", icon: Webhook, adminOnly: true },
    ],
  },
  {
    section: "Business",
    items: [
      { to: "/integrations", label: "Integrations", icon: Blocks, adminOnly: true },
      { to: "/billing", label: "Billing", icon: CreditCard, adminOnly: true },
    ],
  },
];

function initials(email: string) {
  return email.slice(0, 2).toUpperCase();
}

export default function Layout() {
  const { auth, logout, hasRole } = useAuth();
  useNotificationSocket();
  const [menuOpen, setMenuOpen] = useState(false);

  const groups = NAV.map((g) => ({
    ...g,
    items: g.items.filter((i) => !i.adminOnly || hasRole("admin")),
  })).filter((g) => g.items.length > 0);

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 flex w-60 flex-col border-r border-slate-200 bg-white">
        <div className="flex items-center gap-2.5 px-5 py-4">
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 text-sm font-extrabold text-white shadow-sm">
            ⬡
          </div>
          <div>
            <div className="text-[15px] font-bold leading-none text-slate-900">
              CRM
            </div>
            <div className="text-[11px] text-slate-400">Multi-tenant SaaS</div>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 pb-4">
          {groups.map((group) => (
            <div key={group.section}>
              <div className="nav-section">{group.section}</div>
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      end={item.end}
                      className={({ isActive }) =>
                        `nav-item ${isActive ? "nav-item-active" : ""}`
                      }
                    >
                      <Icon size={17} strokeWidth={2} />
                      {item.label}
                    </NavLink>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        <div className="border-t border-slate-100 px-4 py-3">
          <div className="flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-2">
            <div className="h-2 w-2 rounded-full bg-emerald-500" />
            <span className="truncate text-sm font-medium text-slate-700">
              {auth?.tenantName}
            </span>
          </div>
        </div>
      </aside>

      {/* Main column */}
      <div className="flex flex-1 flex-col pl-60">
        <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-slate-200 bg-white/80 px-6 backdrop-blur">
          <div className="relative w-full max-w-md">
            <Search
              size={16}
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            />
            <input
              className="input border-transparent bg-slate-100 pl-9 shadow-none focus:bg-white"
              placeholder="Search leads, deals, tasks…"
            />
          </div>

          <div className="flex items-center gap-3">
            <NotificationBell />
            <div className="relative">
              <button
                className="flex items-center gap-2 rounded-lg px-1.5 py-1 hover:bg-slate-100"
                onClick={() => setMenuOpen((o) => !o)}
              >
                <div className="grid h-8 w-8 place-items-center rounded-full bg-brand-600 text-xs font-bold text-white">
                  {auth ? initials(auth.email) : "?"}
                </div>
              </button>
              {menuOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setMenuOpen(false)} />
                  <div className="absolute right-0 z-50 mt-2 w-60 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-pop">
                    <div className="border-b border-slate-100 px-4 py-3">
                      <div className="truncate text-sm font-medium text-slate-800">
                        {auth?.email}
                      </div>
                      <span className="badge-slate mt-1 uppercase">{auth?.role}</span>
                    </div>
                    <button
                      className="flex w-full items-center gap-2 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50"
                      onClick={logout}
                    >
                      <LogOut size={16} /> Sign out
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </header>

        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>

      <AIAssistantButton />
    </div>
  );
}
