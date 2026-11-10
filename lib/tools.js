// 插件注册给模型的 3 个工具：出图 / 排期 / 监测
import { loadConfig, runScript } from './runner.js'

const str = (description, extra = {}) => ({ type: 'string', description, ...extra })
const text = (value) => [{ type: 'text', text: value }]

function check(args, schema) {
  const errs = []
  for (const k of schema.required || []) if (args?.[k] === undefined || args[k] === '') errs.push(`缺少 ${k}`)
  if (errs.length) throw new Error(errs.join('；'))
}

const ACC = str('账号 slug（在 config.json 的 accounts 里配置）')

const OUTPUT = {
  schema: {
    type: 'object',
    additionalProperties: false,
    required: ['output'],
    properties: { output: { type: 'string' } },
  },
  render: (_args, v) => text(v.output),
}

export const renderTool = {
  name: 'xhs_render',
  description: '把一天的内容 JSON 渲染成 6 张 3:4 小红书图 + 发布包（post.md / publish.json）。',
  parameters: {
    type: 'object', additionalProperties: false, required: ['account', 'day'],
    properties: {
      account: ACC,
      day: str('内容 JSON 路径：绝对路径，或相对 runner 目录的 examples/day01.json'),
    },
  },
  timeoutMs: 300_000,
  output: OUTPUT,
  async execute(args) {
    check(args, this.parameters)
    const cfg = loadConfig()
    const out = await runScript(cfg, 'render.py', ['--account', args.account, '--day', args.day])
    if (out.code !== 0) throw new Error('渲染失败：\n' + out.output.slice(-1500))
    return { output: out.output }
  },
}

export const publishTool = {
  name: 'xhs_publish',
  description: '把已渲染的发布包定时发布到小红书（浏览器自动化）。遇到扫码验证时会等待用户扫码。',
  parameters: {
    type: 'object', additionalProperties: false, required: ['account', 'dayDir'],
    properties: {
      account: ACC,
      dayDir: str('发布包目录名，例如 01_2026-11-10_痛值愿'),
      time: str('定时发布时间 YYYY-MM-DD HH:MM（北京时间）；draft=true 时可省略'),
      draft: str('填 "true" 只存草稿，不发布', { enum: ['true', 'false'] }),
    },
  },
  timeoutMs: 900_000,
  output: OUTPUT,
  async execute(args) {
    check(args, this.parameters)
    const cfg = loadConfig()
    const argv = ['--account', args.account, '--day', args.dayDir]
    if (args.draft === 'true') argv.push('--draft')
    else {
      if (!args.time) throw new Error('定时发布需要 time')
      argv.push('--time', args.time)
    }
    const out = await runScript(cfg, 'publish.py', argv, 900_000)
    const fail = { 2: '需要登录创作中心（先跑 login.py 扫码）', 3: '扫码验证超时' }
    if (out.code !== 0) throw new Error((fail[out.code] || '发布失败') + '\n' + out.output.slice(-1500))
    return { output: out.output }
  },
}

export const monitorTool = {
  name: 'xhs_monitor',
  description: '检查某个小红书账号的评论/@、私信、赞藏、关注的未读变化；有新增时返回数量。',
  parameters: {
    type: 'object', additionalProperties: false, required: ['account'],
    properties: { account: ACC },
  },
  timeoutMs: 300_000,
  output: OUTPUT,
  async execute(args) {
    check(args, this.parameters)
    const cfg = loadConfig()
    const out = await runScript(cfg, 'monitor.py', ['--account', args.account], 300_000)
    if (out.code !== 0) throw new Error('监测失败：\n' + out.output.slice(-1500))
    return { output: out.output }
  },
}

export const setupTool = {
  name: 'xhs_setup',
  description: '首次使用时初始化小红书流水线：建工作目录、检查 playwright 与 Chrome、下载字体、生成 config.json。装好插件后先跑这个。',
  parameters: {
    type: 'object', additionalProperties: false,
    properties: { home: str('工作目录（可选），默认 ~/xhs-workspace') },
  },
  timeoutMs: 300_000,
  output: OUTPUT,
  async execute(args) {
    const cfg = loadConfig()
    const argv = args && args.home ? ['--home', args.home] : []
    const out = await runScript(cfg, 'setup.py', argv, 300_000)
    return { output: out.output }
  },
}

export const TOOLS = [setupTool, renderTool, publishTool, monitorTool]
