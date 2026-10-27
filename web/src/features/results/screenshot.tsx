import { useState } from "react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import type { Evidence, Rectangle } from "./model"

function position(
  box: Rectangle,
  width: number,
  height: number,
  originX = 0,
  originY = 0
) {
  return {
    left: `${((box.x - originX) / width) * 100}%`,
    top: `${((box.y - originY) / height) * 100}%`,
    width: `${(box.w / width) * 100}%`,
    height: `${(box.h / height) * 100}%`,
  }
}

function MarkOverlay({
  evidence,
  width,
  height,
  cropMarks = false,
}: {
  evidence: Evidence
  width: number
  height: number
  cropMarks?: boolean
}) {
  const crop = evidence.crop
  return (
    <>
      {!cropMarks && crop && (
        <span
          aria-hidden="true"
          className="pointer-events-none absolute border-2 border-dashed border-destructive bg-destructive/10"
          style={position(crop, width, height)}
        />
      )}
      {evidence.marks?.map((mark, index) => (
        <span
          key={`${mark.label}-${index}`}
          className="pointer-events-none absolute border-2 border-destructive bg-destructive/10"
          style={
            cropMarks && crop
              ? {
                  left: `${((mark.x - crop.x) / crop.w) * 100}%`,
                  top: `${((mark.y - crop.y) / crop.h) * 100}%`,
                  width: `${(mark.w / crop.w) * 100}%`,
                  height: `${(mark.h / crop.h) * 100}%`,
                }
              : position(mark, width, height)
          }
          aria-hidden="true"
        >
          <span className="absolute -top-3 -left-3 flex size-6 items-center justify-center rounded-full border border-destructive bg-background px-1 text-xs font-semibold text-destructive">
            {mark.label}
          </span>
        </span>
      ))}
    </>
  )
}

export function Screenshot({ evidence }: { evidence: Evidence }) {
  const [dimensions, setDimensions] = useState<{
    width: number
    height: number
  }>()
  const [failed, setFailed] = useState(false)
  const src = `/artifacts/${encodeURIComponent(evidence.artifact_id)}`
  const crop = dimensions
    ? (evidence.crop ?? {
        x: 0,
        y: 0,
        w: dimensions.width,
        h: dimensions.height,
      })
    : undefined

  if (failed) {
    return (
      <Alert variant="destructive">
        <AlertTitle>截图无法加载</AlertTitle>
        <AlertDescription>
          {evidence.caption || "系统未能读取这张证据图片。"}
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <figure className="w-full overflow-hidden rounded-xl border bg-muted/30">
      <Dialog>
        <DialogTrigger asChild>
          <Button variant="ghost" className="h-auto w-full rounded-none p-0">
            {dimensions && crop ? (
              <span
                className="relative block w-full overflow-hidden"
                style={{
                  aspectRatio: `${crop.w} / ${crop.h}`,
                  maxWidth: `${crop.w}px`,
                }}
              >
                <img
                  src={src}
                  alt={evidence.caption || "测试过程的原始截图，显示标记区域"}
                  className="absolute max-w-none"
                  style={{
                    width: `${(dimensions.width / crop.w) * 100}%`,
                    left: `${(-crop.x / crop.w) * 100}%`,
                    top: `${(-crop.y / crop.h) * 100}%`,
                  }}
                  loading="lazy"
                  onLoad={(event) =>
                    setDimensions({
                      width: event.currentTarget.naturalWidth,
                      height: event.currentTarget.naturalHeight,
                    })
                  }
                  onError={() => setFailed(true)}
                />
                <span className="absolute inset-0" aria-hidden="true">
                  <MarkOverlay
                    evidence={evidence}
                    width={crop.w}
                    height={crop.h}
                    cropMarks
                  />
                </span>
              </span>
            ) : (
              <span className="relative block w-full">
                <img
                  src={src}
                  alt={evidence.caption || "测试过程的原始截图"}
                  className="block h-auto w-full"
                  loading="lazy"
                  onLoad={(event) =>
                    setDimensions({
                      width: event.currentTarget.naturalWidth,
                      height: event.currentTarget.naturalHeight,
                    })
                  }
                  onError={() => setFailed(true)}
                />
              </span>
            )}
          </Button>
        </DialogTrigger>
        <DialogContent
          showCloseButton={false}
          className="max-h-[95vh] w-[96vw] max-w-none overflow-hidden sm:max-w-none"
        >
          <DialogHeader>
            <DialogTitle>{evidence.caption || "测试证据原图"}</DialogTitle>
            <DialogDescription>
              原始图片保持不变；矩形和编号对应测试记录中的证据标注。
            </DialogDescription>
          </DialogHeader>
          <div className="max-h-[calc(95vh-8rem)] overflow-auto">
            {dimensions && (
              <div
                className="relative w-fit"
                style={{
                  width: `${dimensions.width}px`,
                  height: `${dimensions.height}px`,
                }}
              >
                <img
                  src={src}
                  alt={evidence.caption || "测试过程的原始截图"}
                  className="block max-w-none"
                  width={dimensions.width}
                  height={dimensions.height}
                  loading="eager"
                />
                <MarkOverlay
                  evidence={evidence}
                  width={dimensions.width}
                  height={dimensions.height}
                />
              </div>
            )}
          </div>
          <DialogClose asChild>
            <Button variant="outline" className="justify-self-end">
              关闭
            </Button>
          </DialogClose>
        </DialogContent>
      </Dialog>
      {evidence.caption && (
        <figcaption className="border-t px-3 py-2 text-sm text-muted-foreground">
          {evidence.caption}
        </figcaption>
      )}
    </figure>
  )
}
