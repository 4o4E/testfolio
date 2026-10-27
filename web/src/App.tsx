import { useEffect, useRef } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import {
  AlertCircleIcon,
  ClipboardCheckIcon,
  FolderKanbanIcon,
} from "lucide-react"
import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams,
} from "react-router"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar"
import { Skeleton } from "@/components/ui/skeleton"
import { CaseReader } from "@/features/results/case-reader"
import { ReaderHeader } from "@/features/results/reader-header"
import { ReaderLayout } from "@/features/results/reader-layout"
import { TestSidebar } from "@/features/results/test-sidebar"
import {
  imageEvidence,
  mergeEntries,
  type CaseHistory,
  type Project,
  type RunDetail,
  type TestCase,
  type TestRun,
} from "@/features/results/model"
import { useReaderStore } from "@/features/results/store"

async function read<T>(path: string, signal: AbortSignal): Promise<T> {
  const response = await fetch(path, {
    signal,
    headers: { Accept: "application/json" },
  })
  if (!response.ok)
    throw new Error(`读取测试记录失败（HTTP ${response.status}）`)
  return response.json() as Promise<T>
}

const encoded = encodeURIComponent

function routeFor(
  projectId: string,
  runId?: string | null,
  caseId?: string | null
) {
  const base = `/projects/${encoded(projectId)}`
  if (!runId) return base
  const runPath = `${base}/runs/${encoded(runId)}`
  return caseId ? `${runPath}/cases/${encoded(caseId)}` : runPath
}

function ProjectHome() {
  const setSearch = useReaderStore((state) => state.setSearch)
  const setStatusFilter = useReaderStore((state) => state.setStatusFilter)
  const setScope = useReaderStore((state) => state.setScope)
  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: ({ signal }) => read<Project[]>("/api/projects", signal),
  })
  const projects = projectsQuery.data ?? []

  return (
    <main className="mx-auto flex min-h-svh w-full max-w-5xl flex-col gap-8 px-5 py-10 sm:px-10 sm:py-16">
      <header className="flex items-center gap-3">
        <div className="flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
          <ClipboardCheckIcon aria-hidden="true" className="size-5" />
        </div>
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Testfolio</h1>
          <p className="text-sm text-muted-foreground">选择项目查看测试记录</p>
        </div>
      </header>
      {projectsQuery.error ? (
        <Alert variant="destructive">
          <AlertCircleIcon />
          <AlertTitle>暂时无法读取项目</AlertTitle>
          <AlertDescription>{projectsQuery.error.message}</AlertDescription>
          <Button
            variant="outline"
            className="mt-3 w-fit"
            onClick={() => void projectsQuery.refetch()}
          >
            重新读取
          </Button>
        </Alert>
      ) : projectsQuery.isPending ? (
        <div className="flex flex-col gap-4" aria-label="正在读取项目">
          <Skeleton className="h-8 w-2/5" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      ) : projects.length ? (
        <section aria-label="项目列表" className="grid gap-3 sm:grid-cols-2">
          {projects.map((project) => (
            <Button
              key={project.id}
              asChild
              variant="outline"
              className="h-auto min-h-24 justify-start gap-4 p-5 text-left whitespace-normal"
            >
              <Link
                to={routeFor(project.id)}
                onClick={() => {
                  setSearch("")
                  setStatusFilter("all")
                  setScope("run")
                }}
              >
                <FolderKanbanIcon
                  aria-hidden="true"
                  className="size-5 shrink-0 text-muted-foreground"
                />
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-medium">
                    {project.title}
                  </span>
                  <span className="mt-1 block text-sm font-normal text-muted-foreground">
                    {project.case_count} 个用例
                  </span>
                </span>
              </Link>
            </Button>
          ))}
        </section>
      ) : (
        <Empty className="min-h-72 border">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <FolderKanbanIcon />
            </EmptyMedia>
            <EmptyTitle>还没有项目</EmptyTitle>
            <EmptyDescription>
              录入项目和测试用例后，可以在这里查看项目记录。
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      )}
    </main>
  )
}

function LegacyQueryRedirect() {
  const location = useLocation()
  const params = new URLSearchParams(location.search)
  const projectId = params.get("project")
  if (!projectId) return <ProjectHome />
  return (
    <Navigate
      replace
      to={routeFor(projectId, params.get("run"), params.get("case"))}
    />
  )
}

function NotFound() {
  return (
    <main className="flex min-h-svh items-center justify-center p-6">
      <Empty className="max-w-md border">
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <AlertCircleIcon />
          </EmptyMedia>
          <EmptyTitle>找不到这个页面</EmptyTitle>
          <EmptyDescription>此地址不属于测试结果页面。</EmptyDescription>
        </EmptyHeader>
        <EmptyContent>
          <Button asChild>
            <Link to="/projects">返回项目列表</Link>
          </Button>
        </EmptyContent>
      </Empty>
    </main>
  )
}

