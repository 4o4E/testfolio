# Testfolio 网页

网页提供测试记录的只读查看界面，使用 React、TypeScript、Vite、React Router、shadcn/ui Nova（Radix）、Tailwind、Lucide 和 TanStack Query。Zustand 保存目录选择及筛选状态；项目与轮次数据从只读 API 读取。

用例步骤、截图和实际结果按记录展示。预期、定义、版本、报告及历史默认折叠；点击截图可查看原图和已有标注。网页不会创建或推断测试结果。

本地开发与检查：

```bash
npm ci
npm run dev
npm run lint
npm run build
```

生产构建由 Dockerfile 在镜像构建阶段生成，并复制到 Python 服务提供的静态资源目录。生产网页和读取 API 同源，不依赖外部字体或前端资源服务器。服务边界及运行方式见仓库根目录 [README.md](../README.md)。
