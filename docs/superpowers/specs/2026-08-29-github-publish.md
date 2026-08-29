# 智慧记运营测试专家 GitHub 首次发布规范

## 目标

将智慧记运营测试专家的可维护源码和文档保存到
`https://github.com/hansonzhang0606-ux/ZHJ_test_expert`，并让当前工作目录成为后续更新的本地 Git 工作目录。

## 入库范围

- `ZHJ_test_skills/` 中的源码、Skill 文档、配置模板、测试和参考资料。
- `docs/` 中的设计说明与实施计划。
- 仓库根目录的 `README.md` 与 `.gitignore`。

## 排除范围

- 所有 `*.zip`、`*.rar` 安装包或压缩文件。
- `deliverables/` 及其中的安装包、WorkBuddy 展开副本。
- MySQL 实际连接配置、运行记录、环境变量文件、私钥和凭据。
- Python 缓存、编辑器缓存、测试缓存和临时文件。

## 发布约束

- 保留远程仓库已有的 `main` 分支和 `Initial commit` 历史。
- 推送前运行时间追踪回归测试、Python AST 检查、排除文件检查和敏感文件名检查。
- 推送后读取远程 `main`，确认提交存在且远程树中没有 ZIP/RAR、运行配置或记录文件。

