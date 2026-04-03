"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { FileText, Search } from "lucide-react";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { reportsApi } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";
import { useDebounce } from "@/hooks/useDebounce";

export default function ReportsPage() {
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const debouncedSearch = useDebounce(search, 300);
  const limit = 15;

  const { data, isLoading } = useQuery({
    queryKey: ["reports", { search: debouncedSearch, offset }],
    queryFn: () => reportsApi.list({ limit, offset }),
  });

  return (
    <div className="flex flex-col h-full">
      <Header title="Clinical Reports" description={`${data?.total ?? "—"} total reports`} />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-4xl space-y-5">
          {/* Search bar */}
          <div className="relative max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              placeholder="Search reports..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setOffset(0); }}
              className="h-9 w-full rounded-md border border-input bg-transparent pl-9 pr-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring placeholder:text-muted-foreground"
            />
          </div>

          {/* Reports list */}
          <div className="space-y-3">
            {isLoading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <Card key={i}>
                  <CardContent className="pt-4 pb-4 space-y-2">
                    <Skeleton className="h-4 w-64" />
                    <Skeleton className="h-3 w-40" />
                  </CardContent>
                </Card>
              ))
            ) : data?.items.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-24 gap-3 text-muted-foreground">
                <FileText className="h-12 w-12 opacity-20" />
                <p className="text-sm">No reports generated yet</p>
                <p className="text-xs">Run an AI analysis on a patient to generate a clinical report</p>
              </div>
            ) : (
              data?.items.map((r, i) => (
                <motion.div
                  key={r.id}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04 }}
                >
                  <Link href={`/reports/${r.id}`}>
                    <Card className="hover:border-primary/50 transition-colors cursor-pointer">
                      <CardContent className="pt-4 pb-4">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex items-start gap-3 min-w-0">
                            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 shrink-0">
                              <FileText className="h-4 w-4 text-primary" />
                            </div>
                            <div className="min-w-0">
                              <p className="font-medium text-sm truncate">{r.title}</p>
                              <p className="text-xs text-muted-foreground mt-0.5">{formatRelativeTime(r.created_at)}</p>
                            </div>
                          </div>
                          <Badge
                            variant={r.status === "completed" ? "success" : r.status === "failed" ? "destructive" : "secondary"}
                            className="shrink-0"
                          >
                            {r.status}
                          </Badge>
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                </motion.div>
              ))
            )}
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
