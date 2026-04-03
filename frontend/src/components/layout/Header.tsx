"use client";
import { useEffect, useState } from "react";
import { Bell, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";

interface HeaderProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export function Header({ title, description, action }: HeaderProps) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-border px-6 gap-4">
      <div className="min-w-0">
        <h1 className="text-lg font-semibold truncate">{title}</h1>
        {description && <p className="text-sm text-muted-foreground truncate">{description}</p>}
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {action}
        <Button variant="ghost" size="icon" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
          {mounted && theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>
        <Button variant="ghost" size="icon">
          <Bell className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}
