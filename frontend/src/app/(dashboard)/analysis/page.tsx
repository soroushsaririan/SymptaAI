"use client";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Brain, CheckCircle2, Clock, XCircle, Loader2 } from "lucide-react";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { analysisApi, patientsApi } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";

const STATUS_ICON: Record<string, React.ReactNode> = {
  completed: <CheckCircle2 className="h-4 w-4 text-green-500" />,
  failed: <XCircle className="h-4 w-4 text-red-500" />,
  running: <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />,
  pending: <Clock className="h-4 w-4 text-muted-foreground" />,
  cancelled: <XCircle className="h-4 w-4 text-muted-foreground" />,
};

export default function AnalysisListPage() {
  const { data: patients } = useQuery({
    queryKey: ["patients"],
    queryFn: () => patientsApi.list({ limit: 100 }),
  });

  const patientMap = Object.fromEntries(
    (patients?.items ?? []).map((p) => [p.id, `${p.first_name} ${p.last_name}`])
  );

  const { data: runs, isLoading } = useQuery({
    queryKey: ["analysis-all"],
    queryFn: async () => {
      const ids = patients?.items.map((p) => p.id) ?? [];
      const results = await Promise.all(ids.map((id) => analysisApi.history(id)));
      return results.flat().sort((a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
    },
    enabled: !!patients,
  });

  return (
    <div className="flex flex-col h-full">
      <Header title="AI Analysis" description={`${runs?.length ?? "—"} total runs`} />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-4xl space-y-3">
          {isLoading || !runs ? (
            Array.from({ length: 5 }).map((_, i) => (
              <Card key={i}><CardContent className="pt-4 pb-4 space-y-2">
                <Skeleton className="h-4 w-64" /><Skeleton className="h-3 w-40" />
              </CardContent></Card>
            ))
          ) : runs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 gap-3 text-muted-foreground">
              <Brain className="h-12 w-12 opacity-20" />
              <p className="text-sm">No analyses run yet</p>
              <p className="text-xs">Open a patient and click "Run AI Analysis" to start</p>
            </div>
          ) : (
            runs.map((run, i) => (
              <motion.div key={run.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}>
                <Link href={`/analysis/${run.id}`}>
                  <Card className="hover:border-primary/50 transition-colors cursor-pointer">
                    <CardContent className="pt-4 pb-4">
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3 min-w-0">
                          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 shrink-0">
                            <Brain className="h-4 w-4 text-primary" />
                          </div>
                          <div className="min-w-0">
                            <p className="font-medium text-sm truncate">
                              {patientMap[run.patient_id] ?? "Unknown Patient"}
                            </p>
                            <p className="text-xs text-muted-foreground mt-0.5">
                              {formatRelativeTime(run.created_at)}
                              {run.tokens_used > 0 && ` · ${run.tokens_used} tokens`}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          {STATUS_ICON[run.status]}
                          <Badge variant={run.status === "completed" ? "success" : run.status === "failed" ? "destructive" : "secondary"}>
                            {run.status}
                          </Badge>
                        </div>
                      </div>
                      {run.steps_completed?.length > 0 && (
                        <p className="text-xs text-muted-foreground mt-2 pl-12">
                          {run.steps_completed.length}/8 agents completed
                        </p>
                      )}
                    </CardContent>
                  </Card>
                </Link>
              </motion.div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
