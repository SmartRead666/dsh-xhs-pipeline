// 配置读取 + 调用 python 脚本
import { existsSync, readFileSync, readdirSync, statSync, mkdirSync, writeFileSync } from 'node:fs'
import { spawn } from 'node:child_process'
import { homedir } from 'node:os'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = fileURLToPath(new URL('..', import.meta.url))
const RUNNER = join(ROOT, 'runner')

export function configPath() {
  if (process.env.XHS_PLUGIN_CONFIG) return process.env.XHS_PLUGIN_CONFIG
  const dshHome = process.env.DSH_HOME || join(homedir(), '.dsh')
  return join(dshHome, 'xhs-pipeline.json')
}

function findPython(cfg) {
  if (cfg && cfg.python && existsSync(cfg.python)) return cfg.python
  // DSH 自带 python 的候选路径（Windows / macOS / Linux）
  const runtimeDirs = []
  try {
    const root = join(homedir(), '.dsh', 'dsh-runtimes')
    if (existsSync(root)) for (const d of readdirSync(root)) runtimeDirs.push(join(root, d, 'dependencies', 'python'))
  } catch {}
  const cands = [
    process.env.XHS_PYTHON,
    join(homedir(), '.dsh', 'dsh-runtimes', 'dsh-primary-runtime', 'dependencies', 'python', 'python.exe'),
    ...runtimeDirs.flatMap((d) => [
      join(d, 'python.exe'),
      join(d, 'bin', 'python3'),
      join(d, 'bin', 'python'),
    ]),
    '/opt/homebrew/bin/python3',
    '/usr/local/bin/python3',
    '/usr/bin/python3',
    'python',
    'python3',
  ].filter(Boolean)
  for (const c of cands) {
    if (c === 'python' || c === 'python3') return c
    if (existsSync(c)) return c
  }
  return 'python'
}

// 首次启动自举：缺配置就生成一份可用的默认配置，避免同事卡在「缺少插件配置」
function bootstrapConfig(p) {
  try {
    mkdirSync(dirname(p), { recursive: true })
    writeFileSync(p, JSON.stringify({
      home: join(homedir(), 'xhs-workspace'),
      python: '',
      update: { enabled: false },
    }, null, 2))
  } catch {}
}

function bootstrapHome(home) {
  try {
    for (const d of ['photos', 'fonts', 'profiles', 'output']) mkdirSync(join(home, d), { recursive: true })
    const cfgPath = join(home, 'config.json')
    if (!existsSync(cfgPath)) {
      writeFileSync(cfgPath, JSON.stringify({
        home,
        fonts_dir: '',
        _hint: '把 accounts 改成你自己的账号；每个账号一项 {slug, name, handle, default_time}，slug 用英文且不要重复。',
        accounts: [],
      }, null, 2))
    }
  } catch {}
}

export function loadConfig() {
  const p = configPath()
  if (!existsSync(p)) bootstrapConfig(p)
  const cfg = JSON.parse(readFileSync(p, 'utf8').replace(/^\uFEFF/, ''))
  const home = (cfg.home || '~/xhs-workspace').replace(/^~/, homedir())
  bootstrapHome(home)
  const homeCfgPath = join(home, 'config.json')
  let accounts = cfg.accounts || []
  if (existsSync(homeCfgPath)) {
    try { accounts = JSON.parse(readFileSync(homeCfgPath, 'utf8').replace(/^\uFEFF/, '')).accounts || accounts } catch {}
  }
  return { ...cfg, home, accounts, python: findPython(cfg), runner: RUNNER }
}

export function listDays(cfg) {
  const out = []
  for (const acc of cfg.accounts || []) {
    const dir = join(cfg.home, 'output', acc.slug)
    if (!existsSync(dir)) continue
    for (const name of readdirSync(dir)) {
      const full = join(dir, name)
      try {
        if (!statSync(full).isDirectory()) continue
      } catch { continue }
      const pj = join(full, 'publish.json')
      if (!existsSync(pj)) continue
      try {
        const pkg = JSON.parse(readFileSync(pj, 'utf8'))
        out.push({
          account: acc.slug, accountName: acc.name, dir: name,
          day: pkg.day, date: pkg.date, time: pkg.time, style: pkg.style,
          title: pkg.title, images: (pkg.images || []).length,
          status: pkg.status || '', scheduledAt: pkg.scheduled_at || '',
        })
      } catch {}
    }
  }
  return out.sort((a, b) => String(a.date).localeCompare(String(b.date)))
}

export function runScript(cfg, script, args, timeout = 300_000) {
  return new Promise((resolve) => {
    const file = join(RUNNER, script)
    if (!existsSync(file)) return resolve({ code: 1, output: '找不到脚本：' + file })
    const child = spawn(cfg.python, [file, ...args], {
      cwd: RUNNER,
      env: {
        ...process.env,
        XHS_HOME: cfg.home,
        XHS_CONFIG: join(cfg.home, 'config.json'),
        PYTHONIOENCODING: 'utf-8',
      },
      windowsHide: true,
    })
    let output = ''
    const timer = setTimeout(() => { try { child.kill() } catch {} ; output += '\n（超时已终止）' }, timeout)
    child.stdout.on('data', (d) => { output += d.toString() })
    child.stderr.on('data', (d) => { output += d.toString() })
    child.on('error', (e) => { clearTimeout(timer); resolve({ code: 1, output: output + '\n' + e.message }) })
    child.on('close', (code) => { clearTimeout(timer); resolve({ code: code ?? 1, output }) })
  })
}
