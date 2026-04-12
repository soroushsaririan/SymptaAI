"use client";
import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  ArrowLeft, Brain, FileText, FlaskConical, FolderOpen,
  AlertTriangle, Calendar, User, Phone, Plus, Loader2,
} from "lucide-react";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { patientsApi, analysisApi, labsApi, recordsApi, reportsApi } from "@/lib/api";
import { calculateAge, formatDate, formatRelativeTime, getInitials } from "@/lib/utils";
import toast from "react-hot-toast";

const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

function LabStatusBadge({ flag }: { flag: string | null | undefined }) {
  if (!flag) return <Badge variant="secondary">Normal</Badge>;
  if (flag === "critical_high" || flag === "critical_low")
    return <Badge variant="destructive">Critical</Badge>;
  return <Badge variant="outline" className="text-yellow-500 border-yellow-500/50">Abnormal</Badge>;
}

export default function PatientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const qc = useQueryClient();
  const [activeTab, setActiveTab] = useState("overview");

  const { data: patient, isLoading } = useQuery({
    queryKey: ["patient", id],
    queryFn: () => patientsApi.get(id),
  });

  const { data: labs } = useQuery({
    queryKey: ["labs", id],
    queryFn: () => labsApi.list(id, { limit: 50 }),
    enabled: activeTab === "labs",
  });

  const { data: records } = useQuery({
    queryKey: ["records", id],
    queryFn: () => recordsApi.list(id, { limit: 20 }),
    enabled: activeTab === "records",
  });

  const { data: reports } = useQuery({
    queryKey: ["reports", { patient_id: id }],
    queryFn: () => reportsApi.list({ patient_id: id, limit: 10 }),
    enabled: activeTab === "reports",
  });

  const startAnalysis = useMutation({
    mutationFn: () => analysisApi.start({ patient_id: id, analysis_type: "full" }),
    onSuccess: (run) => {
      toast.success("Analysis started");
      router.push(`/analysis/${run.id}`);
    },
    onError: () => toast.error("Failed to start analysis"),
  });

  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <Header title="Loading..." />
        <div className="p-6 space-y-4 max-w-5xl">
          <Skeleton className="h-32 w-full rounded-xl" />
          <Skeleton className="h-64 w-full rounded-xl" />
        </div>
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="flex flex-col h-full items-center justify-center gap-3">
        <AlertTriangle className="h-10 w-10 text-muted-foreground" />
        <p className="text-muted-foreground">Patient not found</p>
        <Link href="/patients"><Button variant="outline" size="sm">Back to Patients</Button></Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <Header
        title={`${patient.first_name} ${patient.last_name}`}
        description={`MRN: ${patient.mrn} · ${calculateAge(patient.date_of_birth)}y · ${patient.gender}`}
        action={
          <div className="flex items-center gap-2">
            <Link href="/patients">
              <Button variant="ghost" size="sm" className="gap-1.5">
                <ArrowLeft className="h-4 w-4" /> Patients
              </Button>
            </Link>
            <Button
              size="sm"
              className="gap-1.5"
              onClick={() => startAnalysis.mutate()}
              disabled={startAnalysis.isPending}
            >
              {startAnalysis.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Brain className="h-4 w-4" />
              )}
              Run AI Analysis
            </Button>
          </div>
        }
      />

      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-5xl space-y-5">
          {/* Demographics card */}
          <motion.div variants={item} initial="hidden" animate="show">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-start gap-5">
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/20 text-primary text-xl font-bold shrink-0">
                    {getInitials(`${patient.first_name} ${patient.last_name}`)}
                  </div>
                  <div className="flex-1 grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    <InfoItem icon={User} label="Date of Birth" value={`${formatDate(patient.date_of_birth)} (${calculateAge(patient.date_of_birth)} yrs)`} />
                    <InfoItem icon={Calendar} label="Gender" value={patient.gender} />
                    {patient.phone && <InfoItem icon={Phone} label="Phone" value={patient.phone} />}
                    {patient.email && <InfoItem icon={User} label="Email" value={patient.email} />}
                    {patient.address && <InfoItem icon={User} label="Address" value={typeof patient.address === "string" ? patient.address : Object.values(patient.address).join(", ")} />}
                    {patient.insurance_id && <InfoItem icon={User} label="Insurance" value={patient.insurance_id} />}
                  </div>
                  <Badge variant={patient.intake_completed ? "success" : "secondary"} className="shrink-0">
                    {patient.intake_completed ? "Intake Complete" : "Intake Pending"}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger value="overview"><User className="h-3.5 w-3.5 mr-1.5" />Overview</TabsTrigger>
              <TabsTrigger value="labs"><FlaskConical className="h-3.5 w-3.5 mr-1.5" />Lab Results</TabsTrigger>
              <TabsTrigger value="records"><FolderOpen className="h-3.5 w-3.5 mr-1.5" />Records</TabsTrigger>
              <TabsTrigger value="reports"><FileText className="h-3.5 w-3.5 mr-1.5" />Reports</TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview">
              <div className="grid md:grid-cols-2 gap-4 mt-4">
                {/* Allergies */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-yellow-500" /> Allergies
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {patient.allergies && patient.allergies.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {patient.allergies.map((a: string, i: number) => (
                          <Badge key={i} variant="outline" className="text-yellow-500 border-yellow-500/50">{a}</Badge>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">No known allergies</p>
                    )}
                  </CardContent>
                </Card>

                {/* Current Medications */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">Current Medications</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {patient.current_medications && patient.current_medications.length > 0 ? (
                      <div className="space-y-2">
                        {patient.current_medications.map((med: { name: string; dose: string; frequency: string }, i: number) => (
                          <div key={i} className="flex items-center justify-between text-sm">
                            <span className="font-medium">{med.name}</span>
                            <span className="text-muted-foreground">{med.dose} · {med.frequency}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">No current medications</p>
                    )}
                  </CardContent>
                </Card>

                {/* Medical History */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">Medical History</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {patient.medical_history && patient.medical_history.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {patient.medical_history.map((h: string | { condition: string }, i: number) => (
                          <Badge key={i} variant="secondary">{typeof h === "string" ? h : h.condition}</Badge>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">No medical history recorded</p>
                    )}
                  </CardContent>
                </Card>

                {/* Vitals */}
                {patient.vitals && (
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base">Latest Vitals</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-3">
                        {patient.vitals.blood_pressure && (
                          <VitalItem label="BP" value={patient.vitals.blood_pressure} unit="mmHg" />
                        )}
                        {patient.vitals.heart_rate && (
                          <VitalItem label="HR" value={patient.vitals.heart_rate} unit="bpm" />
                        )}
                        {patient.vitals.temperature && (
                          <VitalItem label="Temp" value={patient.vitals.temperature} unit="°F" />
                        )}
                        {patient.vitals.oxygen_saturation && (
                          <VitalItem label="SpO2" value={patient.vitals.oxygen_saturation} unit="%" />
                        )}
                        {patient.vitals.respiratory_rate && (
                          <VitalItem label="RR" value={patient.vitals.respiratory_rate} unit="/min" />
                        )}
                        {patient.vitals.weight_kg && (
                          <VitalItem label="Weight" value={patient.vitals.weight_kg} unit="kg" />
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Chief Complaint */}
                {patient.chief_complaint && (
                  <Card className="md:col-span-2">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base">Chief Complaint</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm">{patient.chief_complaint}</p>
                    </CardContent>
                  </Card>
                )}
              </div>
            </TabsContent>

            {/* Labs Tab */}
            <TabsContent value="labs">
              <div className="mt-4 space-y-3">
                {!labs ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-14 w-full" />
                  ))
                ) : labs.items.length === 0 ? (
                  <EmptyState icon={FlaskConical} message="No lab results on file" />
                ) : (
                  <Card>
                    <CardContent className="p-0">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left p-3 font-medium text-muted-foreground">Test</th>
                            <th className="text-left p-3 font-medium text-muted-foreground">Value</th>
                            <th className="text-left p-3 font-medium text-muted-foreground">Reference</th>
                            <th className="text-left p-3 font-medium text-muted-foreground">Status</th>
                            <th className="text-left p-3 font-medium text-muted-foreground">Date</th>
                          </tr>
                        </thead>
                        <tbody>
                          {labs.items.map((lab) => (
                            <tr key={lab.id} className="border-b last:border-0 hover:bg-secondary/30">
                              <td className="p-3 font-medium">{lab.test_name}</td>
                              <td className="p-3">{lab.value} {lab.unit}</td>
                              <td className="p-3 text-muted-foreground">{lab.reference_range ?? "—"}</td>
                              <td className="p-3"><LabStatusBadge flag={lab.abnormal_flag} /></td>
                              <td className="p-3 text-muted-foreground">{formatRelativeTime(lab.collected_at)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </CardContent>
                  </Card>
                )}
              </div>
            </TabsContent>

            {/* Records Tab */}
            <TabsContent value="records">
              <div className="mt-4 space-y-3">
                {!records ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} className="h-20 w-full" />
                  ))
                ) : records.items.length === 0 ? (
                  <EmptyState icon={FolderOpen} message="No medical records on file" />
                ) : (
                  records.items.map((rec) => (
                    <Card key={rec.id}>
                      <CardContent className="pt-4 pb-4">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <Badge variant="outline">{rec.record_type.replace("_", " ")}</Badge>
                              <span className="text-xs text-muted-foreground">{formatRelativeTime(rec.created_at)}</span>
                            </div>
                            {rec.chief_complaint && (
                              <p className="text-sm font-medium truncate">{rec.chief_complaint}</p>
                            )}
                            {rec.summary && (
                              <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{rec.summary}</p>
                            )}
                          </div>
                          {rec.provider_name && (
                            <p className="text-xs text-muted-foreground shrink-0">Dr. {rec.provider_name}</p>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </TabsContent>

            {/* Reports Tab */}
            <TabsContent value="reports">
              <div className="mt-4 space-y-3">
                {!reports ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} className="h-20 w-full" />
                  ))
                ) : reports.items.length === 0 ? (
                  <EmptyState icon={FileText} message="No AI reports generated yet" action={
                    <Button size="sm" className="gap-1.5 mt-3" onClick={() => startAnalysis.mutate()} disabled={startAnalysis.isPending}>
                      <Brain className="h-4 w-4" /> Run First Analysis
                    </Button>
                  } />
                ) : (
                  reports.items.map((r) => (
                    <Link key={r.id} href={`/reports/${r.id}`}>
                      <Card className="hover:border-primary/50 transition-colors cursor-pointer">
                        <CardContent className="pt-4 pb-4">
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="text-sm font-medium">{r.title}</p>
                              <p className="text-xs text-muted-foreground mt-0.5">{formatRelativeTime(r.created_at)}</p>
                            </div>
                            <Badge variant={r.status === "completed" ? "success" : r.status === "failed" ? "destructive" : "secondary"}>
                              {r.status}
                            </Badge>
                          </div>
                        </CardContent>
                      </Card>
                    </Link>
                  ))
                )}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}

function InfoItem({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string }) {
  return (
    <div className="flex items-start gap-2">
      <Icon className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-sm font-medium">{value}</p>
      </div>
    </div>
  );
}

function VitalItem({ label, value, unit }: { label: string; value: string | number; unit: string }) {
  return (
    <div className="rounded-lg bg-secondary/50 p-2">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-base font-semibold">{value} <span className="text-xs font-normal text-muted-foreground">{unit}</span></p>
    </div>
  );
}

function EmptyState({ icon: Icon, message, action }: { icon: React.ElementType; message: string; action?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-2 text-muted-foreground">
      <Icon className="h-10 w-10 opacity-30" />
      <p className="text-sm">{message}</p>
      {action}
    </div>
  );
}
