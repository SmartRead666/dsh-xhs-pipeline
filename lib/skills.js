// 把插件自带的 skills/<name>/SKILL.md 注册进 DSH 的 skill 目录
import { existsSync, readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'

const RANK = 600
const INVOCATION = { modelInvocable: true, userInvocable: true }

function parse(file) {
  const text = readFileSync(file, 'utf8')
  const m = text.match(/^---\n([\s\S]*?)\n---\n?/)
  if (!m) return null
  const field = (k) => (m[1].match(new RegExp(`^${k}:\\s*(.+)$`, 'm')) || [])[1]?.trim().replace(/^(["'])(.*)\1$/, '$2')
  const name = field('name'), description = field('description')
  return name && description ? { name, description, body: text.slice(m[0].length) } : null
}

export function readSkills(dirs) {
  return [].concat(dirs).flatMap((dir) => {
    if (!existsSync(dir)) return []
    return readdirSync(dir, { withFileTypes: true })
      .filter((d) => d.isDirectory() && existsSync(join(dir, d.name, 'SKILL.md')))
      .map((d) => ({ dir: join(dir, d.name), file: join(dir, d.name, 'SKILL.md'), ...parse(join(dir, d.name, 'SKILL.md')) }))
      .filter((s) => s.name)
  })
}

// 插件环境下补充一段：脚本在哪、怎么调用工具
function addendum(skill, pluginRoot) {
  return `
---

## 在本插件里使用

- 本 skill 目录：\`${skill.dir}\`
- 脚本随插件提供：\`${join(pluginRoot, 'runner')}\`，用 \`XHS_HOME\` 指向的工作目录读写数据
- 出图 / 排期 / 监测请优先调用插件工具 \`xhs_render\`、\`xhs_publish\`、\`xhs_monitor\`（它们会自己找到配置好的账号和脚本）
- 首次使用前，让用户先跑一次 \`runner/setup.py\` 并把账号写进 \`~/.dsh/xhs-pipeline.json\` 的 home 目录下 config.json
`
}

export function createSkillProvider(dir, pluginRoot) {
  const candidate = (s) => ({
    name: s.name, description: s.description, path: s.file,
    invocation: INVOCATION, source: 'bundled', provider: 'xhs-pipeline', rank: RANK, locator: s.dir,
    resourceBase: { kind: 'directory', path: s.dir },
  })
  return {
    name: 'xhs-pipeline',
    async list() {
      return readSkills(dir).map(candidate)
    },
    async get(c) {
      const s = readSkills(dir).find((x) => x.dir === c.locator && x.name === c.name)
      if (!s) return undefined
      const content = s.body.replaceAll('<SKILL_ROOT>', s.dir).replaceAll('<PLUGIN_ROOT>', pluginRoot) + addendum(s, pluginRoot)
      const { rank, locator, ...summary } = candidate(s)
      return { ...summary, content }
    },
  }
}
