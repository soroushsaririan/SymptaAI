"use client";
import { motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import { Users, Brain, FileText, AlertCircle, ArrowRight, Plus, FlaskConical, Activity } from "lucide-react";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { patientsApi, reportsApi, labsApi, dashboardApi } from "@/lib/api";
import { formatRelativeTime, calculateAge, getInitials } from "@/lib/utils";

const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.07 } } };
const item = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } };

export default function DashboardPage() {
  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: () => dashboardApi.stats(),
    refetchInterval: 30000,
  });

  const { data: patients, isLoading: loadingPatients } = useQuery({
    queryKey: ["patients", { limit: 5 }],
    queryFn: () => patientsApi.list({ limit: 5 }),
  });

  const { data: reports, isLoading: loadingReports } = useQuery({
    queryKey: ["reports", { limit: 4 }],
    queryFn: () => reportsApi.list({ limit: 4 }),
  });

  const patientIds = patients?.items.map((p) => p.id) ?? [];
  const { data: criticalLabs } = useQuery({
    queryKey: ["critical-labs", patientIds],
    queryFn: async () => {
      const results = await Promise.all(patientIds.map((id) => labsApi.critical(id)));
      return results.flat().slice(0, 5);
    },
    enabled: patientIds.length > 0,
  });

  const statCards = [
    { label: "Total Patients",    value: stats?.total_patients,   icon: Users,        color: "text-blue-400",   bg: "bg-blue-400/10",   href: "/patients" },
    { label: "Active Analyses",   value: stats?.active_analyses,  icon: Brain,        color: "text-violet-400", bg: "bg-violet-400/10", href: "/analysis"  },
    { label: "Reports Generated", value: stats?.total_reports,    icon: FileText,     color: "text-emerald-400",bg: "bg-emerald-400/10",href: "/reports"   },
    { label: "Critical Labs",     value: stats?.critical_labs,    icon: AlertCircle,  color: "text-red-400",    bg: "bg-red-400/10",    href: "/labs"      },
  ];

  return (
    <div className="flex flex-col h-full">
      <Header
        title="Dashboard"
        description="Clinical overview"
        action={
          <Link href="/patients/new">
            <Button size="sm" className="gap-1.5"><Plus className="h-3.5 w-3.5" /> New Patient</Button>
          </Link>
        }
      />
      <div className="flex-1 overflow-auto p-6">
        <motion.div variants={container} initial="hidden" animate="show" className="space-y-6 max-w-6xl">

          {/* Stats */}
          <motion.div variants={item} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {statCards.map((s) => (
              <Link key={s.label} href={s.href}>
                <Card className="hover:border-primary/40 transition-colors cursor-pointer">
                  <CardContent className="pt-5 pb-5">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">{s.label}</p>
                        {loadingStats ? <Skeleton className="h-7 w-10" /> : <p className="text-2xl font-bold">{s.value ?? "—"}</p>}
                      </div>
                      <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${s.bg}`}>
                        <s.icon className={`h-5 w-5 ${s.color}`} />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </motion.div>

          <div className="grid lg:grid-cols-3 gap-6">
            {/* Recent Patients */}
            <motion.div variants={item}>
              <Card className="h-full">
                <CardHeader className="flex flex-row items-center justify-between pb-3">
                  <CardTitle className="text-sm font-semibold">Recent Patients</CardTitle>
                  <Link href="/patients">
                    <Button size="sm" variant="ghost" className="gap-1 text-xs h-7 text-muted-foreground">View all <ArrowRight className="h-3 w-3" /></Button>
                  </Link>
                </CardHeader>
                <CardContent className="space-y-1">
                  {loadingPatients ? Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="flex items-center gap-3 p-2">
                      <Skeleton className="h-8 w-8 rounded-full shrink-0" />
                      <div className="space-y-1.5 flex-1"><Skeleton className="h-3.5 w-28" /><Skeleton className="h-3 w-20" /></div>
                    </div>
                  )) : patients?.items.map((p) => (
                    <Link key={p.id} href={`/patients/${p.id}`} className="flex items-center gap-3 hover:bg-muted/50 rounded-lg p-2 -mx-1 transition-colors">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/15 text-primary text-xs font-semibold shrink-0">
                        {getInitials(`${p.first_name} ${p.last_name}`)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{p.first_name} {p.last_name}</p>
                        <p className="text-xs text-muted-foreground">{calculateAge(p.date_of_birth)}y · {p.gender}</p>
                      </div>
                    </Link>
                  ))}
                </CardContent>
              </Card>
            </motion.div>

            {/* Recent Reports */}
            <motion.div variants={item}>
              <Card className="h-full">
                <CardHeader className="flex flex-row items-center justify-between pb-3">
                  <CardTitle className="text-sm font-semibold">Recent Reports</CardTitle>
                  <Link href="/reports">
                    <Button size="sm" variant="ghost" className="gap-1 text-xs h-7 text-muted-foreground">View all <ArrowRight className="h-3 w-3" /></Button>
                  </Link>
                </CardHeader>
                <CardContent className="space-y-1">
                  {loadingReports ? Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="space-y-1.5 p-2"><Skeleton className="h-3.5 w-40" /><Skeleton className="h-3 w-24" /></div>
                  )) : reports?.items.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-8 gap-2 text-muted-foreground">
                      <FileText className="h-8 w-8 opacity-20" /><p className="text-xs">No reports yet</p>
                    </div>
                  ) : reports?.items.map((r) => (
                    <Link key={r.id} href={`/reports/${r.id}`} className="block hover:bg-muted/50 rounded-lg p-2 -mx-1 transition-colors">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <p className="text-sm font-medium truncate leading-tight">{r.title}</p>
                          <p className="text-xs text-muted-foreground mt-0.5">{formatRelativeTime(r.created_at)}</p>
                        </div>
                        <Badge variant={r.status === "completed" ? "success" : r.status === "failed" ? "destructive" : "secondary"} className="shrink-0 text-xs">
                          {r.status}
                        </Badge>
                      </div>
                    </Link>
                  ))}
                </CardContent>
              </Card>
            </motion.div>

            {/* Critical Labs */}
            <motion.div variants={item}>
              <Card className="h-full">
                <CardHeader className="flex flex-row items-center justify-between pb-3">
                  <CardTitle className="text-sm font-semibold flex items-center gap-1.5">
                    <AlertCircle className="h-4 w-4 text-red-400" /> Critical Labs
                  </CardTitle>
                  <Link href="/labs">
                    <Button size="sm" variant="ghost" className="gap-1 text-xs h-7 text-muted-foreground">View all <ArrowRight className="h-3 w-3" /></Button>
                  </Link>
                </CardHeader>
                <CardContent className="space-y-2">
                  {!criticalLabs ? Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="flex items-center justify-between p-2"><Skeleton className="h-3.5 w-28" /><Skeleton className="h-3.5 w-16" /></div>
                  )) : criticalLabs.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-8 gap-2 text-muted-foreground">
                      <FlaskConical className="h-8 w-8 opacity-20" /><p className="text-xs">No critical values</p>
                    </div>
                  ) : criticalLabs.map((lab) => (
                    <div key={lab.id} className="flex items-center justify-between rounded-lg px-3 py-2 bg-red-500/5 border border-red-500/10">
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{lab.test_name}</p>
                        <p className="text-xs text-muted-foreground">{formatRelativeTime(lab.collected_at)}</p>
                      </div>
                      <span className="font-mono text-sm font-semibold text-red-400 shrink-0 ml-2">{lab.value} {lab.unit}</span>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Active analysis banner */}
          {stats && stats.active_analyses > 0 && (
            <motion.div variants={item}>
              <Card className="border-violet-500/20 bg-violet-500/5">
                <CardContent className="pt-4 pb-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="relative flex h-2.5 w-2.5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-400 opacity-75" />
                        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-violet-500" />
                      </div>
                      <p className="text-sm font-medium">
                        {stats.active_analyses} analysis {stats.active_analyses === 1 ? "is" : "are"} currently running
                      </p>
                    </div>
                    <Link href="/analysis">
                      <Button size="sm" variant="outline" className="gap-1.5 border-violet-500/30 text-violet-400 hover:bg-violet-500/10">
                        <Activity className="h-3.5 w-3.5" /> View
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

        </motion.div>
      </div>
    </div>
  );
}
