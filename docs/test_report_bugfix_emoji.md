# Bug 修复测试报告 - UTF-8 转 GBK emoji 报错问题

**日期**：2026-11-07  
**问题类型**：UnicodeEncodeError  
**严重程度**：中（功能缺陷）

---

## 问题描述

用户报告：当从 UTF-8 编码转换为 GBK 编码时，如果源文件包含 emoji 字符（如 ✅ U+2705、🎉 U+1F389），转换会失败并报错：

```
'gbk' codec can't encode character '✅' in position 176: illegal multibyte sequence
```

## 根因分析

通过 systematic-debugging 流程：

1. **复现问题**：成功复现，确认 `UnicodeEncodeError` 错误
2. **分析原因**：GBK 编码字符集不包含 emoji 字符（U+2705 等）。这些字符属于 Unicode 补充平面，不在 GBK 的标准字符集内
3. **验证假设**：Python 标准库在写入文件时使用 `errors='strict'` 默认策略，遇到无法编码的字符会抛出 `UnicodeEncodeError`

## 修复方案

在 `Encoder` 类中添加 `errors` 参数，支持四种错误处理策略：

| 策略 | 行为 | 场景 |
|------|------|------|
| `strict`（默认） | 遇到无法编码的字符时抛出异常 | 严格校验，确保内容完整 |
| `replace` | 用 `?` 替换无法编码的字符 | 容忍部分字符丢失 |
| `ignore` | 跳过无法编码的字符 | 接受字符丢失 |
| `xmlcharrefreplace` | 用 XML 实体引用（如 `&#x2705;`）替换 | 保留字符信息 |

同时在 GUI 界面添加"错误处理"下拉选择框。

## 修改文件

| 文件 | 修改内容 |
|------|----------|
| `converter/encoder.py` | `Encoder.__init__` 添加 `errors` 参数；`convert` 方法传递 `errors` 到文件写入 |
| `gui/app.py` | 添加"错误处理"下拉选择框；`start_conversion` 传递错误策略 |
| `tests/test_encoder.py` | 添加 2 个新测试：replace 和 ignore 策略 |
| `README.md` | 添加错误处理策略说明 |

## 测试结果

### 新增测试（2 个）

| 测试名称 | 内容 | 结果 |
|----------|------|------|
| test_emoji_to_gbk_with_replace | emoji 转 GBK 使用 replace 策略 | ✅ PASSED |
| test_emoji_to_gbk_with_ignore | emoji 转 GBK 使用 ignore 策略 | ✅ PASSED |

### 全部测试

| 测试文件 | 测试数 | 通过 | 结果 |
|----------|--------|------|------|
| test_encoder.py | 9 | 9 | ✅ |
| test_utils.py | 7 | 7 | ✅ |
| test_app.py | 9 | 9 | ✅ |
| test_main.py | 5 | 5 | ✅ |
| **总计** | **30** | **30** | ✅ |

### 手动验证

| 场景 | 结果 |
|------|------|
| 含 ✅ 的 MD 文件 UTF-8→GBK（strict） | ✅ 按预期报错 |
| 含 ✅ 的 MD 文件 UTF-8→GBK（replace） | ✅ 成功，✅ 变为 ? |
| 含 ✅ 的 MD 文件 UTF-8→GBK（ignore） | ✅ 成功，✅ 被忽略 |
| 纯中文文本 UTF-8→GBK | ✅ 正常，内容一致 |

## 结论

Bug 已修复，所有测试通过。用户现在可以选择错误处理策略来处理无法编码的字符。
