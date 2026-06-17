"use client";

import { useEffect, useState } from "react";
import { auth } from "@/lib/api";
import type { MeResponse } from "@/lib/types";

export default function SettingsPage() {
  const [me, setMe] = useState<MeResponse | null>(null);

  useEffect(() => { auth.me().then(setMe); }, []);

  if (!me) return <div className="p-8 text-gray-400 text-sm">Loading...</div>;

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>

      <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
        <div className="px-5 py-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide font-medium mb-3">Profile</p>
          <div className="space-y-2">
            <Row label="Name" value={`Dr. ${me.user.full_name}`} />
            <Row label="Email" value={me.user.email} />
            {me.user.phone && <Row label="Phone" value={me.user.phone} />}
          </div>
        </div>
        <div className="px-5 py-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide font-medium mb-3">Clinic</p>
          <div className="space-y-2">
            <Row label="Specialization" value={me.doctor.specialization} />
            <Row label="Clinic name" value={me.doctor.clinic_name ?? "—"} />
            <Row label="Language" value={me.doctor.preferred_language} />
          </div>
        </div>
        <div className="px-5 py-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide font-medium mb-3">Subscription</p>
          <div className="space-y-2">
            <Row
              label="Plan"
              value={
                me.doctor.subscription_tier === "pro"
                  ? "Pro — Unlimited"
                  : `Free — ${me.doctor.consultations_this_month}/${me.doctor.free_quota} used this month`
              }
            />
          </div>
          {me.doctor.subscription_tier === "free" && (
            <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg px-4 py-3">
              <p className="text-sm text-blue-800 font-medium">Upgrade to Pro</p>
              <p className="text-xs text-blue-600 mt-0.5 mb-3">
                ₹2,999/month — unlimited consultations, priority support
              </p>
              <a
                href="https://wa.me/your-number?text=I%20want%20to%20upgrade%20to%20Pro"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block bg-blue-600 text-white text-xs font-medium px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Contact to Upgrade
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="text-sm text-gray-900 font-medium">{value}</span>
    </div>
  );
}
