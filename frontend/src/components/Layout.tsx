import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

const NAV = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/leads", label: "Leads", end: false },
  { to: "/pipeline", label: "Pipeline", end: false },
  { to: "/tasks", label: "Tasks", end: false },
  { to: "/activity", label: "Activity", end: false },
  { to: "/members", label: "Members", end: false },
];

export default function Layout() {
  const { auth, logout } = useAuth();

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="flex w-56 flex-col border-r border-slate-200 bg-white">
        <div className="px-5 py-4 text-lg font-bold text-brand-700">CRM</div>
        <nav className="flex-1 space-y-1 px-3">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `block rounded-md px-3 py-2 text-sm font-medium ${
                  isActive
                    ? "bg-brand-50 text-brand-700"
                    : "text-slate-600 hover:bg-slate-100"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-slate-200 px-4 py-3 text-xs text-slate-500">
          {auth?.tenantName}
        </div>
      </aside>

      {/* Main */}
      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
          <div className="text-sm text-slate-500">
            Workspace: <span className="font-medium text-slate-700">{auth?.slug}</span>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-slate-600">{auth?.email}</span>
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium uppercase text-slate-600">
              {auth?.role}
            </span>
            <button className="btn-ghost" onClick={logout}>
              Logout
            </button>
          </div>
        </header>
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
