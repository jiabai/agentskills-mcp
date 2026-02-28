"use client"

import { useState } from "react"
import Link from "next/link"
import { Sparkles } from "lucide-react"

import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export default function RegisterPage() {
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsLoading(true)
    setError(null)
    setSuccess(null)
    try {
      await api.register({ username, email, password })
      setSuccess("注册成功，请登录。")
      setUsername("")
      setEmail("")
      setPassword("")
    } catch (err) {
      setError(err instanceof Error ? err.message : "注册失败")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto grid min-h-screen max-w-screen-xl items-center gap-10 px-6 py-12 lg:grid-cols-[0.9fr_1.1fr]">
        <Card className="border-border/80 shadow-lg">
          <CardHeader>
            <CardTitle>创建账户</CardTitle>
            <CardDescription>开启你的私有 Skill 控制台。</CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username">用户名</Label>
                <Input
                  id="username"
                  placeholder="你的显示名称"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">邮箱</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">密码</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="至少 8 位字符"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                />
              </div>
              {error ? <p className="text-sm text-destructive">{error}</p> : null}
              {success ? <p className="text-sm text-primary">{success}</p> : null}
            </CardContent>
            <CardFooter className="flex flex-col gap-3">
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? "正在创建..." : "创建账户"}
              </Button>
              <Link href="/login" className="text-sm text-primary hover:underline">
                已有账户？前往登录
              </Link>
            </CardFooter>
          </form>
        </Card>
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
              <Sparkles className="h-6 w-6" />
            </div>
            <div>
              <p className="font-display text-2xl">即刻启动</p>
              <p className="text-sm text-muted-foreground">多用户隔离、API Token 与 MCP 工具整合</p>
            </div>
          </div>
          <div className="rounded-lg border border-border bg-muted/60 p-6">
            <ul className="space-y-3 text-sm text-muted-foreground">
              <li>独立 Skill 存储目录与授权</li>
              <li>JWT 登录 + MCP API Token 双认证</li>
              <li>运行历史与可观测性指标</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
