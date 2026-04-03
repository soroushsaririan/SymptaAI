"use client";
import { motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import { Users, Brain, FileText, AlertCircle, ArrowRight, Plus } from "lucide-react";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { patientsApi, reportsApi, labsApi } from "@/lib/api";
import { formatRelativeTime, calculateAge, getInitials } from "@/lib/utils";

const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.07 } } };
const item = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } };

export default function DashboardPage() {
  const { data: patients, isLoading: loadingPatients } = useQuery({
    queryKey: ["patients"],
    queryFn: () => patientsApi.list({ limit: 5 }),
  });
  const { data: reports, isLoading: loadingReports } = useQuery({
    queryKey: ["reports"],
    queryFn: () => reportsApi.list({ limit: 3 }),
  });

  const stats = [
    { label: "Total Patients", value: patients?.total ?? "—", icon: Users, color: "text-blue-400" },
    { label: "Active Analyses", value: "—", icon: Brain, color: "text-purple-400" },
    { label: "Reports Generated", value: reports?.total ?? "—", icon: FileText, color: "text-green-400" },
    { label: "Critical Labs", value: "—", icon: AlertCircle, color: "text-red-400" },
  ];

  return (
    <div className="flex flex-col h-full">
      <Header title="Dashboard" description="Clinical overview" />
      <div className="flex-1 overflow-auto p-6">
        <motion.div variants={container} initial="hidden" animate="show" className="space-y-6 max-w-6xl">
          {/* Stats */}
          <motion.div variants={item} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {stats.map((s) => (
              <Card key={s.label}>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">{s.label}</p>
                      <p className="text-2xl font-bold mt-1">{s.value}</p>
                    </div>
                    <s.icon className={`h-8 w-8 ${s.color} opacity-70`} />
                  </div>
                </CardContent>
              </Card>
            ))}
          </motion.div>

          <div className="grid lg:grid-cols-2 gap-6">
            {/* Recent Patients */}
            <motion.div variants={item}>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-3">
                  <CardTitle>Recent Patients</CardTitle>
                  <Link href="/patients/new">
                    <Button size="sm" variant="outline" className="gap-1.5">
                      <Plus className="h-3.5 w-3.5" /> New
                    </Button>
                  </Link>
                </CardHeader>
                <CardContent className="space-y-3">
                  {loadingPatients ? (
                    Array.from({ length: 4 }).map((_, i) => (
                      <div key={i} className="flex items-center gap-3">
                        <Skeleton className="h-8 w-8 rounded-full" />
                        <div className="space-y-1.5 flex-1">
                          <Skeleton className="h-3.5 w-32" />
                          <Skeleton className="h-3 w-20" />
                        </div>
                      </div>
                    ))
                  ) : patients?.items.map((p) => (
                    <Link key={p.id} href={`/patients/${p.id}`}
                      className="flex items-center gap-3 hover:bg-secondary/50 rounded-lg p-2 -mx-2 transition-colors"
                    >
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/20 text-primary text-xs font-semibold shrink-0">
                        {getInitials(`${p.first_name} ${p.last_name}`)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{p.first_name} {p.last_name}</p>
                        <p className="text-xs text-muted-foreground">{p.mrn} · {calculateAge(p.date_of_birth)}y {p.gender}</p>
                      </div>
                      <Badge variant={p.intake_completed ? "success" : "secondary"} className="shrink-0">
                        {p.intake_completed ? "Intake done" : "Pending"}
                      </Badge>
                    </Link>
                  ))}
                  {patients && patients.total > 5 && (
                    <Link href="/patients" className="flex items-center gap-1 text-sm text-primary hover:underline pt-1">
                      View all {patients.total} patients <ArrowRight className="h-3.5 w-3.5" />
                    </Link>
                  )}
                </CardContent>
              </Card>
            </motion.div>

            {/* Recent Reports */}
            <motion.div variants={item}>
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle>Recent Reports</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {loadingReports ? (
                    Array.from({ length: 3 }).map((_, i) => (
                      <div key={i} className="space-y-1.5">
                        <Skeleton className="h-4 w-48" />
                        <Skeleton className="h-3 w-32" />
                      </div>
                    ))
                  ) : reports?.items.map((r) => (
                    <Link key={r.id} href={`/reports/${r.id}`}
                      className="block hover:bg-secondary/50 rounded-lg p-3 -mx-1 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <p className="text-sm font-medium truncate">{r.title}</p>
                          <p className="text-xs text-muted-foreground mt-0.5">{formatRelativeTime(r.created_at)}</p>
                        </div>
                        <Badge variant={r.status === "completed" ? "success" : r.status === "failed" ? "destructive" : "secondary"}>
                          {r.status}
                        </Badge>
                      </div>
                    </Link>
                  ))}
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
