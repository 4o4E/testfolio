import { useMemo, useState } from "react"
import {
  ChevronDown,
  CircleAlert,
  CircleCheck,
  CircleDashed,
  CircleMinus,
  CircleOff,
  CircleX,
  Search,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { Empty, EmptyHeader, EmptyTitle } from "@/components/ui/empty"
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field"
import { cn } from "@/lib/utils"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
} from "@/components/ui/input-group"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubItem,
  useSidebar,
} from "@/components/ui/sidebar"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { humanTitle, runStartedAt, statusLabels, statusOf } from "./model"
import type {
  CaseEntry,
  EntryStatus,
  Project,
  StatusFilter,
  TestRun,
} from "./model"

type TreeNode = {
  label: string
  path: string[]
  entries: CaseEntry[]
  directEntries: CaseEntry[]
  children: Map<string, TreeNode>
}

const statusIcons = {
  passed: CircleCheck,
  failed: CircleX,
  blocked: CircleAlert,
  not_run: CircleDashed,
  skipped: CircleMinus,
  not_included: CircleOff,
} satisfies Record<EntryStatus, typeof CircleCheck>

const statusVariants = {
  passed: "secondary",
  failed: "destructive",
  blocked: "outline",
  not_run: "outline",
  skipped: "secondary",
  not_included: "ghost",
} as const

function makeTree(entries: CaseEntry[]) {
  const root: TreeNode = {
    label: "",
    path: [],
    entries: [],
    directEntries: [],
    children: new Map(),
  }

  for (const entry of entries) {
    let node = root
    for (const label of entry.case.path) {
      let child = node.children.get(label)
      if (!child) {
        child = {
          label,
          path: [...node.path, label],
          entries: [],
          directEntries: [],
          children: new Map(),
        }
        node.children.set(label, child)
      }
      child.entries.push(entry)
      node = child
    }
    node.directEntries.push(entry)
  }

  return [...root.children.values()]
}

function TestStatusBadge({ entry }: { entry: CaseEntry }) {
  const status = statusOf(entry)
  const Icon = statusIcons[status]

  return (
    <Badge
      variant={statusVariants[status]}
      aria-label={`状态：${statusLabels[status]}`}
    >
      <Icon aria-hidden="true" />
    </Badge>
  )
}

function CaseLeaf({
  entry,
  selected,
  onCaseChange,
}: {
  entry: CaseEntry
  selected: boolean
  onCaseChange: (id: string) => void
}) {
  const { isMobile, setOpenMobile } = useSidebar()
  const title = humanTitle(entry.case)
  const status = statusLabels[statusOf(entry)]

  return (
    <SidebarMenuSubItem>
      <SidebarMenuButton
        size="sm"
        isActive={selected}
        title={title}
        aria-label={`${title}，状态：${status}`}
        data-testid="case-leaf"
        data-case-id={entry.case.id}
        onClick={() => {
          onCaseChange(entry.case.id)
          if (isMobile) setOpenMobile(false)
        }}
      >
        <span className="min-w-0 flex-1 truncate">{title}</span>
        <TestStatusBadge entry={entry} />
      </SidebarMenuButton>
    </SidebarMenuSubItem>
  )
}

