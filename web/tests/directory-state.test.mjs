import assert from "node:assert/strict"
import test from "node:test"
import { directoryKeys, useReaderStore } from "../src/features/results/store.ts"

test("目录独立展开，批量操作覆盖所有祖先且不同项目互不影响", () => {
  const first = directoryKeys("alpha", ["suite", "group"])
  const sibling = directoryKeys("alpha", ["another-suite", "group"])
  const otherProject = directoryKeys("beta", ["suite", "group"])
  const { setDirectoriesOpen } = useReaderStore.getState()
  const current = () => useReaderStore.getState().expandedDirectories

  assert.equal(new Set([...first, ...sibling, ...otherProject]).size, 6)
  setDirectoriesOpen(first, true)
  setDirectoriesOpen(sibling, true)
  assert([...first, ...sibling].every(key => current()[key]))
  assert(otherProject.every(key => current()[key] === undefined))

  setDirectoriesOpen([first[0]], false)
  assert.equal(current()[first[1]], true)
  assert(sibling.every(key => current()[key]))
  setDirectoriesOpen([first[0]], true)
  assert(first.every(key => current()[key]))

  setDirectoriesOpen([...first, ...sibling, ...otherProject], true)
  setDirectoriesOpen([...first, ...sibling], false)
  assert([...first, ...sibling].every(key => current()[key] === false))
  assert(otherProject.every(key => current()[key]))
})
