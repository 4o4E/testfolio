import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  humanTitle,
  runCaption,
  statusLabels,
  statusOf,
  type CaseEntry,
  type CaseHistory,
  type Evidence,
  type TestRun,
} from "./model"
import { Screenshot } from "./screenshot"

const badgeVariant: Record<
  string,
  "default" | "secondary" | "destructive" | "outline"
> = {
  passed: "secondary",
  failed: "destructive",
  blocked: "destructive",
  not_run: "outline",
  skipped: "outline",
  not_included: "outline",
}

const images = (items: Evidence[]) =>
  items.filter((item) => (item.media_type ?? "image/png").startsWith("image/"))
const files = (items: Evidence[]) =>
  items.filter((item) => !(item.media_type ?? "image/png").startsWith("image/"))

function StatusBadge({ status }: { status: string }) {
  return (
    <Badge variant={badgeVariant[status] ?? "outline"}>
      {statusLabels[status as keyof typeof statusLabels] ?? status}
    </Badge>
  )
}

function ScreenshotList({ items }: { items: Evidence[] }) {
  return (
    <div className="flex min-w-0 flex-col gap-4">
      {items.map((item, index) => (
        <Screenshot key={`${item.artifact_id}-${index}`} evidence={item} />
      ))}
    </div>
  )
}

function AttachmentList({ items }: { items: Evidence[] }) {
  if (items.length === 0)
    return <p className="text-sm text-muted-foreground">没有其他报告附件。</p>
  return (
    <ul className="flex flex-col gap-2">
      {items.map((item, index) => (
        <li key={`${item.artifact_id}-${index}`}>
          <a
            className="text-sm break-all underline underline-offset-4"
            href={`/artifacts/${encodeURIComponent(item.artifact_id)}`}
            target="_blank"
            rel="noreferrer"
          >
            {item.caption || `附件 ${item.artifact_id}`}
          </a>
          <span className="ml-2 text-xs text-muted-foreground">
            {item.media_type || "未知文件类型"}
          </span>
        </li>
      ))}
    </ul>
  )
}

function Expected({ value }: { value: string }) {
  return (
    <Accordion type="single" collapsible>
      <AccordionItem value="expected" className="border-b-0">
        <AccordionTrigger className="py-1 text-xs font-normal text-muted-foreground">
          查看预期结果
        </AccordionTrigger>
        <AccordionContent>
          <p className="text-sm break-words whitespace-pre-wrap">
            {value || "未填写预期结果。"}
          </p>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  )
}

function StepSection({
  action,
  caption,
  actual,
  expected,
  evidence,
  status,
  index,
}: {
  action: string
  caption?: string
  actual?: string
  expected?: string
  evidence: Evidence[]
  status?: string
  index: number
}) {
  return (
    <section className="flex min-w-0 flex-col gap-3 rounded-xl border bg-card p-3 sm:p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-base font-semibold">
          {caption || `步骤 ${index + 1}`}
        </h2>
        {status && <StatusBadge status={status} />}
      </div>
      <p className="text-sm leading-6 break-words whitespace-pre-wrap">
        {action}
      </p>
      {evidence.length > 0 && <ScreenshotList items={evidence} />}
      {actual !== undefined && (
        <div className="flex flex-col gap-2">
          <h3 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
            实际结果
          </h3>
          <p className="text-sm leading-6 break-words whitespace-pre-wrap">
            {actual || "没有填写本步骤的实际观察结果。"}
          </p>
        </div>
      )}
      {expected !== undefined && <Expected value={expected} />}
    </section>
  )
}

function lastParagraph(value: string) {
  return (
    value
      .split(/\n\s*\n/)
      .map((paragraph) => paragraph.trim())
      .filter(Boolean)
      .at(-1) ?? ""
  )
}

