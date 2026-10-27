import { Moon, RefreshCw, Sun } from "lucide-react"
import { useTheme } from "next-themes"

import { Button } from "@/components/ui/button"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Link } from "react-router"

export function ReaderHeader({
  onRefresh,
  refreshing,
}: {
  onRefresh: () => void
  refreshing: boolean
}) {
  const { resolvedTheme, setTheme } = useTheme()
  const dark = resolvedTheme === "dark"
  const themeLabel = dark ? "切换到浅色模式" : "切换到深色模式"

  return (
    <header className="flex min-h-12 shrink-0 items-center gap-3 border-b px-3 md:px-5">
      <SidebarTrigger aria-label="显示或隐藏用例目录" />
      <Button asChild variant="ghost" size="sm">
        <Link to="/projects">项目列表</Link>
      </Button>
      <div className="flex-1" />
      <Button
        variant="outline"
        size="icon-sm"
        aria-label={themeLabel}
        title={themeLabel}
        onClick={() => setTheme(dark ? "light" : "dark")}
      >
        {dark ? <Sun /> : <Moon />}
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={onRefresh}
        disabled={refreshing}
        aria-label={refreshing ? "正在刷新" : "刷新测试数据"}
      >
        <RefreshCw data-icon="inline-start" aria-hidden="true" />
        <span className="hidden sm:inline">
          {refreshing ? "刷新中" : "刷新"}
        </span>
      </Button>
    </header>
  )
}
