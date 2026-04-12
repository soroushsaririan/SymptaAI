"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  Brain, FlaskConical, FileText, ShieldCheck, Zap, Users,
  ArrowRight, CheckCircle2, ChevronRight, Activity,
} from "lucide-react";

const FEATURES = [
  {
    icon: Brain,
    title: "Multi-Agent AI Pipeline",
    description:
      "Eight specialized agents run in sequence — from patient intake through differential diagnosis to a complete care plan — each passing enriched context to the next.",
    color: "text-violet-400",
    bg: "bg-violet-400/10",
  },
  {
    icon: FlaskConical,
    title: "Lab Result Interpretation",
    description:
      "Flags critical and abnormal values, interprets trends, and contextualizes results within the patient's full medical history and medications.",
    color: "text-cyan-400",
    bg: "bg-cyan-400/10",
  },
  {
    icon: ShieldCheck,
    title: "Drug Interaction Checking",
    description:
      "Cross-references current medications against proposed treatments. Flags contraindications, major interactions, and dosing concerns automatically.",
    color: "text-emerald-400",
    bg: "bg-emerald-400/10",
  },
  {
    icon: FileText,
    title: "Structured Clinical Reports",
    description:
      "Generates reports with executive summaries, differential diagnoses ranked by probability with ICD-10 codes, and prioritized care plan actions.",
    color: "text-amber-400",
    bg: "bg-amber-400/10",
  },
  {
    icon: Users,
    title: "Full Patient Records",
    description:
      "Manage demographics, vitals, allergies, medications, medical history, and uploaded clinical documents in one place.",
    color: "text-rose-400",
    bg: "bg-rose-400/10",
  },
  {
    icon: Zap,
    title: "Real-Time Streaming",
    description:
      "Watch each agent's reasoning stream live via SSE — full transparency at every step, no waiting for a black-box result.",
    color: "text-blue-400",
    bg: "bg-blue-400/10",
  },
];

const AGENTS = [
  { name: "Patient Intake", desc: "Validates & structures patient data" },
  { name: "Record Summarizer", desc: "Extracts key findings from documents" },
  { name: "Symptom Analysis", desc: "Maps symptoms to clinical patterns" },
  { name: "Lab Interpretation", desc: "Contextualises values against norms" },
  { name: "Drug Interaction", desc: "Checks medication conflicts" },
  { name: "Differential Dx", desc: "Ranks diagnoses with ICD-10 codes" },
  { name: "Care Plan", desc: "Generates prioritised action items" },
  { name: "Clinical Report", desc: "Compiles full structured report" },
];

const STATS = [
  { value: "8", label: "Specialized AI agents" },
  { value: "<2min", label: "Full analysis time" },
  { value: "ICD-10", label: "Coded diagnoses" },
  { value: "SSE", label: "Real-time streaming" },
];

function AnimatedCounter({ value }: { value: string }) {
  return <span>{value}</span>;
}

