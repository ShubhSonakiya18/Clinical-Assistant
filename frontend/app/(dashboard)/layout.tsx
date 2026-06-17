"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { isAuthenticated, clearTokens, getRefreshToken } from "@/lib/auth";
import { auth } from "@/lib/api";
import type { MeResponse } from "@/lib/types";
import { LayoutDashboard, Plus, Users, Settings, LogOut } from "lucide-react";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [me, setMe] = useState<MeResponse | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    auth.me().then(setMe).catch(() => {
      clearTokens();
      router.replace("/login");
    });
  }, [router]);

  async function handleLogout() {
    const rt = getRefreshToken();
    if (rt) {
      try { await auth.logout(rt); } catch {}
    }
    clearTokens();
    router.replace("/login");
  }

  const navItems = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/consultations/new", label: "New Consultation", icon: Plus },
    { href: "/patients", label: "Patients", icon: Users },
    { href: "/settings", label: "Settings", icon: Settings },
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-56 bg-white border-r border-gray-200 flex flex-col">
        <div className="px-5 py-5 border-b border-gray-100">
          <span className="text-base font-bold text-blue-600">Clinical Assistant</span>
          {me && (
            <p className="text-xs text-gray-400 mt-1 truncate">Dr. {me.user.full_name}</p>
          )}
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-blue-50 hover:text-blue-700 transition-colors"
            >
              <Icon size={16} />
              {label}
            </Link>
          ))}
        </nav>
        {me && (
          <div className="px-3 py-4 border-t border-gray-100">
            <div className="px-3 py-2 text-xs text-gray-400">
              {me.doctor.subscription_tier === "free"
                ? `${me.doctor.consultations_this_month}/${me.doctor.free_quota} free consultations`
                : "Pro plan"}
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-500 hover:text-red-600 hover:bg-red-50 transition-colors w-full"
            >
              <LogOut size={16} />
              Sign out
            </button>
          </div>
        )}
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