export function CaseReader({
  entry,
  run,
  history,
  historyLoading,
  historyError,
  onHistoryRun,
}: {
  entry: CaseEntry
  run: TestRun | null
  history: CaseHistory | undefined
  historyLoading: boolean
  historyError?: string
  onHistoryRun: (id: string) => void
}) {
  const { case: testCase, result, inScope } = entry
  const status = statusOf(entry)
  const resultImages = result ? images(result.evidence) : []
  const stepImages = result?.steps.map((step) => images(step.evidence)) ?? []
  const nonImageAttachments = result
    ? [
        ...files(result.evidence),
        ...result.steps.flatMap((step) => files(step.evidence)),
      ]
    : []
  const failedStep = result?.steps.find(
    (step) =>
      (step.status === "failed" || step.status === "blocked") &&
      step.actual.trim()
  )
  const failureReason =
    failedStep?.actual.trim() || (result ? lastParagraph(result.actual) : "")
  const failure = result?.status === "failed" || result?.status === "blocked"

  return (
    <article className="flex min-w-0 flex-col gap-5">
      <header className="flex flex-col gap-2">
        <div className="flex items-center gap-2">
          <StatusBadge status={status} />
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
            {humanTitle(testCase)}
          </h1>
        </div>
        {testCase.path.length > 0 && (
          <p className="text-sm text-muted-foreground">
            {testCase.path.join(" / ")}
          </p>
        )}
      </header>

      {!inScope ? (
        <Alert>
          <AlertTitle>本轮未包含此用例</AlertTitle>
          <AlertDescription>
            当前测试轮次没有执行或记录此用例。下方仅展示用例定义。
          </AlertDescription>
        </Alert>
      ) : !result ? (
        <Alert>
          <AlertTitle>本轮没有测试结果</AlertTitle>
          <AlertDescription>
            此用例属于当前轮次，但没有提交执行结果。下方操作和预期来自用例定义，不代表已经执行。
          </AlertDescription>
        </Alert>
      ) : null}

      {failure && (
        <Alert variant="destructive">
          <AlertTitle>
            {result?.status === "failed" ? "失败原因" : "受阻原因"}
          </AlertTitle>
          <AlertDescription>
            {failureReason || "结果标记为异常，但记录中没有填写具体原因。"}
          </AlertDescription>
        </Alert>
      )}

      {resultImages.length > 0 && (
        <section className="flex min-w-0 flex-col gap-3">
          <h2 className="text-base font-semibold">本次记录截图</h2>
          <ScreenshotList items={resultImages} />
        </section>
      )}

      {result?.steps.length ? (
        result.steps.map((step, index) => (
          <StepSection
            key={`${index}-${step.action}`}
            index={index}
            action={step.action}
            caption={
              step.evidence.find((item) =>
                (item.media_type ?? "image/png").startsWith("image/")
              )?.caption
            }
            actual={step.actual}
            expected={step.expected}
            evidence={stepImages[index]}
            status={step.status}
          />
        ))
      ) : testCase.steps.length > 0 ? (
        testCase.steps.map((step, index) => (
          <StepSection
            key={`${index}-${step.action}`}
            index={index}
            action={step.action}
            expected={step.expected}
            evidence={[]}
          />
        ))
      ) : (
        <p className="text-sm text-muted-foreground">
          此用例没有定义操作步骤。
        </p>
      )}

      {result?.steps.length === 0 && !result.actual && (
        <p className="text-sm text-muted-foreground">
          结果中没有记录实际观察内容。
        </p>
      )}
      {result && result.steps.length === 0 && result.actual && (
        <section className="flex flex-col gap-2 rounded-xl border bg-card p-3 sm:p-4">
          <h2 className="text-base font-semibold">实际结果</h2>
          <p className="text-sm leading-6 break-words whitespace-pre-wrap">
            {result.actual}
          </p>
        </section>
      )}
      {result &&
        stepImages.every((items) => items.length === 0) &&
        resultImages.length === 0 && (
          <p className="rounded-lg border border-dashed px-4 py-4 text-sm text-muted-foreground">
            本次记录没有截图证据；实际结果仅以文字展示。
          </p>
        )}
      {result?.issues.length ? (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-semibold">关联问题</h2>
          {result.issues.map((issue) => (
            <a
              key={issue.url}
              className="text-sm break-all underline underline-offset-4"
              href={issue.url}
              target="_blank"
              rel="noreferrer"
            >
              {issue.title}
            </a>
          ))}
        </section>
      ) : null}

      <Accordion type="multiple" className="rounded-lg border px-3 sm:px-4">
        <AccordionItem value="definition">
          <AccordionTrigger>用例信息与测试环境</AccordionTrigger>
          <AccordionContent>
            <div className="flex flex-col gap-4">
              <div>
                <h3 className="text-sm font-medium">用例编号与优先级</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  {testCase.id} · {testCase.priority}
                </p>
              </div>
              {testCase.requirement && (
                <div>
                  <h3 className="text-sm font-medium">关联需求</h3>
                  <p className="mt-1 text-sm leading-6 whitespace-pre-wrap text-muted-foreground">
                    {testCase.requirement}
                  </p>
                </div>
              )}
              {testCase.preconditions.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium">前置条件</h3>
                  <ul className="mt-1 list-inside list-disc text-sm leading-6 text-muted-foreground">
                    {testCase.preconditions.map((item, index) => (
                      <li key={`${index}-${item}`}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
              <div>
                <h3 className="text-sm font-medium">标签与来源</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  {testCase.tags.length ? testCase.tags.join("、") : "无标签"}
                  {testCase.source ? ` · ${testCase.source}` : ""}
                </p>
              </div>
              {result?.notes && (
                <div>
                  <h3 className="text-sm font-medium">完整备注</h3>
                  <p className="mt-1 text-sm leading-6 break-words whitespace-pre-wrap text-muted-foreground">
                    {result.notes}
                  </p>
                </div>
              )}
              {run && (
                <div>
                  <h3 className="text-sm font-medium">当前测试轮次与环境</h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {run.title} · {runCaption(run)} · {run.environment}
                  </p>
                  {Object.keys(run.versions).length > 0 && (
                    <dl className="mt-2 grid gap-2 sm:grid-cols-2">
                      {Object.entries(run.versions).map(([name, version]) => (
                        <div key={name} className="flex gap-2 text-sm">
                          <dt className="text-muted-foreground">{name}</dt>
                          <dd className="break-all">{version}</dd>
                        </div>
                      ))}
                    </dl>
                  )}
                </div>
              )}
            </div>
          </AccordionContent>
        </AccordionItem>
        <AccordionItem value="attachments">
          <AccordionTrigger>报告与其他附件</AccordionTrigger>
          <AccordionContent>
            <AttachmentList items={nonImageAttachments} />
          </AccordionContent>
        </AccordionItem>
        <AccordionItem value="history">
          <AccordionTrigger>历史测试记录</AccordionTrigger>
          <AccordionContent>
            {historyError ? (
              <Alert variant="destructive">
                <AlertTitle>历史记录读取失败</AlertTitle>
                <AlertDescription>{historyError}</AlertDescription>
              </Alert>
            ) : historyLoading ? (
              <p className="text-sm text-muted-foreground">正在读取历史记录…</p>
            ) : history?.history.length ? (
              <ol className="flex flex-col gap-2">
                {history.history.map(
                  ({ run: historyRun, result: historyResult }) => (
                    <li
                      key={historyRun.id}
                      className="flex flex-col gap-2 rounded-lg border p-3 sm:flex-row sm:items-center sm:justify-between"
                    >
                      <div className="min-w-0">
                        <p className="font-medium">{historyRun.title}</p>
                        <p className="mt-1 text-sm text-muted-foreground">
                          {runCaption(historyRun)} · {historyRun.environment}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <StatusBadge
                          status={historyResult?.status ?? "not_run"}
                        />
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onHistoryRun(historyRun.id)}
                        >
                          查看该轮
                        </Button>
                      </div>
                    </li>
                  )
                )}
              </ol>
            ) : (
              <p className="text-sm text-muted-foreground">
                {history ? "没有历史测试记录。" : "尚未读取历史测试记录。"}
              </p>
            )}
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </article>
  )
}