export default function LandingPage() {
  const [activeAgent, setActiveAgent] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveAgent((prev) => (prev + 1) % AGENTS.length);
    }, 1200);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white overflow-x-hidden">
      {/* Background grid */}
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#ffffff08_1px,transparent_1px),linear-gradient(to_bottom,#ffffff08_1px,transparent_1px)] bg-[size:64px_64px] pointer-events-none" />
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,#6d28d920,transparent)] pointer-events-none" />

      {/* Nav */}
      <nav className="relative z-20 border-b border-white/5 bg-[#0a0a0f]/80 backdrop-blur-xl sticky top-0">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-600">
              <Brain className="h-4 w-4 text-white" />
            </div>
            <span className="font-semibold text-base tracking-tight">SymptaAI</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm text-white/50">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#workflow" className="hover:text-white transition-colors">Workflow</a>
            <a href="#tech" className="hover:text-white transition-colors">Technology</a>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login" className="text-sm text-white/50 hover:text-white transition-colors px-4 py-2">
              Sign in
            </Link>
            <Link
              href="/login"
              className="inline-flex items-center gap-1.5 h-9 rounded-lg bg-violet-600 hover:bg-violet-500 transition-colors px-4 text-sm font-medium"
            >
              Get started <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 pt-28 pb-24 text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-violet-500/30 bg-violet-500/10 px-4 py-1.5 text-xs text-violet-300 mb-8">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-violet-500" />
          </span>
          Clinical AI · Multi-Agent · Real-Time
        </div>

        <h1 className="text-6xl md:text-7xl font-bold tracking-tight leading-[1.08] mb-6">
          AI clinical decision
          <br />
          <span className="bg-gradient-to-r from-violet-400 via-fuchsia-400 to-cyan-400 bg-clip-text text-transparent">
            support that thinks
          </span>
        </h1>

        <p className="text-lg text-white/50 max-w-2xl mx-auto mb-10 leading-relaxed">
          SymptaAI runs a pipeline of eight specialized AI agents across your patient's
          full clinical picture — labs, records, symptoms, and medications — delivering a
          differential diagnosis and care plan in under two minutes.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4 mb-16">
          <Link
            href="/login"
            className="inline-flex items-center gap-2 h-12 rounded-xl bg-violet-600 hover:bg-violet-500 transition-all px-8 text-sm font-semibold shadow-lg shadow-violet-500/25"
          >
            Open dashboard <ArrowRight className="h-4 w-4" />
          </Link>
          <a
            href="#workflow"
            className="inline-flex items-center gap-2 h-12 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 transition-all px-8 text-sm font-medium"
          >
            See how it works
          </a>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto">
          {STATS.map((stat) => (
            <div key={stat.label} className="rounded-xl border border-white/8 bg-white/3 px-4 py-4">
              <div className="text-2xl font-bold text-white mb-0.5">
                <AnimatedCounter value={stat.value} />
              </div>
              <div className="text-xs text-white/40">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Live agent preview */}
      <section id="workflow" className="relative z-10 border-t border-white/5 bg-white/[0.02]">
        <div className="max-w-7xl mx-auto px-6 py-24">
          <div className="grid md:grid-cols-2 gap-16 items-center">
            <div>
              <div className="text-xs font-mono text-violet-400 uppercase tracking-widest mb-4">Workflow</div>
              <h2 className="text-4xl font-bold leading-tight mb-5">
                8 agents.<br />One complete analysis.
              </h2>
              <p className="text-white/50 leading-relaxed mb-8">
                Each agent is a specialist. They run in sequence, passing enriched context
                forward — building a complete clinical picture no single model could produce alone.
              </p>
              <div className="space-y-1.5">
                {["Structured patient intake with validation", "Parallel record summarization & symptom mapping", "Lab value interpretation with clinical context", "Drug interaction & contraindication checking", "Differential diagnosis with probability rankings", "Prioritized care plan with timeframes"].map((item) => (
                  <div key={item} className="flex items-start gap-2.5 text-sm text-white/60">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                    {item}
                  </div>
                ))}
              </div>
            </div>

            {/* Animated agent pipeline */}
            <div className="rounded-2xl border border-white/8 bg-[#0d0d14] p-6 space-y-2">
              <div className="text-xs text-white/30 font-mono mb-4 flex items-center gap-2">
                <Activity className="h-3.5 w-3.5 text-emerald-400" />
                Live agent pipeline
              </div>
              {AGENTS.map((agent, i) => (
                <div
                  key={agent.name}
                  className={`flex items-center gap-3 rounded-lg px-4 py-2.5 transition-all duration-300 ${
                    i === activeAgent
                      ? "bg-violet-500/15 border border-violet-500/30"
                      : i < activeAgent
                      ? "opacity-40"
                      : "opacity-20"
                  }`}
                >
                  <div className={`h-6 w-6 rounded-md flex items-center justify-center text-xs font-mono shrink-0 ${
                    i === activeAgent ? "bg-violet-500 text-white" : "bg-white/5 text-white/30"
                  }`}>
                    {i < activeAgent ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> : i + 1}
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-white/90 truncate">{agent.name}</div>
                    <div className="text-xs text-white/35 truncate">{agent.desc}</div>
                  </div>
                  {i === activeAgent && (
                    <div className="ml-auto flex gap-0.5 shrink-0">
                      {[0, 1, 2].map((d) => (
                        <div
                          key={d}
                          className="h-1 w-1 rounded-full bg-violet-400 animate-bounce"
                          style={{ animationDelay: `${d * 150}ms` }}
                        />
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="relative z-10 max-w-7xl mx-auto px-6 py-24">
        <div className="text-center mb-16">
          <div className="text-xs font-mono text-violet-400 uppercase tracking-widest mb-4">Features</div>
          <h2 className="text-4xl font-bold mb-4">Built for real clinical workflows</h2>
          <p className="text-white/50 max-w-xl mx-auto">
            Every feature was designed around actual physician needs — not a generic AI wrapper.
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-5">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="group rounded-2xl border border-white/8 bg-white/[0.02] hover:bg-white/[0.04] hover:border-white/15 transition-all p-6"
            >
              <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${f.bg} mb-5`}>
                <f.icon className={`h-5 w-5 ${f.color}`} />
              </div>
              <h3 className="font-semibold text-base mb-2">{f.title}</h3>
              <p className="text-sm text-white/45 leading-relaxed">{f.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Tech stack */}
      <section id="tech" className="relative z-10 border-t border-white/5 bg-white/[0.02]">
        <div className="max-w-7xl mx-auto px-6 py-20 text-center">
          <div className="text-xs font-mono text-white/30 uppercase tracking-widest mb-8">Technology stack</div>
          <div className="flex flex-wrap justify-center gap-3">
            {[
              "NVIDIA NIM", "LangGraph", "FastAPI", "Next.js 14",
              "SQLAlchemy", "Server-Sent Events", "JWT Auth", "ChromaDB RAG",
            ].map((tech) => (
              <span
                key={tech}
                className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs text-white/50"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 py-24">
        <div className="rounded-3xl border border-violet-500/20 bg-gradient-to-br from-violet-500/10 via-fuchsia-500/5 to-transparent p-12 text-center relative overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,#7c3aed15,transparent_70%)]" />
          <div className="relative z-10">
            <h2 className="text-4xl font-bold mb-4">Start an analysis now</h2>
            <p className="text-white/50 mb-8 max-w-md mx-auto">
              Sign in with your clinical staff credentials and run a full AI analysis on any patient.
            </p>
            <Link
              href="/login"
              className="inline-flex items-center gap-2 h-12 rounded-xl bg-violet-600 hover:bg-violet-500 transition-all px-10 text-sm font-semibold shadow-2xl shadow-violet-500/30"
            >
              Sign in to dashboard <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-8 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-white/25">
          <div className="flex items-center gap-2">
            <Brain className="h-3.5 w-3.5" />
            <span>SymptaAI — Clinical AI Decision Support</span>
          </div>
          <p>For research and clinical decision support only. Not a substitute for professional medical judgment.</p>
        </div>
      </footer>
    </div>
  );
}
