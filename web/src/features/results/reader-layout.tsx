import type { ReactNode } from "react"

import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"
import { useSidebar } from "@/components/ui/sidebar"

// 电脑目录与正文共同分配宽度；手机继续由 Sidebar 的 Sheet 管理目录。
export function ReaderLayout({
  sidebar,
  children,
}: {
  sidebar: ReactNode
  children: ReactNode
}) {
  const { isMobile, open } = useSidebar()
  if (isMobile)
    return (
      <>
        {sidebar}
        {children}
      </>
    )

  return (
    <ResizablePanelGroup orientation="horizontal">
      {sidebar && open && (
        <>
          <ResizablePanel
            id="case-directory"
            defaultSize="288px"
            minSize="240px"
            maxSize="50%"
          >
            {sidebar}
          </ResizablePanel>
          <ResizableHandle withHandle aria-label="调整目录宽度" />
        </>
      )}
      <ResizablePanel id="test-content" minSize="50%">
        {children}
      </ResizablePanel>
    </ResizablePanelGroup>
  )
}
