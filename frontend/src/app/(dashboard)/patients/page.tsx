"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Plus, Search } from "lucide-react";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { patientsApi } from "@/lib/api";
import { calculateAge, formatDate, getInitials } from "@/lib/utils";
import { useDebounce } from "@/hooks/useDebounce";

export default function PatientsPage() {
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const debouncedSearch = useDebounce(search, 300);
  const limit = 12;

  const { data, isLoading } = useQuery({
    queryKey: ["patients", { search: debouncedSearch, offset }],
    queryFn: () => patientsApi.list({ limit, offset, q: debouncedSearch || undefined }),
  });

  return (
    <div className="flex flex-col h-full">
      <Header title="Patients" description={`${data?.total ?? "—"} total patients`} />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-6xl space-y-5">
          {/* Toolbar */}
          <div className="flex items-center justify-between gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                placeholder="Search by name or MRN..."
                value={search}
                onChange={(e) => { setSearch(e.target.value); setOffset(0); }}
                className="h-9 w-full rounded-md border border-input bg-transparent pl-9 pr-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring placeholder:text-muted-foreground"
              />
            </div>
            <Link href="/patients/new">
              <Button size="sm" className="gap-1.5">
                <Plus className="h-4 w-4" /> New Patient
              </Button>
            </Link>
          </div>

          {/* Grid */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {isLoading
              ? Array.from({ length: 8 }).map((_, i) => (
                  <Card key={i}>
                    <CardContent className="pt-6 space-y-3">
                      <Skeleton className="h-12 w-12 rounded-full" />
                      <Skeleton className="h-4 w-24" />
                      <Skeleton className="h-3 w-16" />
                    </CardContent>
                  </Card>
                ))
              : data?.items.map((p, i) => (
                  <motion.div
                    key={p.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.04 }}
                  >
                    <Link href={`/patients/${p.id}`}>
                      <Card className="hover:border-primary/50 transition-colors cursor-pointer">
                        <CardContent className="pt-6">
                          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/20 text-primary font-semibold mb-3">
                            {getInitials(`${p.first_name} ${p.last_name}`)}
                          </div>
                          <p className="font-medium text-sm">{p.first_name} {p.last_name}</p>
                          <p className="text-xs text-muted-foreground mt-0.5">{p.mrn}</p>
                          <p className="text-xs text-muted-foreground">{calculateAge(p.date_of_birth)}y · {p.gender}</p>
                          <div className="flex items-center gap-2 mt-3">
                            <Badge variant={p.intake_completed ? "success" : "secondary"} className="text-xs">
                              {p.intake_completed ? "Intake" : "Pending"}
                            </Badge>
                          </div>
                        </CardContent>
                      </Card>
                    </Link>
                  </motion.div>
                ))}
          </div>

          {/* Pagination */}
          {data && data.total > limit && (
            <div className="flex items-center justify-center gap-2 pt-2">
              <Button variant="outline" size="sm" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - limit))}>Previous</Button>
              <span className="text-sm text-muted-foreground">
                {Math.floor(offset / limit) + 1} / {Math.ceil(data.total / limit)}
              </span>
              <Button variant="outline" size="sm" disabled={offset + limit >= data.total} onClick={() => setOffset(offset + limit)}>Next</Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
