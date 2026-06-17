"use client";

import { useEffect, useState } from "react";
import { patients as patientsApi } from "@/lib/api";
import type { Patient } from "@/lib/types";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Plus, Search, X } from "lucide-react";

const schema = z.object({
  name: z.string().min(1, "Name required"),
  age: z.coerce.number().int().positive().optional().or(z.literal("")),
  sex: z.enum(["M", "F", "Other", ""]).optional(),
  phone: z.string().optional(),
});
type FormData = z.infer<typeof schema>;

export default function PatientsPage() {
  const [patientsList, setPatientsList] = useState<Patient[]>([]);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  useEffect(() => {
    const t = setTimeout(() => {
      patientsApi.list(search || undefined).then(setPatientsList);
    }, 300);
    return () => clearTimeout(t);
  }, [search]);

  async function onSubmit(data: FormData) {
    setError(null);
    try {
      const p = await patientsApi.create({
        name: data.name,
        age: data.age ? Number(data.age) : undefined,
        sex: data.sex || undefined,
        phone: data.phone || undefined,
      });
      setPatientsList((prev) => [p, ...prev]);
      reset();
      setShowForm(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add patient");
    }
  }

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Patients</h1>
          <p className="text-gray-500 text-sm mt-1">{patientsList.length} patients</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          <Plus size={15} />
          Add Patient
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-800">New Patient</h2>
            <button onClick={() => setShowForm(false)}><X size={16} className="text-gray-400" /></button>
          </div>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
            <div>
              <input
                {...register("name")}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Full name *"
              />
              {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name.message}</p>}
            </div>
            <div className="grid grid-cols-3 gap-3">
              <input
                {...register("age")}
                type="number"
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Age"
              />
              <select
                {...register("sex")}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
              >
                <option value="">Sex</option>
                <option value="M">Male</option>
                <option value="F">Female</option>
                <option value="Other">Other</option>
              </select>
              <input
                {...register("phone")}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Phone"
              />
            </div>
            {error && <p className="text-red-500 text-xs">{error}</p>}
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={isSubmitting}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white px-4 py-2 rounded-lg text-sm font-medium"
              >
                {isSubmitting ? "Adding..." : "Add Patient"}
              </button>
              <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700">
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="relative mb-4">
        <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Search patients..."
        />
      </div>

      <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
        {patientsList.length === 0 ? (
          <p className="text-center text-gray-400 text-sm py-10">No patients found</p>
        ) : (
          patientsList.map((p) => (
            <div key={p.id} className="px-5 py-3 flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-gray-900">{p.name}</span>
                {(p.age || p.sex) && (
                  <span className="text-xs text-gray-400 ml-2">
                    {p.age && `${p.age}y`}{p.sex && ` · ${p.sex}`}
                  </span>
                )}
              </div>
              {p.phone && <span className="text-xs text-gray-400">{p.phone}</span>}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
