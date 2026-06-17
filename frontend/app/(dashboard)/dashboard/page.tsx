"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { consultations as consultationsApi } from "@/lib/api";
import type { ConsultationListItem } from "@/lib/types";
import { formatDate, statusLabel, statusColor } from "@/lib/utils";
import { Plus, ChevronRight, Mic } from "lucide-react";

export default function DashboardPage() {
  const [items, setItems] = useState<ConsultationListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    consultationsApi.list(0, 10).then(setItems).finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 text-sm mt-1">Recent consultations</p>
        </div>
        <Link
          href="/consultations/new"
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          <Plus size={16} />
          New Consultation
        </Link>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 bg-gray-100 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-xl border border-gray-200">
          <Mic size={40} className="mx-auto text-gray-300 mb-4" />
          <h3 className="text-gray-700 font-medium mb-1">No consultations yet</h3>
          <p className="text-gray-400 text-sm mb-4">Record your first consultation to get started</p>
          <Link
            href="/consultations/new"
            className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            <Plus size={15} />
            Start your first consultation
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
          {items.map((c) => (
            <Link
              key={c.id}
              href={`/consultations/${c.id}`}
              className="flex items-center justify-between px-5 py-4 hover:bg-gray-50 transition-colors"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3">
                  <span className="font-medium text-gray-900 text-sm">{c.patient_name}</span>
                  {c.patient_age && (
                    <span className="text-xs text-gray-400">{c.patient_age}y</span>
                  )}
                </div>
                {c.chief_complaint && (
                  <p className="text-xs text-gray-400 mt-0.5 truncate max-w-xs">{c.chief_complaint}</p>
                )}
              </div>
              <div className="flex items-center gap-4 ml-4">
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${statusColor(c.status)}`}>
                  {statusLabel(c.status)}
                </span>
                <span className="text-xs text-gray-400">{formatDate(c.consultation_date)}</span>
                <ChevronRight size={16} className="text-gray-300" />
              </div>
            </Link>
          ))}
        </div>
      )}

      {items.length === 10 && (
        <Link
          href="/consultations"
          className="block text-center text-sm text-blue-600 hover:underline mt-4"
        >
          View all consultations
        </Link>
      )}
    </div>
  );
}
