import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-IN", {
    day: "numeric", month: "short", year: "numeric",
  });
}

export function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString("en-IN", {
    day: "numeric", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

export function statusLabel(status: string): string {
  const map: Record<string, string> = {
    created: "Created",
    uploading: "Uploading",
    uploaded: "Uploaded",
    transcribing: "Transcribing...",
    transcribed: "Transcribed",
    generating: "Generating Note...",
    generated: "Ready for Review",
    approved: "Approved",
    failed: "Failed",
  };
  return map[status] ?? status;
}

export function statusColor(status: string): string {
  if (status === "approved") return "text-green-600 bg-green-50";
  if (status === "generated") return "text-blue-600 bg-blue-50";
  if (status === "failed") return "text-red-600 bg-red-50";
  if (["transcribing", "generating", "uploading"].includes(status))
    return "text-yellow-700 bg-yellow-50";
  return "text-gray-600 bg-gray-100";
}
