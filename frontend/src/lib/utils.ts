import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { formatDistanceToNow, format, parseISO } from "date-fns";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  const d = typeof date === "string" ? parseISO(date) : date;
  return format(d, "MMM d, yyyy");
}

export function formatDateTime(date: string | Date): string {
  const d = typeof date === "string" ? parseISO(date) : date;
  return format(d, "MMM d, yyyy 'at' h:mm a");
}

export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === "string" ? parseISO(date) : date;
  return formatDistanceToNow(d, { addSuffix: true });
}

export function calculateAge(dob: string): number {
  const birthDate = new Date(dob);
  const today = new Date();
  let age = today.getFullYear() - birthDate.getFullYear();
  const m = today.getMonth() - birthDate.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) age--;
  return age;
}

export function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1).replace(/_/g, " ");
}

export function truncate(str: string, length: number): string {
  return str.length > length ? `${str.slice(0, length)}...` : str;
}

export function formatMRN(mrn: string): string {
  return mrn.toUpperCase();
}

export function getLikelihoodColor(likelihood: string): string {
  switch (likelihood.toLowerCase()) {
    case "high": return "text-red-400 bg-red-400/10 border-red-400/20";
    case "medium": return "text-yellow-400 bg-yellow-400/10 border-yellow-400/20";
    case "low": return "text-green-400 bg-green-400/10 border-green-400/20";
    default: return "text-muted-foreground bg-muted border-border";
  }
}

export function getSeverityColor(severity: string): string {
  switch (severity.toLowerCase()) {
    case "critical": return "text-red-400";
    case "major": case "severe": return "text-orange-400";
    case "moderate": return "text-yellow-400";
    case "minor": case "mild": return "text-blue-400";
    default: return "text-muted-foreground";
  }
}

export function getPriorityColor(priority: string): string {
  switch (priority.toLowerCase()) {
    case "immediate": return "text-red-400 border-red-400/30 bg-red-400/5";
    case "short_term": return "text-yellow-400 border-yellow-400/30 bg-yellow-400/5";
    case "long_term": return "text-green-400 border-green-400/30 bg-green-400/5";
    default: return "text-muted-foreground border-border bg-muted";
  }
}
