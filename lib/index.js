// 小红书内容流水线 · Host 半边
// 1) 把插件自带的 skills/xiaohongshu-pipeline 注册进 ctx.skills
// 2) 注册 3 个模型工具：出图 / 排期 / 监测
// 3) /xhs-pipeline/ 小面板：选账号 → 出图 → 排期 → 监测（浏览器里点）
import { existsSync, readdirSync, readFileSync } from 'node:fs'
import { homedir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createSkillProvider, readSkills } from './skills.js'
import { TOOLS } from './tools.js'
import { loadConfig, listDays, runScript } from './runner.js'
import { checkUpdate } from './update.js'
import { startQrLogin, readLoginStatus, readLoginQr } from './login.js'

const ROOT = fileURLToPath(new URL('..', import.meta.url))
const BASE = '/xhs-pipeline'
const SKILL_DIRS = [join(ROOT, 'skills')]
const PUBLIC = join(ROOT, 'public')

const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.svg': 'image/svg+xml',
}

export const name = 'xhs-pipeline'
export const inject = ['webServer', 'skills', 'tools']

function sendJson(res, status, body) {
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' })
  res.end(JSON.stringify(body))
}

function readJson(req, max = 32 * 1024) {
  return new Promise((resolve, reject) => {
    if (req.method !== 'POST') return reject(Object.assign(new Error('method'), { status: 405 }))
    let size = 0
    const chunks = []
    req.on('data', (c) => { size += c.length; if (size > max) req.destroy(); else chunks.push(c) })
    req.on('end', () => { try { resolve(JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}')) } catch (e) { reject(Object.assign(e, { status: 400 })) } })
    req.on('error', reject)
  })
}

export function apply(ctx) {
  // 1. skill
  ctx.effect(() => ctx.skills.registerProvider(() => createSkillProvider(SKILL_DIRS, ROOT)))

  // 2. 工具
  for (const tool of TOOLS) ctx.tools.register(tool)

  // 3. 面板 + API
  ctx.effect(() =>
    ctx.webServer.register({
      kind: 'prefix',
      path: BASE,
      async handler(req, res) {
        const url = new URL(req.url || '/', 'http://x')
        const rest = decodeURIComponent(url.pathname.slice(BASE.length)) || '/'

        if (rest === '/api/state') {
          try {
            const cfg = loadConfig()
            let update = null
            try { update = await checkUpdate(cfg) } catch {}
            return sendJson(res, 200, {
              ok: true,
              home: cfg.home,
              python: cfg.python,
              accounts: cfg.accounts,
              days: listDays(cfg),
              update,
              skillInstalled: readSkills(SKILL_DIRS).length > 0,
            })
          } catch (e) {
            return sendJson(res, 200, { ok: false, error: e.message, hint: '先运行 scripts/setup.py 或写 ~/.dsh/xhs-pipeline.json' })
          }
        }

        if (rest === '/api/content') {
          try {
            const cfg = loadConfig()
            const dir = join(cfg.home, 'content')
            const items = []
            if (existsSync(dir)) {
              for (const name of readdirSync(dir)) {
                if (!name.endsWith('.json')) continue
                try {
                  const j = JSON.parse(readFileSync(join(dir, name), 'utf8'))
                  items.push({
                    file: name,
                    day: j.no,
                    date: j.date,
                    title: (j.post && j.post.title) || j.h1 || name,
                    style: j.style || '',
                  })
                } catch {}
              }
            }
            items.sort((a, b) => String(a.date).localeCompare(String(b.date)))
            return sendJson(res, 200, { ok: true, items })
          } catch (e) {
            return sendJson(res, 500, { ok: false, error: e.message })
          }
        }

        if (rest === '/api/sync') {
          try {
            const body = await readJson(req)
            const cfg = loadConfig()
            const out = await runScript(cfg, 'sync_status.py', ['--account', String(body.account || '')], 300_000)
            return sendJson(res, 200, { ok: out.code === 0, code: out.code, output: out.output })
          } catch (e) {
            return sendJson(res, 500, { ok: false, error: e.message })
          }
        }

        if (rest === '/api/reschedule') {
          try {
            const body = await readJson(req)
            const cfg = loadConfig()
            const args = ['--account', String(body.account || ''), '--title', String(body.title || '')]
            if (body.now) args.push('--now')
            else args.push('--time', String(body.time || ''))
            const out = await runScript(cfg, 'reschedule.py', args, 900_000)
            return sendJson(res, 200, { ok: out.code === 0, code: out.code, output: out.output })
          } catch (e) {
            return sendJson(res, 500, { ok: false, error: e.message })
          }
        }

        if (rest === '/api/login-start') {
          try {
            const body = await readJson(req)
            const cfg = loadConfig()
            const r = startQrLogin(cfg, String(body.account || ''), body.main ? 'main' : 'creator')
            return sendJson(res, 200, { ok: true, pid: r.pid, state: r.state })
          } catch (e) {
            return sendJson(res, 500, { ok: false, error: e.message })
          }
        }

        if (rest === '/api/login-qr' || rest === '/api/login-status') {
          try {
            const cfg = loadConfig()
            const slug = String(url.searchParams.get('account') || '')
            const site = url.searchParams.get('main') === '1' ? 'main' : 'creator'
            if (rest === '/api/login-status') {
              return sendJson(res, 200, { ok: true, ...readLoginStatus(cfg, slug, site) })
            }
            const buf = readLoginQr(cfg, slug, site)
            if (!buf) { res.writeHead(404); return res.end('no qr yet') }
            res.writeHead(200, { 'content-type': 'image/png', 'cache-control': 'no-store' })
            return res.end(buf)
          } catch (e) {
            return sendJson(res, 500, { ok: false, error: e.message })
          }
        }

        if (rest === '/api/update-check') {
          try {
            const cfg = loadConfig()
            const u = await checkUpdate(cfg, { force: true })
            return sendJson(res, 200, { ok: true, ...u })
          } catch (e) {
            return sendJson(res, 500, { ok: false, error: e.message })
          }
        }

        if (rest === '/api/render' || rest === '/api/publish' || rest === '/api/monitor' || rest === '/api/login') {
          try {
            const body = await readJson(req)
            const cfg = loadConfig()
            let out
            if (rest === '/api/render') {
              out = await runScript(cfg, 'render.py', ['--account', body.account, '--day', body.day])
            } else if (rest === '/api/publish') {
              const args = ['--account', body.account, '--day', body.dayDir]
              if (body.draft) args.push('--draft'); else args.push('--time', body.time)
              out = await runScript(cfg, 'publish.py', args, 900_000)
            } else if (rest === '/api/monitor') {
              out = await runScript(cfg, 'monitor.py', ['--account', body.account], 300_000)
            } else {
              const args = ['--account', body.account]
              if (body.main) args.push('--main')
              out = await runScript(cfg, 'login.py', args, 900_000)
            }
            return sendJson(res, 200, { ok: out.code === 0, code: out.code, output: out.output })
          } catch (e) {
            return sendJson(res, 500, { ok: false, error: e.message })
          }
        }

        if (req.method !== 'GET' && req.method !== 'HEAD') return sendJson(res, 404, { ok: false })
        const rel = rest === '/' ? 'index.html' : rest.replace(/^\/+/, '')
        const file = join(PUBLIC, rel)
        if (!file.startsWith(PUBLIC) || !existsSync(file)) {
          res.writeHead(404); return res.end('not found')
        }
        const type = MIME[file.slice(file.lastIndexOf('.'))] || 'application/octet-stream'
        res.writeHead(200, { 'content-type': type, 'cache-control': 'no-cache' })
        return res.end(readFileSync(file))
      },
    }),
  )
}
