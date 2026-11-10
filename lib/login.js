// 无头登录 sidecar 管理：启动 qr_login.py 后台进程，读取二维码与状态
import { existsSync, mkdirSync, readFileSync, rmSync } from 'node:fs'
import { spawn } from 'node:child_process'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = fileURLToPath(new URL('..', import.meta.url))
const RUNNER = join(ROOT, 'runner')

export function loginStateDir(cfg, slug, site) {
  return join(cfg.home, '_work', `login-${slug}-${site}`)
}

export function startQrLogin(cfg, slug, site) {
  const state = loginStateDir(cfg, slug, site)
  mkdirSync(state, { recursive: true })
  for (const f of ['status.json', 'qr.png']) {
    try { rmSync(join(state, f), { force: true }) } catch {}
  }
  const child = spawn(cfg.python, [join(RUNNER, 'qr_login.py'),
    '--account', slug, '--site', site, '--state', state], {
    cwd: RUNNER,
    env: {
      ...process.env,
      XHS_HOME: cfg.home,
      XHS_CONFIG: join(cfg.home, 'config.json'),
      PYTHONIOENCODING: 'utf-8',
    },
    detached: true,
    stdio: 'ignore',
    windowsHide: true,
  })
  child.unref()
  return { state, pid: child.pid }
}

export function readLoginStatus(cfg, slug, site) {
  const state = loginStateDir(cfg, slug, site)
  try {
    return JSON.parse(readFileSync(join(state, 'status.json'), 'utf8'))
  } catch {
    return { state: 'none' }
  }
}

export function readLoginQr(cfg, slug, site) {
  const file = join(loginStateDir(cfg, slug, site), 'qr.png')
  if (!existsSync(file)) return null
  try { return readFileSync(file) } catch { return null }
}
