"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Github,
  Home,
  Info,
  Menu,
  Server,
  Star,
  Users,
  X,
} from "lucide-react";
import { useState } from "react";

import { cn } from "@/lib/utils";
import { Switch } from "@/components/ui/switch";
import { ReadOnlyBadge } from "@/components/readonly-indicator";

const navItems = [
  { href: "/", label: "Home", icon: Home },
  { href: "/about", label: "About", icon: Info },
  { href: "/servers", label: "Servers", icon: Server },
  { href: "/levels", label: "Levels", icon: Star },
  { href: "/members", label: "Members", icon: Users },
];

function NavLinks({ pathname, onNavigate }: { pathname: string; onNavigate?: () => void }) {
  return (
    <nav className="flex flex-col gap-1 px-2">
      {navItems.map(({ href, label, icon: Icon }) => {
        const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            onClick={onNavigate}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              active
                ? "bg-sidebar-primary text-sidebar-primary-foreground"
                : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
            )}
          >
            <Icon className="size-4" />
            {label}
          </Link>
        );
      })}
      <a
        href="https://github.com/Natsku123/Hellshade-bot"
        target="_blank"
        rel="noreferrer"
        className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-sidebar-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
      >
        <Github className="size-4" />
        Github
      </a>
    </nav>
  );
}

function DarkModeToggle() {
  const [dark, setDark] = useState(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem("dark") === "true";
  });

  const toggle = (value: boolean) => {
    setDark(value);
    localStorage.setItem("dark", value.toString());
    document.documentElement.classList.toggle("dark", value);
  };

  return (
    <div className="flex items-center justify-between gap-2 px-3 py-2 text-sm text-sidebar-foreground">
      <span>Dark Mode</span>
      <Switch checked={dark} onCheckedChange={toggle} />
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex min-h-screen w-full">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col border-r border-sidebar-border bg-sidebar md:flex">
        <div className="px-4 py-5">
          <p className="text-lg font-semibold text-sidebar-foreground">Hellshade-bot</p>
          <p className="text-sm text-muted-foreground">Multi-purpose Discord bot</p>
          <div className="mt-2">
            <ReadOnlyBadge />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          <NavLinks pathname={pathname} />
        </div>
        <div className="border-t border-sidebar-border">
          <DarkModeToggle />
        </div>
      </aside>

      {mobileOpen ? (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div
            className="fixed inset-0 bg-black/40"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="relative z-50 flex w-64 flex-col border-r border-sidebar-border bg-sidebar">
            <div className="flex items-center justify-between px-4 py-5">
              <div>
                <p className="text-lg font-semibold text-sidebar-foreground">Hellshade-bot</p>
                <p className="text-sm text-muted-foreground">Multi-purpose Discord bot</p>
                <div className="mt-2">
                  <ReadOnlyBadge />
                </div>
              </div>
              <button
                type="button"
                onClick={() => setMobileOpen(false)}
                className="rounded-md p-1 text-sidebar-foreground hover:bg-sidebar-accent"
                aria-label="Close menu"
              >
                <X className="size-5" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto">
              <NavLinks pathname={pathname} onNavigate={() => setMobileOpen(false)} />
            </div>
            <div className="border-t border-sidebar-border">
              <DarkModeToggle />
            </div>
          </aside>
        </div>
      ) : null}

      <div className="flex min-h-screen w-full flex-col md:pl-64">
        <header className="sticky top-0 z-30 flex items-center gap-3 border-b bg-background px-4 py-3 md:hidden">
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            className="rounded-md p-1.5 hover:bg-accent"
            aria-label="Open menu"
          >
            <Menu className="size-5" />
          </button>
          <span className="font-semibold">Hellshade-bot</span>
        </header>

        <main className="flex-1">{children}</main>

        <footer className="border-t px-4 py-4 text-center text-sm text-muted-foreground">
          Hellshade-bot {new Date().getFullYear()}
        </footer>
      </div>
    </div>
  );
}
