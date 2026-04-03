"use client";
import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft, CheckCircle2, XCircle, Loader2, Brain, FileText,
  AlertTriangle, ChevronDown, ChevronUp, Download,
} from "lucide-react";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { analysisApi } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { StreamEvent } from "@/types";

const AGENT_LABELS: Record<string, { label: string; icon: string }> = {
  patient_intake:        { label: "Patient Intake",        icon: "🏥" },
  medical_record_summarizer: { label: "Record Summarizer", icon: "📋" },
  symptom_analysis:      { label: "Symptom Analysis",      icon: "🔍" },
  lab_interpretation:    { label: "Lab Interpretation",    icon: "🧪" },
  drug_interaction:      { label: "Drug Interaction Check", icon: "💊" },
  differential_diagnosis:{ label: "Differential Diagnosis", icon: "🧠" },
  care_plan:             { label: "Care Plan Generation",  icon: "📝" },
  clinical_report:       { label: "Clinical Report",       icon: "📄" },
};

interface AgentStep {
  agent: string;
  status: "pending" | "running" | "completed" | "failed";
  thought?: string;
  startedAt?: number;
  completedAt?: number;
  error?: string;
}

const AGENT_ORDER = Object.keys(AGENT_LABELS);

export default function AnalysisPage() {
  const { runId } = useParams<{ runId: string }>();
  const router = useRouter();
  const [steps, setSteps] = useState<AgentStep[]>(
    AGENT_ORDER.map((agent) => ({ agent, status: "pending" }))
  );
  const [currentThought, setCurrentThought] = useState<string>("");
  const [streamDone, setStreamDone] = useState(false);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [tokensUsed, setTokensUsed] = useState(0);
  const eventSourceRef = useRef<EventSource | null>(null);
  const thoughtBoxRef = useRef<HTMLDivElement>(null);

  const { data: run } = useQuery({
    queryKey: ["run", runId],
    queryFn: () => analysisApi.get(runId),
    refetchInterval: streamDone ? false : 3000,
  });

  useEffect(() => {
    // streamUrl() already includes ?token=...
    const url = analysisApi.streamUrl(runId);
    const es = new EventSource(url);
    eventSourceRef.current = es;
    let done = false;

    const finish = (error?: string) => {
      if (done) return;
      done = true;
      es.close();
      setStreamDone(true);
      if (error) setStreamError(error);
    };

    es.onmessage = (e) => {
      try {
        const event: StreamEvent = JSON.parse(e.data);
        const type = event.event_type ?? event.type;
        const agent = event.agent_name ?? event.agent;

        if (type === "done") { finish(); return; }

        if (type === "step_complete" && agent) {
          setSteps((prev) => prev.map((s) =>
            s.agent === agent ? { ...s, status: "completed", completedAt: Date.now() } : s
          ));
        } else if (type === "step_start" && agent) {
          setSteps((prev) => prev.map((s) =>
            s.agent === agent ? { ...s, status: "running", startedAt: Date.now() } : s
          ));
        } else if (type === "agent_thought" || type === "token") {
          const thought = event.thought ?? event.token ?? "";
          if (thought && agent) {
            setCurrentThought((prev) => prev + thought);
            setSteps((prev) => prev.map((s) =>
              s.agent === agent ? { ...s, thought: (s.thought ?? "") + thought, status: "running" } : s
            ));
            setTimeout(() => thoughtBoxRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
          }
        } else if (type === "workflow_complete") {
          if (event.tokens_used) setTokensUsed(event.tokens_used);
          // Mark any still-running steps as completed
          setSteps((prev) => prev.map((s) =>
            s.status === "running" ? { ...s, status: "completed", completedAt: Date.now() } : s
          ));
          finish();
        } else if (type === "workflow_error") {
          finish(event.error ?? "An error occurred during analysis");
        }
      } catch {
        // Ignore parse errors
      }
    };

    // onerror fires on normal close too — only treat as error if not already done
    es.onerror = () => {
      if (!done) finish("Connection to analysis server lost");
    };

    return () => { done = true; es.close(); };
  }, [runId]);

  function handleStreamEvent(event: StreamEvent) {
    if (event.type === "token" && event.token) {
      setCurrentThought((prev) => prev + event.token);
    }
  }

  const completedCount = steps.filter((s) => s.status === "completed").length;
  const failedCount = steps.filter((s) => s.status === "failed").length;
  const progress = (completedCount / AGENT_ORDER.length) * 100;
  const reportId = run?.report_id;

  return (
    <div className="flex flex-col h-full">
      <Header
        title="AI Clinical Analysis"
        description={run ? `Patient: ${run.patient_id}` : "Running analysis..."}
        action={
          <div className="flex items-center gap-2">
            <Link href={`/patients/${run?.patient_id}`}>
              <Button variant="ghost" size="sm" className="gap-1.5">
                <ArrowLeft className="h-4 w-4" /> Patient
              </Button>
            </Link>
            {streamDone && reportId && (
              <Link href={`/reports/${reportId}`}>
                <Button size="sm" className="gap-1.5">
                  <FileText className="h-4 w-4" /> View Report
                </Button>
              </Link>
            )}
          </div>
        }
      />

      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-3xl mx-auto space-y-5">
          {/* Progress header */}
          <Card>
            <CardContent className="pt-5 pb-5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  {streamDone ? (
                    streamError ? (
                      <XCircle className="h-5 w-5 text-destructive" />
                    ) : (
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                    )
                  ) : (
                    <Loader2 className="h-5 w-5 animate-spin text-primary" />
                  )}
                  <span className="font-semibold">
                    {streamDone
                      ? streamError
                        ? "Analysis Failed"
                        : "Analysis Complete"
                      : "Analysis in Progress"}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-sm text-muted-foreground">
                  <span>{completedCount}/{AGENT_ORDER.length} agents</span>
                  {failedCount > 0 && (
                    <Badge variant="destructive">{failedCount} failed</Badge>
                  )}
                  {tokensUsed > 0 && (
                    <span>{tokensUsed.toLocaleString()} tokens</span>
                  )}
                </div>
              </div>
              <Progress value={progress} className="h-1.5" />
              {streamError && (
                <p className="text-sm text-destructive mt-2">{streamError}</p>
              )}
            </CardContent>
          </Card>

          {/* Agent timeline */}
          <div className="space-y-2">
            {steps.map((step, i) => {
              const meta = AGENT_LABELS[step.agent];
              const isExpanded = expanded[step.agent];
              const duration = step.startedAt && step.completedAt
                ? ((step.completedAt - step.startedAt) / 1000).toFixed(1)
                : null;

              return (
                <motion.div
                  key={step.agent}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <Card className={`transition-colors ${
                    step.status === "running" ? "border-primary/50 bg-primary/5" :
                    step.status === "failed" ? "border-destructive/50" : ""
                  }`}>
                    <CardContent className="pt-4 pb-4">
                      <button
                        className="w-full flex items-center gap-3 text-left"
                        onClick={() => step.thought && setExpanded((p) => ({ ...p, [step.agent]: !p[step.agent] }))}
                      >
                        {/* Status icon */}
                        <div className="shrink-0">
                          {step.status === "pending" && (
                            <div className="h-6 w-6 rounded-full border-2 border-border" />
                          )}
                          {step.status === "running" && (
                            <Loader2 className="h-5 w-5 animate-spin text-primary" />
                          )}
                          {step.status === "completed" && (
                            <CheckCircle2 className="h-5 w-5 text-green-500" />
                          )}
                          {step.status === "failed" && (
                            <XCircle className="h-5 w-5 text-destructive" />
                          )}
                        </div>

                        {/* Agent info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-lg leading-none">{meta?.icon}</span>
                            <span className="font-medium text-sm">{meta?.label}</span>
                            {step.status === "running" && (
                              <Badge variant="outline" className="text-xs text-primary border-primary/50 animate-pulse">
                                Processing
                              </Badge>
                            )}
                          </div>
                          {step.status === "running" && step.thought && (
                            <p className="text-xs text-muted-foreground mt-1 truncate">{step.thought}</p>
                          )}
                          {step.status === "failed" && step.error && (
                            <p className="text-xs text-destructive mt-1">{step.error}</p>
                          )}
                        </div>

                        {/* Duration + expand */}
                        <div className="flex items-center gap-2 shrink-0">
                          {duration && (
                            <span className="text-xs text-muted-foreground">{duration}s</span>
                          )}
                          {step.thought && (
                            isExpanded ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />
                          )}
                        </div>
                      </button>

                      {/* Expandable thought content */}
                      <AnimatePresence>
                        {isExpanded && step.thought && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden"
                          >
                            <Separator className="my-3" />
                            <p className="text-xs text-muted-foreground font-mono leading-relaxed whitespace-pre-wrap">
                              {step.thought}
                            </p>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>

          {/* Live thought stream */}
          {!streamDone && currentThought && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              ref={thoughtBoxRef}
            >
              <Card className="border-primary/30">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Brain className="h-4 w-4 text-primary animate-pulse" />
                    Live Agent Reasoning
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-muted-foreground font-mono leading-relaxed whitespace-pre-wrap max-h-48 overflow-auto">
                    {currentThought}
                    <span className="inline-block h-3 w-1 bg-primary animate-pulse ml-0.5 translate-y-0.5" />
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Completion CTA */}
          {streamDone && !streamError && reportId && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
              <Card className="border-green-500/30 bg-green-500/5">
                <CardContent className="pt-5 pb-5">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-green-400">Analysis complete!</p>
                      <p className="text-sm text-muted-foreground mt-0.5">
                        The clinical report has been generated and is ready for review.
                      </p>
                    </div>
                    <Link href={`/reports/${reportId}`}>
                      <Button className="gap-1.5 bg-green-600 hover:bg-green-700">
                        <FileText className="h-4 w-4" /> Open Report
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
