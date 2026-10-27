export type TestStatus = "passed" | "failed" | "blocked" | "not_run" | "skipped"
export type EntryStatus = TestStatus | "not_included"
export type StatusFilter = "all" | EntryStatus
export type CatalogScope = "run" | "all"

export interface Project {
  id: string
  title: string
  description: string
  case_count: number
}

export interface TestCase {
  id: string
  project_id: string
  title: string
  path: string[]
  requirement: string
  preconditions: string[]
  steps: { action: string; expected: string }[]
  priority: "P0" | "P1" | "P2"
  tags: string[]
  source: string
}

export interface Rectangle {
  x: number
  y: number
  w: number
  h: number
}
export interface Evidence {
  artifact_id: string
  caption: string
  media_type?: string
  crop?: Rectangle | null
  marks?: (Rectangle & { label: string | number })[] | null
}

export interface ResultStep {
  action: string
  expected: string
  actual: string
  status: TestStatus
  evidence: Evidence[]
}

export interface TestResult {
  case_id: string
  status: TestStatus
  actual: string
  steps: ResultStep[]
  evidence: Evidence[]
  issues: { title: string; url: string }[]
  recorded_at: string
  notes: string
}

export type Counts = Record<TestStatus, number> & { total: number }

export interface TestRun {
  id: string
  project_id: string
  title: string
  environment: string
  kind: "browser" | "blackbox" | "whitebox" | "import"
  started_at: string
  versions: Record<string, string>
  scope_case_ids: string[]
  summary: string
  source: string
  state: "running" | "completed" | "interrupted"
  finished_at: string | null
  counts?: Counts
}

export interface RunDetail {
  run: TestRun
  cases: { case: TestCase; result: TestResult | null }[]
  counts: Counts
}

export interface CaseEntry {
  case: TestCase
  result: TestResult | null
  inScope: boolean
}

export interface CaseHistory {
  case: TestCase
  history: { run: TestRun; result: TestResult | null }[]
}

export const statusLabels: Record<EntryStatus, string> = {
  passed: "通过",
  failed: "失败",
  blocked: "受阻",
  not_run: "未测试",
  skipped: "跳过",
  not_included: "本轮未包含",
}

export function statusOf(entry: CaseEntry): EntryStatus {
  return entry.inScope ? (entry.result?.status ?? "not_run") : "not_included"
}

export function humanTitle(value: TestCase): string {
  return value.title.includes("：")
    ? value.title.split("：").slice(1).join("：")
    : value.title
}

export function imageEvidence(result: TestResult | null): Evidence[] {
  if (!result) return []
  return [
    ...result.evidence,
    ...result.steps.flatMap((step) => step.evidence),
  ].filter((item) => (item.media_type ?? "image/png").startsWith("image/"))
}

export function shortDate(value: string): string {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "long",
    day: "numeric",
    timeZone: "Asia/Shanghai",
  }).format(new Date(value))
}

export function runStartedAt(value: string): string {
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).format(new Date(value))
}

export function runCaption(run: TestRun): string {
  const kind = {
    browser: "页面操作",
    blackbox: "黑盒测试",
    whitebox: "白盒审查",
    import: "导入记录",
  }[run.kind]
  return `${kind} · ${shortDate(run.started_at)}`
}

// 所选轮次内使用当时保存的用例定义；其他用例只展示目录定义。
export function mergeEntries(cases: TestCase[], run?: RunDetail): CaseEntry[] {
  const items = new Map(
    cases.map((item) => [
      item.id,
      { case: item, result: null, inScope: false } as CaseEntry,
    ])
  )
  for (const item of run?.cases ?? [])
    items.set(item.case.id, { ...item, inScope: true })
  return [...items.values()]
}