function ReaderRoute() {
  const { projectId, runId: routeRunId, caseId: routeCaseId } = useParams()
  return (
    <Reader
      projectId={projectId!}
      routeRunId={routeRunId ?? null}
      routeCaseId={routeCaseId ?? null}
    />
  )
}

function Reader({
  projectId,
  routeRunId,
  routeCaseId,
}: {
  projectId: string
  routeRunId: string | null
  routeCaseId: string | null
}) {
  const navigate = useNavigate()
  const search = useReaderStore((state) => state.search)
  const statusFilter = useReaderStore((state) => state.statusFilter)
  const scope = useReaderStore((state) => state.scope)
  const setSearch = useReaderStore((state) => state.setSearch)
  const setStatusFilter = useReaderStore((state) => state.setStatusFilter)
  const setScope = useReaderStore((state) => state.setScope)
  const queryClient = useQueryClient()
  const readingPane = useRef<HTMLDivElement>(null)
  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: ({ signal }) => read<Project[]>("/api/projects", signal),
  })
  const projects = projectsQuery.data ?? []
  const project = projects.find((item) => item.id === projectId)
  const casesQuery = useQuery({
    queryKey: ["cases", projectId],
    queryFn: ({ signal }) =>
      read<TestCase[]>(`/api/projects/${encoded(projectId)}/cases`, signal),
    enabled: !!project,
  })
  const runsQuery = useQuery({
    queryKey: ["runs", projectId],
    queryFn: ({ signal }) =>
      read<TestRun[]>(`/api/projects/${encoded(projectId)}/runs`, signal),
    enabled: !!project,
  })
  const runs = (runsQuery.data ?? []).filter(
    (item) => item.project_id === projectId
  )
  const projectCases = (casesQuery.data ?? []).filter(
    (item) => item.project_id === projectId
  )
  const defaultRun =
    runs.find(
      (item) => item.kind === "browser" && item.state === "completed"
    ) ??
    runs.find((item) => item.kind === "browser") ??
    runs[0] ??
    null
  const selectedRun = routeRunId
    ? runs.find((item) => item.id === routeRunId)
    : defaultRun
  const detailQuery = useQuery({
    queryKey: ["run", selectedRun?.id],
    queryFn: ({ signal }) =>
      read<RunDetail>(`/api/runs/${encoded(selectedRun!.id)}`, signal),
    enabled: !!selectedRun,
  })
  const detail = detailQuery.data
  const detailMatchesSelection =
    !!detail &&
    detail.run.id === selectedRun?.id &&
    detail.run.project_id === projectId &&
    detail.cases.every((item) => item.case.project_id === projectId)
  const entries = mergeEntries(
    projectCases,
    detailMatchesSelection ? detail : undefined
  )
  const initialEntry =
    entries.find((item) => item.inScope && imageEvidence(item.result).length) ??
    entries.find((item) => item.inScope) ??
    entries[0]
  const selectedCaseId =
    routeCaseId ?? (selectedRun ? (initialEntry?.case.id ?? null) : null)
  const selectedEntry = entries.find((item) => item.case.id === selectedCaseId)
  const historyEnabled =
    !!project &&
    !!selectedCaseId &&
    projectCases.some((item) => item.id === selectedCaseId)
  const historyQuery = useQuery({
    queryKey: ["history", projectId, selectedCaseId],
    queryFn: ({ signal }) =>
      read<CaseHistory>(
        `/api/projects/${encoded(projectId)}/cases/${encoded(selectedCaseId!)}`,
        signal
      ),
    enabled: historyEnabled,
  })
  const historyMatchesSelection =
    !!historyQuery.data &&
    historyQuery.data.case.id === selectedCaseId &&
    historyQuery.data.case.project_id === projectId &&
    historyQuery.data.history.every((item) => item.run.project_id === projectId)
  const pending =
    projectsQuery.isPending ||
    (!!project && (casesQuery.isPending || runsQuery.isPending)) ||
    (!!selectedRun && detailQuery.isPending)
  const requestError =
    projectsQuery.error ??
    casesQuery.error ??
    runsQuery.error ??
    detailQuery.error
  const selectionError =
    !projectsQuery.isPending && !project
      ? "找不到这个项目，请返回项目列表重新选择。"
      : runsQuery.data && routeRunId && !selectedRun
        ? "找不到这个测试轮次，请从上方重新选择。"
        : detail && !detailMatchesSelection
          ? "这个测试轮次不属于当前项目，无法显示其记录。"
          : casesQuery.data && routeCaseId && !selectedEntry
            ? "找不到这个测试用例，请从目录重新选择。"
            : null
  const error = requestError?.message ?? selectionError
  const refreshing =
    projectsQuery.isFetching ||
    casesQuery.isFetching ||
    runsQuery.isFetching ||
    detailQuery.isFetching

  // Direct project and run paths acquire a default run and image case without
  // adding artificial entries to browser history.
  useEffect(() => {
    if (pending || error || !project) return
    if (!routeRunId && selectedRun) {
      navigate(routeFor(project.id, selectedRun.id), { replace: true })
      return
    }
    if (!routeRunId || !selectedRun || !detailMatchesSelection || routeCaseId)
      return
    if (initialEntry)
      navigate(routeFor(project.id, selectedRun.id, initialEntry.case.id), {
        replace: true,
      })
  }, [
    pending,
    error,
    project,
    routeRunId,
    routeCaseId,
    selectedRun,
    detailMatchesSelection,
    initialEntry,
    navigate,
  ])

  useEffect(() => {
    if (readingPane.current) readingPane.current.scrollTop = 0
  }, [routeRunId, routeCaseId])

  const run = detailMatchesSelection
    ? { ...detail.run, counts: detail.counts }
    : (selectedRun ?? null)
  const refresh = () => {
    void queryClient.invalidateQueries()
  }
  const clearReaderFilters = () => {
    setSearch("")
    setStatusFilter("all")
    setScope("run")
  }
  const selectProject = (id: string) => {
    clearReaderFilters()
    navigate(routeFor(id))
  }
  const selectRun = (id: string) => {
    clearReaderFilters()
    navigate(routeFor(projectId, id))
  }
  const selectCase = (id: string) => {
    if (selectedRun) navigate(routeFor(projectId, selectedRun.id, id))
  }
  const selectHistoryRun = (id: string) => {
    clearReaderFilters()
    navigate(routeFor(projectId, id, selectedEntry?.case.id))
  }

  return (
    <SidebarProvider className="h-svh min-h-0">
      <ReaderLayout
        sidebar={
          project && (
            <TestSidebar
              projects={projects}
              projectId={project.id}
              entries={entries}
              selectedCaseId={selectedCaseId}
              runs={runs}
              runId={selectedRun?.id ?? null}
              onProjectChange={selectProject}
              onRunChange={selectRun}
              onCaseChange={selectCase}
              search={search}
              statusFilter={statusFilter}
              scope={scope}
              onSearchChange={setSearch}
              onStatusFilterChange={setStatusFilter}
              onScopeChange={setScope}
            />
          )
        }
      >
        <SidebarInset className="h-full min-w-0 overflow-hidden">
          <ReaderHeader onRefresh={refresh} refreshing={refreshing} />
          <div
            ref={readingPane}
            data-testid="reading-pane"
            className="min-h-0 flex-1 overflow-y-auto"
          >
            <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-5 py-6 sm:px-10 sm:py-9">
              {error ? (
                <Alert variant="destructive">
                  <AlertCircleIcon />
                  <AlertTitle>暂时无法显示测试结果</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              ) : pending ? (
                <div
                  className="flex flex-col gap-6"
                  aria-label="正在读取测试结果"
                >
                  <Skeleton className="h-8 w-3/5" />
                  <Skeleton className="h-4 w-2/5" />
                  <Skeleton className="aspect-video w-full" />
                </div>
              ) : selectedEntry ? (
                <CaseReader
                  key={`${selectedRun?.id}:${selectedCaseId}`}
                  entry={selectedEntry}
                  run={run}
                  history={
                    historyMatchesSelection ? historyQuery.data : undefined
                  }
                  historyLoading={historyEnabled && historyQuery.isPending}
                  historyError={
                    historyQuery.error?.message ??
                    (historyQuery.data && !historyMatchesSelection
                      ? "历史记录不属于当前项目，无法显示。"
                      : undefined)
                  }
                  onHistoryRun={selectHistoryRun}
                />
              ) : (
                <Empty>
                  <EmptyHeader>
                    <EmptyMedia variant="icon">
                      <ClipboardCheckIcon />
                    </EmptyMedia>
                    <EmptyTitle>暂时没有测试记录</EmptyTitle>
                    <EmptyDescription>
                      录入测试用例和结果后，可以在这里查看操作截图和说明。
                    </EmptyDescription>
                  </EmptyHeader>
                </Empty>
              )}
            </main>
          </div>
        </SidebarInset>
      </ReaderLayout>
    </SidebarProvider>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LegacyQueryRedirect />} />
        <Route path="/projects" element={<ProjectHome />} />
        <Route path="/projects/:projectId" element={<ReaderRoute />} />
        <Route
          path="/projects/:projectId/runs/:runId"
          element={<ReaderRoute />}
        />
        <Route
          path="/projects/:projectId/runs/:runId/cases/:caseId"
          element={<ReaderRoute />}
        />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  )
}
