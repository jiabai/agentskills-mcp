import Link from "next/link"
import { ArrowUpRight, Command, FileText, KeyRound, Sparkles } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl">控制台概览</h1>
          <p className="text-sm text-muted-foreground">集中管理你的多用户 Skill 能力与访问凭证。</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild>
            <Link href="/skills/new">创建 Skill</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/tokens">管理 Token</Link>
          </Button>
        </div>
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        {[
          { title: "活跃 Skills", value: "12", tag: "本月 +4" },
          { title: "可用 Tokens", value: "5", tag: "即将过期 1" },
          { title: "调用成功率", value: "99.2%", tag: "过去 24h" }
        ].map((item) => (
          <Card key={item.title}>
            <CardHeader>
              <CardDescription>{item.title}</CardDescription>
              <CardTitle className="text-3xl">{item.value}</CardTitle>
            </CardHeader>
            <CardContent>
              <Badge variant="accent">{item.tag}</Badge>
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>快捷入口</CardTitle>
            <CardDescription>快速进入常用管理操作。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { label: "Skills 列表", href: "/skills", icon: Sparkles },
              { label: "上传参考文件", href: "/skills/new", icon: FileText },
              { label: "创建 Token", href: "/tokens", icon: KeyRound }
            ].map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.label}
                  href={item.href}
                  className="flex items-center justify-between rounded-lg border border-border bg-muted/40 px-4 py-3 text-sm text-foreground transition hover:bg-muted"
                >
                  <span className="flex items-center gap-2">
                    <Icon className="h-4 w-4 text-muted-foreground" />
                    {item.label}
                  </span>
                  <ArrowUpRight className="h-4 w-4 text-muted-foreground" />
                </Link>
              )
            })}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>运行提示</CardTitle>
            <CardDescription>保持 MCP 服务稳定运行的建议。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm text-muted-foreground">
            <div className="flex items-start gap-3 rounded-lg bg-muted/40 p-4">
              <Command className="mt-0.5 h-4 w-4 text-primary" />
              <div>
                <p className="text-foreground">建议每日检查 /metrics</p>
                <p>关注数据库、磁盘与内存使用率。</p>
              </div>
            </div>
            <div className="flex items-start gap-3 rounded-lg bg-muted/40 p-4">
              <Sparkles className="mt-0.5 h-4 w-4 text-primary" />
              <div>
                <p className="text-foreground">保持 Skill 描述清晰</p>
                <p>可帮助 load_skill_metadata 更好地呈现。</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