function TreeBranch({
  node,
  selectedCaseId,
  searchActive,
  onCaseChange,
  depth = 0,
}: {
  node: TreeNode
  selectedCaseId: string | null
  searchActive: boolean
  onCaseChange: (id: string) => void
  depth?: number
}) {
  const containsSelected = node.entries.some(
    (entry) => entry.case.id === selectedCaseId
  )
  const [open, setOpen] = useState(containsSelected)

  const children = [...node.children.values()]

  return (
    <Collapsible open={searchActive || open} onOpenChange={setOpen}>
      {depth === 0 ? (
        <SidebarMenuItem>
          <CollapsibleTrigger asChild>
            <SidebarMenuButton data-testid="directory-toggle">
              <span className="flex min-w-0 flex-1 items-center gap-1.5">
                <span className="truncate" data-testid="directory-label">
                  {node.label}
                </span>
                <Badge variant="secondary" data-testid="directory-count">
                  {node.entries.length}
                </Badge>
              </span>
              <ChevronDown
                data-testid="directory-arrow"
                className={cn(
                  "ml-auto shrink-0 transition-transform",
                  (searchActive || open) && "rotate-180"
                )}
                aria-hidden="true"
              />
            </SidebarMenuButton>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <SidebarMenuSub>
              {children.map((child) => (
                <TreeBranch
                  key={`${JSON.stringify(child.path)}${child.entries.some((entry) => entry.case.id === selectedCaseId) ? "-selected" : ""}`}
                  node={child}
                  selectedCaseId={selectedCaseId}
                  searchActive={searchActive}
                  onCaseChange={onCaseChange}
                  depth={depth + 1}
                />
              ))}
              {node.directEntries.map((entry) => (
                <CaseLeaf
                  key={entry.case.id}
                  entry={entry}
                  selected={entry.case.id === selectedCaseId}
                  onCaseChange={onCaseChange}
                />
              ))}
            </SidebarMenuSub>
          </CollapsibleContent>
        </SidebarMenuItem>
      ) : (
        <SidebarMenuSubItem>
          <CollapsibleTrigger asChild>
            <SidebarMenuButton size="sm" data-testid="directory-toggle">
              <span className="flex min-w-0 flex-1 items-center gap-1.5">
                <span className="truncate" data-testid="directory-label">
                  {node.label}
                </span>
                <Badge variant="secondary" data-testid="directory-count">
                  {node.entries.length}
                </Badge>
              </span>
              <ChevronDown
                data-testid="directory-arrow"
                className={cn(
                  "ml-auto shrink-0 transition-transform",
                  (searchActive || open) && "rotate-180"
                )}
                aria-hidden="true"
              />
            </SidebarMenuButton>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <SidebarMenuSub>
              {children.map((child) => (
                <TreeBranch
                  key={`${JSON.stringify(child.path)}${child.entries.some((entry) => entry.case.id === selectedCaseId) ? "-selected" : ""}`}
                  node={child}
                  selectedCaseId={selectedCaseId}
                  searchActive={searchActive}
                  onCaseChange={onCaseChange}
                  depth={depth + 1}
                />
              ))}
              {node.directEntries.map((entry) => (
                <CaseLeaf
                  key={entry.case.id}
                  entry={entry}
                  selected={entry.case.id === selectedCaseId}
                  onCaseChange={onCaseChange}
                />
              ))}
            </SidebarMenuSub>
          </CollapsibleContent>
        </SidebarMenuSubItem>
      )}
    </Collapsible>
  )
}

