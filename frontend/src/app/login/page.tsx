"use client"

import { useState } from "react"
import Link from "next/link"
import { Mail, Shield } from "lucide-react"

import { api, storeTokens } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export default function LoginPage() {
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
      const tokenPair = await api.login({ email, password })
      storeTokens(tokenPair)
      setSuccess("登录成功，已保存凭证。")
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto grid min-h-screen max-w-screen-xl items-center gap-10 px-6 py-12 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Shield className="h-6 w-6" />
            </div>
            <div>
              <p className="font-display text-2xl">欢迎回来</p>
              <p className="text-sm text-muted-foreground">安全地进入你的 Skill 空间</p>
            </div>
          </div>
          <div className="rounded-lg border border-border bg-muted/60 p-6">
            <p className="text-sm text-muted-foreground">
              你将访问私有 MCP Skill 目录、API Token 管理与运行记录。所有动作都记录在账户下。
            </p>
          </div>
        </div>
        <Card className="border-border/80 shadow-lg">
          <CardHeader>
            <CardTitle>欢迎回来</CardTitle>
            <CardDescription>请输入邮箱与密码继续。</CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
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
                  placeholder="••••••••"
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
                {isLoading ? "正在登录..." : "登录"}
              </Button>
              <div className="flex w-full items-center justify-between text-sm text-muted-foreground">
                <span className="flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  仅用于认证
                </span>
                <Link href="/register" className="text-primary hover:underline">
                  创建账户
                </Link>
              </div>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  )
}
