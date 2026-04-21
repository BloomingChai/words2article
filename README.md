# Momo Daily Writer

一个本机命令行工具：从墨墨背单词拉取当天新学单词，结合本地 `Momo words` 词库释义，调用 OpenAI 兼容接口生成双语短文。

## 功能

- 拉取当天新学单词
- 用本地 `momowords.core.json` 补充中文释义和例句
- 本地词书缺词时，自动用大模型补全简短义项并缓存
- 调用 OpenAI 兼容接口生成英汉对照文章
- 默认缓存原始数据、提示词和当天文章
- 再次运行时，若当天文章已存在则直接显示

## 项目结构

项目现在按职责拆成了多个模块，便于单独修改和排查：

- `momo/cli.py`：命令行参数解析
- `momo/config.py`：配置读取与校验
- `momo/http.py`：通用 HTTP JSON 请求封装
- `momo/study_api.py`：墨墨学习数据获取与空结果诊断
- `momo/words.py`：词书加载、单词匹配、过滤、报告格式化
- `momo/llm.py`：缺词补全与文章生成的大模型调用
- `momo/article.py`：文章提示词构建
- `momo/storage.py`：输出路径、缓存、文章写入
- `momo/app.py`：主流程编排

## 配置

项目通过环境变量读取配置。

必需环境变量：

- `MOMO_API_TOKEN`
- `LLM_API_KEY` 或 `OPENAI_API_KEY`

可选环境变量：

- `MOMO_API_URL`，默认 `https://open.maimemo.com/open/api/v1/study/get_today_items`
- `LLM_API_URL`，默认 `https://api.siliconflow.cn/v1/chat/completions`
- `LLM_MODEL`，默认 `Pro/deepseek-ai/DeepSeek-V3.2`

仓库里提供了 `.env.example` 作为示例。

## 用法

直接显示今天文章；如果还没生成，会自动生成：

```bash
python3 -m momo
```

默认会请求当天的新学单词，并保留 `FAMILIAR`、`VAGUE`、`FORGET` 等单词，只排除 `first_response=WELL_FAMILIAR` 的词，也就是你当天标记为“非常熟悉”的词。
如果你想把这些词也包含进来，可以加上：

```bash
python3 -m momo --include-well-familiar
```

只看今天的新词：

```bash
python3 -m momo words
```

强制重新生成今天文章：

```bash
python3 -m momo generate --force
```

只基于当天缓存重新请求 LLM，不重新拉取单词：

```bash
python3 -m momo regenerate
```

只打印，不写入输出文件：

```bash
python3 -m momo today --stdout-only
```

## 输出

- 文章默认写入 `output/YYYY-MM-DD.md`
- 同时会额外同步一份到 `/Users/chai/Documents/Obsidian Vault/words2article/YYYY-MM-DD.md`
- 缓存默认写入 `cache/`
  - `YYYY-MM-DD-today-items.json`
  - `YYYY-MM-DD-words.json`
  - `YYYY-MM-DD-prompt.txt`
  - `word_supplements.json`

`regenerate` 会优先复用 `YYYY-MM-DD-words.json` 和 `YYYY-MM-DD-prompt.txt`，因此更适合反复测试模型输出效果。

## 说明

- 当前版本只按 `voc_spelling` 做精确匹配和大小写归一化匹配。
- 当前版本只支持 `momowords.core.json` 这套词库结构，读取 `definitions` 和 `examples` 字段。
- 如果词书中缺少某个单词，工具仍会继续生成文章，但会提示模型谨慎使用该词。
- 如果当天墨墨接口没有返回新词，工具会直接提示并退出。

## 本地配置与运行

可以直接在 shell 中 export：

```bash
export MOMO_API_TOKEN="你的墨墨 token"
export LLM_API_KEY="你的大模型 key"
python3 -m momo
```

也可以基于示例文件创建本地 `.env`，再手动加载：

```bash
cp .env.example .env
# 编辑 .env，填入真实值
set -a
source .env
set +a
python3 -m momo
```