export function TestSidebar({
  projects,
  projectId,
  entries,
  selectedCaseId,
  runs,
  runId,
  onProjectChange,
  onRunChange,
  onCaseChange,
  search,
  statusFilter,
  scope,
  onSearchChange,
  onStatusFilterChange,
  onScopeChange,
}: {
  projects: Project[]
  projectId: string
  entries: CaseEntry[]
  selectedCaseId: string | null
  runs: TestRun[]
  runId: string | null
  onProjectChange: (id: string) => void
  onRunChange: (id: string) => void
  onCaseChange: (id: string) => void
  search: string
  statusFilter: StatusFilter
  scope: "run" | "all"
  onSearchChange: (value: string) => void
  onStatusFilterChange: (value: StatusFilter) => void
  onScopeChange: (value: "run" | "all") => void
}) {
  const { isMobile } = useSidebar()
  const currentProject = projects.find((project) => project.id === projectId)
  const selectedRun = runs.find((run) => run.id === runId)
  const statuses: StatusFilter[] = [
    "all",
    "passed",
    "failed",
    "blocked",
    "not_run",
    "skipped",
    "not_included",
  ]

  const visibleEntries = useMemo(() => {
    const query = search.trim().toLocaleLowerCase()
    return entries.filter((entry) => {
      if (scope === "run" && !entry.inScope) return false
      if (statusFilter !== "all" && statusOf(entry) !== statusFilter)
        return false
      if (!query) return true
      const text = [humanTitle(entry.case), ...entry.case.path, entry.case.id]
        .join(" ")
        .toLocaleLowerCase()
      return text.includes(query)
    })
  }, [entries, scope, search, statusFilter])

  const tree = useMemo(() => makeTree(visibleEntries), [visibleEntries])

  return (
    <Sidebar collapsible={isMobile ? "offcanvas" : "none"} className="w-full">
      <SidebarHeader className="gap-3 p-3">
        <div className="flex min-w-0 items-center justify-between gap-2">
          <span className="truncate text-sm font-semibold">测试用例</span>
          {projects.length > 1 ? (
            <Select value={projectId} onValueChange={onProjectChange}>
              <SelectTrigger aria-label="选择项目" className="max-w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {projects.map((project) => (
                    <SelectItem key={project.id} value={project.id}>
                      {project.title}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          ) : currentProject ? (
            <span className="truncate text-sm text-muted-foreground">
              {currentProject.title}
            </span>
          ) : null}
        </div>
        <FieldGroup>
          <Field>
            <FieldLabel htmlFor="test-run">测试轮次</FieldLabel>
            <Select
              value={runId ?? undefined}
              onValueChange={onRunChange}
              disabled={runs.length === 0}
            >
              <SelectTrigger
                id="test-run"
                className="w-full [&>[data-slot=select-value]]:min-w-0 [&>[data-slot=select-value]]:flex-1"
              >
                <SelectValue placeholder="尚无测试轮次">
                  {selectedRun && (
                    <span className="flex min-w-0 flex-1 items-center gap-2">
                      <span className="min-w-0 flex-1 truncate">
                        {selectedRun.title}
                      </span>
                      <span className="ml-auto shrink-0 text-xs text-muted-foreground">
                        {runStartedAt(selectedRun.started_at)}
                      </span>
                    </span>
                  )}
                </SelectValue>
              </SelectTrigger>
              <SelectContent
                position="popper"
                align="start"
                className="w-max min-w-(--radix-select-trigger-width) max-w-[calc(100vw-2rem)]"
              >
                <SelectGroup>
                  {runs.map((run) => (
                    <SelectItem
                      key={run.id}
                      value={run.id}
                      textValue={run.title}
                      className="w-full min-w-0 gap-3 [&>span:last-child]:min-w-0 [&>span:last-child]:flex-1"
                    >
                      <span className="min-w-0 flex-1 break-words whitespace-normal">
                        {run.title}
                      </span>
                      <span className="ml-auto shrink-0 text-xs text-muted-foreground">
                        {runStartedAt(run.started_at)}
                      </span>
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          </Field>
        </FieldGroup>
        <InputGroup>
          <InputGroupAddon>
            <Search aria-hidden="true" />
          </InputGroupAddon>
          <InputGroupInput
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="搜索用例或模块"
            aria-label="搜索用例或模块"
          />
        </InputGroup>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <ToggleGroup
            type="single"
            value={scope}
            onValueChange={(value) => {
              if (value === "run" || value === "all") onScopeChange(value)
            }}
            size="sm"
            variant="outline"
            aria-label="用例范围"
          >
            <ToggleGroupItem value="run" aria-label="仅显示本轮用例">
              本轮
            </ToggleGroupItem>
            <ToggleGroupItem value="all" aria-label="显示全部用例">
              全部
            </ToggleGroupItem>
          </ToggleGroup>
          <Select
            value={statusFilter}
            onValueChange={(value) =>
              onStatusFilterChange(value as typeof statusFilter)
            }
          >
            <SelectTrigger aria-label="按结果筛选" className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                {statuses.map((status) => (
                  <SelectItem key={status} value={status}>
                    {status === "all" ? "全部结果" : statusLabels[status]}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>
            用例目录 <span className="ml-auto">{visibleEntries.length}</span>
          </SidebarGroupLabel>
          <SidebarGroupContent>
            {tree.length ? (
              <SidebarMenu>
                {tree.map((node) => (
                  <TreeBranch
                    key={`${JSON.stringify(node.path)}${node.entries.some((entry) => entry.case.id === selectedCaseId) ? "-selected" : ""}`}
                    node={node}
                    selectedCaseId={selectedCaseId}
                    searchActive={search.trim().length > 0}
                    onCaseChange={onCaseChange}
                  />
                ))}
              </SidebarMenu>
            ) : (
              <Empty>
                <EmptyHeader>
                  <EmptyTitle>没有符合条件的用例</EmptyTitle>
                </EmptyHeader>
              </Empty>
            )}
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}
