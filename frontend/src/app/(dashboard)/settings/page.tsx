"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { User, KeyRound, Bell, Shield, Save, Eye, EyeOff } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { authApi } from "@/lib/api";
import { toast } from "react-hot-toast";

export default function SettingsPage() {
  const queryClient = useQueryClient();

  const { data: me } = useQuery({
    queryKey: ["me"],
    queryFn: () => authApi.me(),
  });

  // Profile form
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");

  // Password form
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);

  // Sync form with loaded user data
  useState(() => {
    if (me) { setFullName(me.full_name); setEmail(me.email); }
  });

  const updateProfile = useMutation({
    mutationFn: () => authApi.updateMe({ full_name: fullName, email }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["me"] });
      toast.success("Profile updated");
    },
    onError: () => toast.error("Failed to update profile"),
  });

  const changePassword = useMutation({
    mutationFn: () => authApi.changePassword(currentPassword, newPassword),
    onSuccess: () => {
      setCurrentPassword(""); setNewPassword("");
      toast.success("Password changed");
    },
    onError: () => toast.error("Current password is incorrect"),
  });

  const ROLE_COLORS: Record<string, string> = {
    physician: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    nurse: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    admin: "bg-violet-500/10 text-violet-400 border-violet-500/20",
    viewer: "bg-muted text-muted-foreground",
  };

  return (
    <div className="flex flex-col h-full">
      <Header title="Settings" description="Manage your account" />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-2xl space-y-6">

          {/* Profile */}
          <Card>
            <CardHeader className="pb-4">
              <div className="flex items-center gap-2">
                <User className="h-4 w-4 text-muted-foreground" />
                <CardTitle className="text-base">Profile</CardTitle>
              </div>
              <CardDescription>Update your display name and email address.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3 pb-2">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/20 text-primary font-semibold text-lg">
                  {me?.full_name?.charAt(0).toUpperCase() ?? "?"}
                </div>
                <div>
                  <p className="font-medium">{me?.full_name}</p>
                  <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${ROLE_COLORS[me?.role ?? "viewer"]}`}>
                    {me?.role}
                  </span>
                </div>
              </div>
              <Separator />
              <div className="space-y-3">
                <div>
                  <label className="text-sm font-medium mb-1.5 block">Full Name</label>
                  <input
                    value={fullName || me?.full_name || ""}
                    onChange={(e) => setFullName(e.target.value)}
                    className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-1.5 block">Email</label>
                  <input
                    value={email || me?.email || ""}
                    onChange={(e) => setEmail(e.target.value)}
                    type="email"
                    className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  />
                </div>
              </div>
              <div className="flex justify-end pt-1">
                <Button
                  size="sm"
                  className="gap-1.5"
                  disabled={updateProfile.isPending}
                  onClick={() => updateProfile.mutate()}
                >
                  <Save className="h-3.5 w-3.5" />
                  {updateProfile.isPending ? "Saving..." : "Save changes"}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Password */}
          <Card>
            <CardHeader className="pb-4">
              <div className="flex items-center gap-2">
                <KeyRound className="h-4 w-4 text-muted-foreground" />
                <CardTitle className="text-base">Password</CardTitle>
              </div>
              <CardDescription>Change your login password.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <label className="text-sm font-medium mb-1.5 block">Current Password</label>
                <div className="relative">
                  <input
                    type={showCurrent ? "text" : "password"}
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    className="h-9 w-full rounded-md border border-input bg-transparent px-3 pr-9 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  />
                  <button
                    type="button"
                    onClick={() => setShowCurrent((v) => !v)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    {showCurrent ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-1.5 block">New Password</label>
                <div className="relative">
                  <input
                    type={showNew ? "text" : "password"}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="h-9 w-full rounded-md border border-input bg-transparent px-3 pr-9 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  />
                  <button
                    type="button"
                    onClick={() => setShowNew((v) => !v)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    {showNew ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                <p className="text-xs text-muted-foreground mt-1.5">Min 8 characters, one uppercase letter and one number.</p>
              </div>
              <div className="flex justify-end pt-1">
                <Button
                  size="sm"
                  className="gap-1.5"
                  disabled={changePassword.isPending || !currentPassword || !newPassword}
                  onClick={() => changePassword.mutate()}
                >
                  <KeyRound className="h-3.5 w-3.5" />
                  {changePassword.isPending ? "Changing..." : "Change password"}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Account info */}
          <Card>
            <CardHeader className="pb-4">
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-muted-foreground" />
                <CardTitle className="text-base">Account</CardTitle>
              </div>
              <CardDescription>Your account details and access level.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex items-center justify-between py-1.5 border-b border-border/50">
                <span className="text-muted-foreground">Account ID</span>
                <span className="font-mono text-xs">{me?.id?.slice(0, 8)}...</span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-border/50">
                <span className="text-muted-foreground">Role</span>
                <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${ROLE_COLORS[me?.role ?? "viewer"]}`}>
                  {me?.role}
                </span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-border/50">
                <span className="text-muted-foreground">Email verified</span>
                <Badge variant={me?.is_verified ? "success" : "secondary"}>
                  {me?.is_verified ? "Verified" : "Unverified"}
                </Badge>
              </div>
              <div className="flex items-center justify-between py-1.5">
                <span className="text-muted-foreground">Account status</span>
                <Badge variant={me?.is_active ? "success" : "destructive"}>
                  {me?.is_active ? "Active" : "Inactive"}
                </Badge>
              </div>
            </CardContent>
          </Card>

        </div>
      </div>
    </div>
  );
}
