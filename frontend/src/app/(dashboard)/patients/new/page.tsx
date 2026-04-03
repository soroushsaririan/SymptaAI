"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, ArrowRight, Check, Loader2, Plus, X } from "lucide-react";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { patientsApi } from "@/lib/api";
import toast from "react-hot-toast";

const STEPS = ["Demographics", "Medical History", "Vitals & Symptoms", "Review"];

const demographicSchema = z.object({
  first_name: z.string().min(1, "Required"),
  last_name: z.string().min(1, "Required"),
  date_of_birth: z.string().min(1, "Required"),
  gender: z.enum(["male", "female", "other", "prefer_not_to_say"]),
  mrn: z.string().min(1, "Required"),
  email: z.string().email().optional().or(z.literal("")),
  phone: z.string().optional(),
  address: z.string().optional(),
  insurance_id: z.string().optional(),
  emergency_contact_name: z.string().optional(),
  emergency_contact_phone: z.string().optional(),
});

type DemographicData = z.infer<typeof demographicSchema>;

export default function NewPatientPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [allergies, setAllergies] = useState<string[]>([]);
  const [allergyInput, setAllergyInput] = useState("");
  const [medications, setMedications] = useState<{ name: string; dose: string; frequency: string }[]>([]);
  const [medInput, setMedInput] = useState({ name: "", dose: "", frequency: "" });
  const [history, setHistory] = useState<string[]>([]);
  const [historyInput, setHistoryInput] = useState("");
  const [chiefComplaint, setChiefComplaint] = useState("");
  const [vitals, setVitals] = useState({
    blood_pressure: "", heart_rate: "", temperature: "",
    oxygen_saturation: "", respiratory_rate: "", weight_kg: "", height_cm: "",
  });
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    getValues,
    setValue,
    watch,
    formState: { errors },
    trigger,
  } = useForm<DemographicData>({
    resolver: zodResolver(demographicSchema),
    defaultValues: { gender: "prefer_not_to_say" },
  });

  const genderValue = watch("gender");

  const addAllergy = () => {
    if (allergyInput.trim()) {
      setAllergies((p) => [...p, allergyInput.trim()]);
      setAllergyInput("");
    }
  };

  const addMed = () => {
    if (medInput.name.trim()) {
      setMedications((p) => [...p, { ...medInput }]);
      setMedInput({ name: "", dose: "", frequency: "" });
    }
  };

  const addHistory = () => {
    if (historyInput.trim()) {
      setHistory((p) => [...p, historyInput.trim()]);
      setHistoryInput("");
    }
  };

  const nextStep = async () => {
    if (step === 0) {
      const valid = await trigger();
      if (!valid) return;
    }
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  };

  const submit = async () => {
    const demo = getValues();
    setSubmitting(true);
    try {
      const patient = await patientsApi.create({
        ...demo,
        allergies,
        current_medications: medications,
        medical_history: history,
        chief_complaint: chiefComplaint || undefined,
        vitals: Object.values(vitals).some(Boolean)
          ? Object.fromEntries(Object.entries(vitals).filter(([, v]) => v !== ""))
          : undefined,
      });
      toast.success("Patient created successfully");
      router.push(`/patients/${patient.id}`);
    } catch {
      toast.error("Failed to create patient");
      setSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <Header
        title="New Patient"
        description="Register a new patient record"
        action={
          <Link href="/patients">
            <Button variant="ghost" size="sm" className="gap-1.5">
              <ArrowLeft className="h-4 w-4" /> Cancel
            </Button>
          </Link>
        }
      />

      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-2xl mx-auto space-y-6">
          {/* Step indicators */}
          <div className="flex items-center gap-0">
            {STEPS.map((s, i) => (
              <div key={s} className="flex items-center flex-1 last:flex-none">
                <div className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold transition-colors ${
                  i < step ? "bg-primary text-primary-foreground" :
                  i === step ? "bg-primary/20 text-primary ring-2 ring-primary" :
                  "bg-secondary text-muted-foreground"
                }`}>
                  {i < step ? <Check className="h-4 w-4" /> : i + 1}
                </div>
                <div className="hidden sm:block ml-2 text-xs font-medium text-muted-foreground">{s}</div>
                {i < STEPS.length - 1 && (
                  <div className={`flex-1 h-px mx-3 transition-colors ${i < step ? "bg-primary" : "bg-border"}`} />
                )}
              </div>
            ))}
          </div>

          <AnimatePresence mode="wait">
            <motion.div
              key={step}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              {/* Step 0: Demographics */}
              {step === 0 && (
                <Card>
                  <CardHeader><CardTitle>Patient Demographics</CardTitle></CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid sm:grid-cols-2 gap-4">
                      <Input label="First Name *" error={errors.first_name?.message} {...register("first_name")} placeholder="Jane" />
                      <Input label="Last Name *" error={errors.last_name?.message} {...register("last_name")} placeholder="Doe" />
                    </div>
                    <div className="grid sm:grid-cols-2 gap-4">
                      <Input label="Date of Birth *" type="date" error={errors.date_of_birth?.message} {...register("date_of_birth")} />
                      <div className="space-y-1.5">
                        <label className="text-sm font-medium">Gender *</label>
                        <Select value={genderValue} onValueChange={(v) => setValue("gender", v as DemographicData["gender"])}>
                          <SelectTrigger><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="male">Male</SelectItem>
                            <SelectItem value="female">Female</SelectItem>
                            <SelectItem value="other">Other</SelectItem>
                            <SelectItem value="prefer_not_to_say">Prefer not to say</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <Input label="Medical Record Number (MRN) *" error={errors.mrn?.message} {...register("mrn")} placeholder="MRN-2024-001" />
                    <div className="grid sm:grid-cols-2 gap-4">
                      <Input label="Email" type="email" error={errors.email?.message} {...register("email")} placeholder="patient@email.com" />
                      <Input label="Phone" {...register("phone")} placeholder="+1 (555) 000-0000" />
                    </div>
                    <Textarea label="Address" {...register("address")} placeholder="123 Main St, City, State ZIP" rows={2} />
                    <div className="grid sm:grid-cols-2 gap-4">
                      <Input label="Insurance ID" {...register("insurance_id")} placeholder="INS-123456" />
                    </div>
                    <div className="border-t pt-4">
                      <p className="text-sm font-medium mb-3">Emergency Contact</p>
                      <div className="grid sm:grid-cols-2 gap-4">
                        <Input label="Name" {...register("emergency_contact_name")} placeholder="John Doe" />
                        <Input label="Phone" {...register("emergency_contact_phone")} placeholder="+1 (555) 000-0000" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Step 1: Medical History */}
              {step === 1 && (
                <Card>
                  <CardHeader><CardTitle>Medical History</CardTitle></CardHeader>
                  <CardContent className="space-y-6">
                    {/* Allergies */}
                    <div className="space-y-3">
                      <label className="text-sm font-medium">Allergies</label>
                      <div className="flex gap-2">
                        <input
                          value={allergyInput}
                          onChange={(e) => setAllergyInput(e.target.value)}
                          onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addAllergy())}
                          placeholder="e.g. Penicillin, Shellfish..."
                          className="flex-1 h-9 rounded-md border border-input bg-transparent px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                        />
                        <Button type="button" variant="outline" size="sm" onClick={addAllergy}><Plus className="h-4 w-4" /></Button>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {allergies.map((a, i) => (
                          <span key={i} className="flex items-center gap-1 rounded-full bg-yellow-500/10 text-yellow-500 border border-yellow-500/30 px-3 py-0.5 text-sm">
                            {a} <button onClick={() => setAllergies((p) => p.filter((_, j) => j !== i))}><X className="h-3 w-3" /></button>
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Medical History Conditions */}
                    <div className="space-y-3">
                      <label className="text-sm font-medium">Past Medical History</label>
                      <div className="flex gap-2">
                        <input
                          value={historyInput}
                          onChange={(e) => setHistoryInput(e.target.value)}
                          onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addHistory())}
                          placeholder="e.g. Hypertension, Type 2 Diabetes..."
                          className="flex-1 h-9 rounded-md border border-input bg-transparent px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                        />
                        <Button type="button" variant="outline" size="sm" onClick={addHistory}><Plus className="h-4 w-4" /></Button>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {history.map((h, i) => (
                          <span key={i} className="flex items-center gap-1 rounded-full bg-secondary px-3 py-0.5 text-sm">
                            {h} <button onClick={() => setHistory((p) => p.filter((_, j) => j !== i))}><X className="h-3 w-3" /></button>
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Medications */}
                    <div className="space-y-3">
                      <label className="text-sm font-medium">Current Medications</label>
                      <div className="grid grid-cols-3 gap-2">
                        <input value={medInput.name} onChange={(e) => setMedInput((p) => ({ ...p, name: e.target.value }))} placeholder="Drug name" className="h-9 rounded-md border border-input bg-transparent px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" />
                        <input value={medInput.dose} onChange={(e) => setMedInput((p) => ({ ...p, dose: e.target.value }))} placeholder="Dose (e.g. 10mg)" className="h-9 rounded-md border border-input bg-transparent px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" />
                        <div className="flex gap-2">
                          <input value={medInput.frequency} onChange={(e) => setMedInput((p) => ({ ...p, frequency: e.target.value }))} placeholder="Frequency" className="flex-1 h-9 rounded-md border border-input bg-transparent px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" />
                          <Button type="button" variant="outline" size="sm" onClick={addMed}><Plus className="h-4 w-4" /></Button>
                        </div>
                      </div>
                      <div className="space-y-2">
                        {medications.map((m, i) => (
                          <div key={i} className="flex items-center justify-between rounded-lg bg-secondary/50 px-3 py-2 text-sm">
                            <span className="font-medium">{m.name}</span>
                            <span className="text-muted-foreground">{m.dose} · {m.frequency}</span>
                            <button onClick={() => setMedications((p) => p.filter((_, j) => j !== i))}><X className="h-4 w-4 text-muted-foreground hover:text-foreground" /></button>
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Step 2: Vitals & Symptoms */}
              {step === 2 && (
                <Card>
                  <CardHeader><CardTitle>Vitals & Chief Complaint</CardTitle></CardHeader>
                  <CardContent className="space-y-5">
                    <Textarea
                      label="Chief Complaint"
                      value={chiefComplaint}
                      onChange={(e) => setChiefComplaint(e.target.value)}
                      placeholder="Patient presents with..."
                      rows={3}
                    />
                    <div className="space-y-3">
                      <label className="text-sm font-medium">Vitals <span className="text-muted-foreground font-normal">(optional)</span></label>
                      <div className="grid sm:grid-cols-2 gap-4">
                        <div className="space-y-1.5">
                          <label className="text-xs text-muted-foreground">Blood Pressure (mmHg)</label>
                          <input value={vitals.blood_pressure} onChange={(e) => setVitals((p) => ({ ...p, blood_pressure: e.target.value }))} placeholder="120/80" className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs text-muted-foreground">Heart Rate (bpm)</label>
                          <input type="number" value={vitals.heart_rate} onChange={(e) => setVitals((p) => ({ ...p, heart_rate: e.target.value }))} placeholder="72" className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs text-muted-foreground">Temperature (°F)</label>
                          <input type="number" step="0.1" value={vitals.temperature} onChange={(e) => setVitals((p) => ({ ...p, temperature: e.target.value }))} placeholder="98.6" className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs text-muted-foreground">SpO2 (%)</label>
                          <input type="number" value={vitals.oxygen_saturation} onChange={(e) => setVitals((p) => ({ ...p, oxygen_saturation: e.target.value }))} placeholder="98" className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs text-muted-foreground">Respiratory Rate (/min)</label>
                          <input type="number" value={vitals.respiratory_rate} onChange={(e) => setVitals((p) => ({ ...p, respiratory_rate: e.target.value }))} placeholder="16" className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs text-muted-foreground">Weight (kg)</label>
                          <input type="number" step="0.1" value={vitals.weight_kg} onChange={(e) => setVitals((p) => ({ ...p, weight_kg: e.target.value }))} placeholder="70" className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" />
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Step 3: Review */}
              {step === 3 && (
                <Card>
                  <CardHeader><CardTitle>Review & Confirm</CardTitle></CardHeader>
                  <CardContent className="space-y-4 text-sm">
                    <ReviewSection title="Demographics">
                      <ReviewRow label="Name" value={`${getValues("first_name")} ${getValues("last_name")}`} />
                      <ReviewRow label="MRN" value={getValues("mrn")} />
                      <ReviewRow label="DOB" value={getValues("date_of_birth")} />
                      <ReviewRow label="Gender" value={getValues("gender")} />
                      {getValues("email") && <ReviewRow label="Email" value={getValues("email")!} />}
                      {getValues("phone") && <ReviewRow label="Phone" value={getValues("phone")!} />}
                    </ReviewSection>
                    {allergies.length > 0 && (
                      <ReviewSection title="Allergies">
                        <p>{allergies.join(", ")}</p>
                      </ReviewSection>
                    )}
                    {history.length > 0 && (
                      <ReviewSection title="Medical History">
                        <p>{history.join(", ")}</p>
                      </ReviewSection>
                    )}
                    {medications.length > 0 && (
                      <ReviewSection title="Medications">
                        {medications.map((m, i) => (
                          <ReviewRow key={i} label={m.name} value={`${m.dose} · ${m.frequency}`} />
                        ))}
                      </ReviewSection>
                    )}
                    {chiefComplaint && (
                      <ReviewSection title="Chief Complaint">
                        <p className="text-muted-foreground">{chiefComplaint}</p>
                      </ReviewSection>
                    )}
                  </CardContent>
                </Card>
              )}
            </motion.div>
          </AnimatePresence>

          {/* Navigation */}
          <div className="flex justify-between">
            <Button variant="outline" onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0}>
              <ArrowLeft className="h-4 w-4 mr-1.5" /> Back
            </Button>
            {step < STEPS.length - 1 ? (
              <Button onClick={nextStep}>
                Next <ArrowRight className="h-4 w-4 ml-1.5" />
              </Button>
            ) : (
              <Button onClick={submit} disabled={submitting}>
                {submitting ? <Loader2 className="h-4 w-4 mr-1.5 animate-spin" /> : <Check className="h-4 w-4 mr-1.5" />}
                Create Patient
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function ReviewSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <p className="font-semibold text-xs uppercase tracking-wider text-muted-foreground">{title}</p>
      <div className="rounded-lg bg-secondary/50 p-3 space-y-1">{children}</div>
    </div>
  );
}

function ReviewRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium capitalize">{value}</span>
    </div>
  );
}
