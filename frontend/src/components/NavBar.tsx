import { NavLink } from "react-router-dom";

const navItems = [
  { to: "/", label: "Triage Dashboard" },
  { to: "/collector", label: "Hunt & Collect" },
  { to: "/alerts", label: "Alert Center" },
  { to: "/settings", label: "System Health" },
];

export function NavBar() {
  return (
    <nav className="flex flex-wrap gap-2">
      {navItems.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          className={({ isActive }) =>
            `rounded-full px-4 py-2 text-sm font-semibold transition ${
              isActive
                ? "bg-white text-ink shadow-lg"
                : "bg-white/10 text-slate-200 hover:bg-white/20 hover:text-white"
            }`
          }
        >
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}
