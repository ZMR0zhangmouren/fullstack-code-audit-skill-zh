# DYNAMIC_VERIFY(STATIC_UNIT) 单元级动态验证模板

本文件定义 pending_pool 中「闭合方式 = dynamic-unit」条目的本地动态验证执行规范，供 dotnet-audit-pipeline / node-audit-pipeline 阶段 7 及人工执行使用。目的：让「已确认（动态验证）」级标签有一条零凭证的本地执行路径（唯一合规触发路径见本文件；两条 pipeline 的既有语义原文不变）。

## 适用范围

- 仅适用于 pending_pool 中「闭合方式 = dynamic-unit 且状态 = OPEN」的条目
- 仅适用于「单元测试级可复现」项（如 validateParams every/some 取反、正则过度转义等纯逻辑缺陷）
- 不适用于集成级项（服务启动 / 测试租户 / 凭证托管），这类条目的闭合方式为 `needs-env`，本阶段跳过不尝试，集成级另立项
- 测试工程为临时工程，跑完即弃，不并入目标仓库

## 红线自检（运行前强制逐项 PASS）

以下四零红线必须逐项确认 PASS，任一不满足 → 整阶段 NOT_RUN 并在报告中注明原因：

1. **零凭证**——不读取、不构造任何账号、token、连接串、cookie、密钥
2. **零网络**——不发起任何出站请求（loopback 亦禁止），不进行 DNS 解析
3. **零服务**——不启动任何监听端口、不启动任何后台进程 / 守护进程
4. **零 scratch 目录外写入**——测试工程与全部产物只写入 `{output_root}/quality/dynamic_verify_scratch/`，不改目标仓库任何文件

**纯函数前提**：被测函数 / 模块必须为纯函数 / 纯模块（无 I/O 副作用——不读写文件、不访问网络、不查环境变量以外的全局状态）。该前提由登记项的「缺失证据」字段佐证：登记时须确认缺失证据仅为"缺少动态触发观察"，而非"缺少运行环境"。不能满足纯函数前提的条目不得走本路径，应改判闭合方式或另立项。

自检表（逐条填写，全部 ✔ 方可进入生成与运行）：

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 零凭证 | ☐ PASS / ☐ FAIL | {说明} |
| 零网络 | ☐ PASS / ☐ FAIL | {说明} |
| 零服务 | ☐ PASS / ☐ FAIL | {说明} |
| 零 scratch 目录外写入 | ☐ PASS / ☐ FAIL | {说明} |
| 被测函数为纯函数 / 纯模块 | ☐ PASS / ☐ FAIL | 依据登记项「缺失证据」：{缺失证据} |

## dotnet 模板

**复制不引用策略**：从目标仓库**复制**被测源文件到 scratch 测试工程目录，**不引用**目标项目（不添加 ProjectReference / 不 `<Compile Include>` 目标仓库路径之外的文件、不还原目标项目的 NuGet 依赖图），避免触发目标项目依赖图与构建副作用。被测文件复制后原则上只允许为通过编译做最小适配（如删除无关 using），不得改动被测逻辑本身。

临时 xunit 工程骨架（在 `{output_root}/quality/dynamic_verify_scratch/case_{pool_id}/` 下创建）：

````xml
<!-- case_{pool_id}/VerifyCase_{pool_id}.csproj 关键行 -->
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <IsPackable>false</IsPackable>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.9.0" />
    <PackageReference Include="xunit" Version="2.7.0" />
    <PackageReference Include="xunit.runner.visualstudio" Version="2.5.7" />
  </ItemGroup>
  <!-- 复制进来的被测源文件（来自目标仓库，复制非引用） -->
  <ItemGroup>
    <Compile Include="src/{被测文件相对路径}" />
  </ItemGroup>
</Project>
````

单测类结构：

````csharp
// case_{pool_id}/UnitTest_{pool_id}.cs
using Xunit;

namespace DynamicVerify;

public class UnitTest_{pool_id}
{
    // 断言按登记项「补证动作」逐条编写：
    // 例如补证动作为「单测复现 validateParams every/some 取反」→
    // 构造触发输入，断言实际行为与补证动作描述一致
    [Fact]
    public void {pool_id}_{scenario_name}()
    {
        // Arrange: 构造最小触发输入（取自登记项「关联链/发现」中的调用点参数）
        // Act: 调用被测纯函数
        // Assert: 断言预期行为（按「补证动作」编写，禁止写永真断言）
        Assert.Equal({expected}, {actual});
    }
}
````

断言编写指引：

