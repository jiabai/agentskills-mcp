"use client"

import { useEffect, useState } from "react"
import { Loader2, User2 } from "lucide-react"

import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export default function ProfilePage() {
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")
  const [status, setStatus] = useState<"loading" | "ready">("loading")
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    const loadProfile = async () => {
      const user = await api.getMe()
      setUsername(user.username)
      setEmail(user.email)
      setStatus("ready")
    }
    loadProfile()
  }, [])

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setMessage(null)
    await api.updateMe({ username, email })
    setMessage("个人信息已更新。")
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
          <User2 className="h-5 w-5" />
        </div>
        <div>
          <h1 className="font-display text-3xl">个人信息</h1>
          <p className="text-sm text-muted-foreground">更新账户基础资料。</p>
        </div>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>资料信息</CardTitle>
          <CardDescription>所有变更立即生效。</CardDescription>
        </CardHeader>
        <CardContent>
          {status === "loading" ? (
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              加载中
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username">显示名称</Label>
                <Input id="username" value={username} onChange={(event) => setUsername(event.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">邮箱</Label>
                <Input id="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
              </div>
              <Button type="submit">保存变更</Button>
              {message ? <p className="text-sm text-primary">{message}</p> : null}
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
