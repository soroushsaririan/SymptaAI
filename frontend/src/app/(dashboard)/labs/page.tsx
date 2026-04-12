"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { FlaskConical, AlertTriangle } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { labsApi, patientsApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";

const SEVERITY_VARIANT: Record<string, "destructive" | "warning" | "secondary"> = {
  critical: "destructive",
  high: "destructive",
  low: "warning",
};

export default function LabsPage() {
  const [patientId, setPatientId] = useState<string>("all");

  const { data: patients } = useQuery({
    queryKey: ["patients"],
    queryFn: () => patientsApi.list({ limit: 100 }),
  });

  const { data: labs, isLoading } = useQuery({
    queryKey: ["labs", patientId],
    queryFn: () => labsApi.list(patientId === "all" ? undefined : patientId, { limit: 100 }),
  });

  const patientMap = Object.fromEntries(
    (patients?.items ?? []).map((p) => [p.id, `${p.first_name} ${p.last_name}`])
  );

  return (
    <div className="flex flex-col h-full">
      <Header title="Lab Results" description={`${labs?.total ?? "—"} results`} />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-4xl space-y-5">
          <Select value={patientId} onValueChange={setPatientId}>
            <SelectTrigger className="w-56">
              <SelectValue placeholder="Filter by patient" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All patients</SelectItem>
              {patients?.items.map((p) => (
                <SelectItem key={p.id} value={p.id}>
                  {p.first_name} {p.last_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="space-y-2">
            {isLoading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <Card key={i}><CardContent className="pt-3 pb-3 space-y-1">
                  <Skeleton className="h-4 w-48" /><Skeleton className="h-3 w-32" />
                </CardContent></Card>
              ))
            ) : labs?.items.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-24 gap-3 text-muted-foreground">
                <FlaskConical className="h-12 w-12 opacity-20" />
                <p className="text-sm">No lab results found</p>
              </div>
            ) : (
              labs?.items.map((lab, i) => (
                <motion.div key={lab.id} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}>
                  <Card className={lab.is_abnormal ? "border-destructive/30" : ""}>
                    <CardContent className="pt-3 pb-3">
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3 min-w-0">
                          {lab.is_abnormal && <AlertTriangle className="h-4 w-4 text-destructive shrink-0" />}
                          <div className="min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-sm">{lab.test_name}</span>
                              {lab.test_code && <span className="text-xs text-muted-foreground">({lab.test_code})</span>}
                            </div>
                            <p className="text-xs text-muted-foreground mt-0.5">
                              {patientMap[lab.patient_id] ?? "Unknown"} · {formatDate(lab.collected_at)}
                              {lab.reference_range && ` · Ref: ${lab.reference_range}`}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <span className={`font-mono text-sm font-semibold ${lab.is_abnormal ? "text-destructive" : ""}`}>
                            {lab.value} {lab.unit}
                          </span>
                          {lab.abnormality_severity && (
                            <Badge variant={SEVERITY_VARIANT[lab.abnormality_severity] ?? "secondary"}>
                              {lab.abnormality_severity}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