- 每条「补证动作」至少对应一个 `[Fact]` 测试方法，测试方法名带 pool_id 便于回溯
- 断言必须可失败：禁止 `Assert.True(true)` 之类永真断言；失败本身就是有效结果（记 FAILED 保持 OPEN）
- 触发输入从登记项「关联链/发现」的调用点摘录，不得凭空捏造

运行与输出保存：

```bash
cd "{output_root}/quality/dynamic_verify_scratch/case_{pool_id}"
dotnet test --logger "console;verbosity=detailed" > run_{pool_id}.log 2>&1
```

## node 模板

**复制不引用策略**：同 dotnet 侧——用 `cp` 将被测源文件复制到 scratch 测试工程目录，通过相对路径 import 复制的副本；禁止 `require` / `import` 目标仓库的绝对路径，禁止执行目标仓库的 postinstall / 构建脚本，避免触发其依赖图。

临时 vitest 工程骨架（若环境无 vitest，可用 `node --test` 原生 runner，二选一）：

````text
case_{pool_id}/
├── package.json        # 仅含 vitest devDependency（或 node --test 时为最小空包）
├── src/
│   └── {被测文件副本.js}   # 从目标仓库复制
└── test_{pool_id}.test.js
````

````json
// package.json
{
  "name": "dynamic-verify-case-{pool_id}",
  "private": true,
  "type": "module",
  "scripts": { "test": "vitest run" },
  "devDependencies": { "vitest": "^1.6.0" }
}
````

````js
// test_{pool_id}.test.js —— vitest 版本；node:test 版本改用 node:test / node:assert 同等结构
import { describe, it, expect } from 'vitest';
import { {被测导出} } from './src/{被测文件副本.js}';

// 断言按登记项「补证动作」逐条编写
describe('{pool_id}', () => {
  it('{scenario_name}', () => {
    // Arrange: 构造最小触发输入（取自登记项「关联链/发现」）
    // Act + Assert: 断言实际行为与补证动作描述一致，禁止永真断言
    expect({actual}).toBe({expected});
  });
});
````

运行与输出保存：

```bash
cd "{output_root}/quality/dynamic_verify_scratch/case_{pool_id}"
npx vitest run > run_{pool_id}.log 2>&1
# 或（无 vitest 时）：node --test > run_{pool_id}.log 2>&1
```

## 运行与回写协议

- **测试工程路径规范**：`{output_root}/quality/dynamic_verify_scratch/case_{pool_id}/`（fullstack 为 `{output_root}/quality/`，单栈同；全仓仅此目录允许写入）
- **运行输出保存**：每案例完整运行输出存 `case_{pool_id}/run_{pool_id}.log`，作为动态复核的输出证据
- **产物报告**：`quality/dynamic_verify_report_{timestamp}.md`，逐条记录 `pool_id | 闭合方式 | 结果(VERIFIED/FAILED/SKIPPED) | 测试工程路径 | 运行输出摘要`
- **回写语义**：
  - 通过 → 报告记 `VERIFIED`，pending_pool 条目状态翻转为 `DYNAMIC_VERIFIED`，关联发现的报告 / PoC 方可标注「已确认（动态验证）」（引用报告路径）
  - 失败 → 报告记 `FAILED + 输出摘要`，**池条目保持 OPEN** 并记录失败原因，禁止标 `DYNAMIC_VERIFIED`
  - `needs-env` 条目 → 本阶段跳过不尝试（SKIPPED），集成级另立项
- **保守语义（防虚高）**：本阶段任何结果不改变 `audit_surface_status` 判定逻辑；报告只影响 pending_pool 的 `open_count` / `dynamic_verified_count` 分桶计数，`pool_total` 口径不变
- **清理**：报告落盘与池条目回写完成后，scratch 目录保留至本轮审计收尾确认无误再清理；清理动作本身不得触碰 scratch 之外任何路径

## 最低验收要求

- [ ] 红线四零自检表逐项 PASS，且记录于 `run_{pool_id}.log` 头部或随附说明
- [ ] 测试工程完整位于 `dynamic_verify_scratch/case_{pool_id}/` 内，零目录外写入
- [ ] 被测源文件为复制副本，不引用目标项目，未改动被测逻辑
- [ ] 每条「补证动作」至少一个可失败断言，无永真断言
- [ ] 报告逐条给出 VERIFIED / FAILED / SKIPPED 及运行输出摘要
- [ ] FAILED 条目池状态保持 OPEN 并记录失败原因
- [ ] 全程未触碰 `audit_surface_status` 判定逻辑

消费侧（dotnet pipeline 阶段 7 报告节）要求红线核验表头逐字引用本节四零条款；直接人工使用本模板时同样适用
