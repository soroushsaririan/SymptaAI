"use client";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  ArrowLeft, Download, AlertTriangle, Brain, Pill,
  ClipboardList, Activity, FileText, Loader2,
} from "lucide-react";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { reportsApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { DifferentialDiagnosis, DrugInteraction, CarePlanItem } from "@/types";

const PRIORITY_COLORS: Record<string, string> = {
  immediate: "text-red-400 bg-red-400/10 border-red-400/30",
  urgent: "text-orange-400 bg-orange-400/10 border-orange-400/30",
  routine: "text-blue-400 bg-blue-400/10 border-blue-400/30",
  preventive: "text-green-400 bg-green-400/10 border-green-400/30",
};

const SEVERITY_COLORS: Record<string, string> = {
  contraindicated: "text-red-400 bg-red-400/10 border-red-400/30",
  major: "text-orange-400 bg-orange-400/10 border-orange-400/30",
  moderate: "text-yellow-400 bg-yellow-400/10 border-yellow-400/30",
  minor: "text-blue-400 bg-blue-400/10 border-blue-400/30",
};

export default function ReportDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: report, isLoading } = useQuery({
    queryKey: ["report", id],
    queryFn: () => reportsApi.get(id),
  });

  const downloadPdf = async () => {
    const blob = await reportsApi.exportPdf(id);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `clinical-report-${id}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <Header title="Loading Report..." />
        <div className="p-6 max-w-4xl space-y-4">
          <Skeleton className="h-32 w-full rounded-xl" />
          <Skeleton className="h-48 w-full rounded-xl" />
          <Skeleton className="h-48 w-full rounded-xl" />
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex flex-col h-full items-center justify-center gap-3">
        <AlertTriangle className="h-10 w-10 text-muted-foreground" />
        <p className="text-muted-foreground">Report not found</p>
        <Link href="/reports"><Button variant="outline" size="sm">Back to Reports</Button></Link>
      </div>
    );
  }

  const content = report.content;

  return (
    <div className="flex flex-col h-full">
      <Header
        title={report.title}
        description={`Generated ${formatDate(report.created_at)}`}
        action={
          <div className="flex items-center gap-2">
            <Link href="/reports">
              <Button variant="ghost" size="sm" className="gap-1.5">
                <ArrowLeft className="h-4 w-4" /> Reports
              </Button>
            </Link>
            {report.status === "completed" && (
              <Button size="sm" variant="outline" className="gap-1.5" onClick={downloadPdf}>
                <Download className="h-4 w-4" /> Export PDF
              </Button>
            )}
          </div>
        }
      />

      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-4xl mx-auto space-y-5">
          {report.status !== "completed" && (
            <Card className="border-primary/30 bg-primary/5">
              <CardContent className="pt-4 pb-4 flex items-center gap-3">
                <Loader2 className="h-5 w-5 animate-spin text-primary" />
                <p className="text-sm font-medium">Report is being generated...</p>
              </CardContent>
            </Card>
          )}

          {/* Executive Summary */}
          {content?.executive_summary && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5 text-primary" />
                    Executive Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm leading-relaxed">{content.executive_summary}</p>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Symptom Analysis */}
          {content?.symptom_analysis && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="h-5 w-5 text-blue-400" />
                    Symptom Analysis
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {(content.symptom_analysis.primary_symptoms?.length ?? 0) > 0 && (
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-2">Primary Symptoms</p>
                      <div className="flex flex-wrap gap-2">
                        {content.symptom_analysis.primary_symptoms?.map((s: string, i: number) => (
                          <Badge key={i} variant="secondary">{s}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {(content.symptom_analysis.red_flags?.length ?? 0) > 0 && (
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wider text-destructive mb-2">Red Flags</p>
                      <div className="flex flex-wrap gap-2">
                        {content.symptom_analysis.red_flags?.map((f: string, i: number) => (
                          <Badge key={i} variant="destructive">{f}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {content.symptom_analysis.severity && (
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-muted-foreground">Overall Severity:</span>
                      <Badge variant="outline">{content.symptom_analysis.severity}</Badge>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Differential Diagnoses */}
          {content?.differential_diagnoses && content.differential_diagnoses.length > 0 && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="h-5 w-5 text-purple-400" />
                    Differential Diagnoses
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {content.differential_diagnoses.map((dx: DifferentialDiagnosis, i: number) => (
                      <div key={i} className="rounded-lg border bg-secondary/30 p-4">
                        <div className="flex items-start justify-between gap-3 mb-2">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-muted-foreground">#{i + 1}</span>
                            <span className="font-medium">{dx.diagnosis}</span>
                            {dx.icd10_code && (
                              <code className="text-xs text-muted-foreground bg-secondary px-1.5 py-0.5 rounded">
                                {dx.icd10_code}
                              </code>
                            )}
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <div className="flex items-center gap-1">
                              <div
                                className="h-2 rounded-full bg-primary"
                                style={{ width: `${Math.round((dx.probability ?? 0) * 100)}px`, maxWidth: "80px", minWidth: "8px" }}
                              />
                              <span className="text-xs text-muted-foreground">{Math.round((dx.probability ?? 0) * 100)}%</span>
                            </div>
                          </div>
                        </div>
                        {dx.reasoning && (
                          <p className="text-sm text-muted-foreground leading-relaxed">{dx.reasoning}</p>
                        )}
                        {dx.supporting_findings && dx.supporting_findings.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {dx.supporting_findings.map((f: string, j: number) => (
                              <span key={j} className="text-xs bg-primary/10 text-primary rounded-full px-2 py-0.5">{f}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Drug Interactions */}
          {content?.drug_interactions && content.drug_interactions.length > 0 && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2">
                    <Pill className="h-5 w-5 text-yellow-400" />
                    Drug Interactions
                    <Badge variant="outline" className="text-yellow-400 border-yellow-400/50 ml-1">
                      {content.drug_interactions.length}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {content.drug_interactions.map((interaction: DrugInteraction, i: number) => (
                    <div
                      key={i}
                      className={`rounded-lg border p-3 ${SEVERITY_COLORS[interaction.severity] ?? "border-border"}`}
                    >
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <p className="font-medium text-sm">
                          {interaction.drug1} × {interaction.drug2}
                        </p>
                        <Badge variant="outline" className={SEVERITY_COLORS[interaction.severity]}>
                          {interaction.severity}
                        </Badge>
                      </div>
                      <p className="text-xs opacity-80">{interaction.description}</p>
                      {interaction.recommendation && (
                        <p className="text-xs mt-1.5 font-medium">→ {interaction.recommendation}</p>
                      )}
                    </div>
                  ))}
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Care Plan */}
          {content?.care_plan && content.care_plan.length > 0 && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}>
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2">
                    <ClipboardList className="h-5 w-5 text-green-400" />
                    Care Plan
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {content.care_plan.map((item: CarePlanItem, i: number) => (
                    <div key={i} className={`rounded-lg border p-3 ${PRIORITY_COLORS[item.priority] ?? "border-border"}`}>
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant="outline" className={`text-xs capitalize ${PRIORITY_COLORS[item.priority]}`}>
                              {item.priority}
                            </Badge>
                            <span className="text-xs text-muted-foreground capitalize bg-secondary px-2 py-0.5 rounded">
                              {item.category}
                            </span>
                          </div>
                          <p className="font-medium text-sm">{item.action}</p>
                          {item.rationale && <p className="text-xs opacity-75 mt-0.5">{item.rationale}</p>}
                        </div>
                        {item.timeframe && (
                          <span className="text-xs text-muted-foreground shrink-0">{item.timeframe}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Physician disclaimer */}
          {report.status === "completed" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
              <Separator />
              <p className="text-xs text-muted-foreground text-center py-3 leading-relaxed">
                This AI-generated report is intended as a clinical decision support tool only.
                All diagnoses, treatment decisions, and medical interventions must be reviewed and
                approved by a licensed physician. Not a substitute for clinical judgment.
              </p>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
