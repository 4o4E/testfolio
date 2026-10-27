import { create } from "zustand"
import type { CatalogScope, StatusFilter } from "./model"

interface ReaderState {
  search: string
  statusFilter: StatusFilter
  scope: CatalogScope
  setSearch: (value: string) => void
  setStatusFilter: (value: StatusFilter) => void
  setScope: (value: CatalogScope) => void
}

// 路由负责项目、轮次和用例位置；Zustand只保存筛选与搜索等界面状态。
export const useReaderStore = create<ReaderState>((set) => ({
  search: "",
  statusFilter: "all",
  scope: "run",
  setSearch: (search) => set({ search }),
  setStatusFilter: (statusFilter) => set({ statusFilter }),
  setScope: (scope) => set({ scope }),
}))
