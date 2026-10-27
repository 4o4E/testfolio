import { create } from "zustand"
import type { CatalogScope, StatusFilter } from "./model"

interface ReaderState {
  search: string
  statusFilter: StatusFilter
  scope: CatalogScope
  expandedDirectories: Record<string, boolean>
  setSearch: (value: string) => void
  setStatusFilter: (value: StatusFilter) => void
  setScope: (value: CatalogScope) => void
  setDirectoriesOpen: (keys: string[], open: boolean) => void
}

export function directoryKeys(projectId: string, path: string[]) {
  return path.map((_, index) =>
    JSON.stringify([projectId, ...path.slice(0, index + 1)])
  )
}

// 路由负责记录位置；目录状态由项目及完整路径区分，父目录收起后仍保留子目录状态。
export const useReaderStore = create<ReaderState>((set) => ({
  search: "",
  statusFilter: "all",
  scope: "run",
  expandedDirectories: {},
  setSearch: (search) => set({ search }),
  setStatusFilter: (statusFilter) => set({ statusFilter }),
  setScope: (scope) => set({ scope }),
  setDirectoriesOpen: (keys, open) =>
    set((state) => ({
      expandedDirectories: {
        ...state.expandedDirectories,
        ...Object.fromEntries(keys.map((key) => [key, open])),
      },
    })),
}))
