// 更新检查：比对当前插件版本与远端最新版本
// 支持三种来源（在 ~/.dsh/xhs-pipeline.json 的 update 里配置）：
//   { "update": { "npm": "dsh-xhs-pipeline" } }            从 npm registry 查 latest
//   { "update": { "url": "https://.../version.json" } }    从任意 HTTP 地址查 { version, url }
//   { "update": { "file": "D:/.../version.json" } }        本地文件（内网/离线分发用）
//   { "update": { "enabled": false } }                     关闭
import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import { homedir } from 'node:os'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { configPath } from './runner.js'

const ROOT = fileURLToPath(new URL('..', import.meta.url))
const CURRENT = (() => {
  try { return JSON.parse(readFileSync(join(ROOT, 'package.json'), 'utf8')).version } catch { return '0.0.0' }
})()

const CACHE_TTL = 12 * 3600 * 1000  // 12 小时最多查一次，避免拖慢启动

function cachePath() {
  return join(dirname(configPath()), 'xhs-pipeline-update.json')
}

function cmp(a, b) {
  const pa = String(a).replace(/^v/, '').split(/[.-]/).map((x) => parseInt(x, 10) || 0)
  const pb = String(b).replace(/^v/, '').split(/[.-]/).map((x) => parseInt(x, 10) || 0)
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const d = (pa[i] || 0) - (pb[i] || 0)
    if (d) return d > 0 ? 1 : -1
  }
  return 0
}

function readCache() {
  try { return JSON.parse(readFileSync(cachePath(), 'utf8')) } catch { return null }
}

function writeCache(data) {
  try { writeFileSync(cachePath(), JSON.stringify(data)) } catch {}
}

async function fetchJson(url, timeout = 8000) {
  const ctrl = new AbortController()
  const t = setTimeout(() => ctrl.abort(), timeout)
  try {
    const r = await fetch(url, { signal: ctrl.signal, headers: { accept: 'application/json' } })
    if (!r.ok) return null
    return await r.json()
  } catch {
    return null
  } finally {
    clearTimeout(t)
  }
}

/** 返回 { current, latest, available, url, checkedAt, error } */
export async function checkUpdate(cfg, { force = false } = {}) {
  const conf = (cfg && cfg.update) || {}
  if (conf.enabled === false) return { current: CURRENT, latest: null, available: false, disabled: true }

  const cache = readCache()
  if (!force && cache && cache.current === CURRENT && Date.now() - (cache.checkedAt || 0) < CACHE_TTL) {
    return cache
  }

  let latest = null
  let url = ''
  let error = ''
  try {
    if (conf.file) {
      const p = conf.file.replace(/^~/, homedir())
      if (existsSync(p)) {
        const d = JSON.parse(readFileSync(p, 'utf8'))
        latest = d.version || d.latest || null
        url = d.url || ''
      } else error = '找不到版本文件'
    } else if (conf.url) {
      const d = await fetchJson(conf.url)
      if (d) { latest = d.version || d.latest || null; url = d.url || '' } else error = '请求失败'
    } else {
      const name = conf.npm || 'dsh-xhs-pipeline'
      const d = await fetchJson('https://registry.npmjs.org/' + encodeURIComponent(name) + '/latest')
      if (d) { latest = d.version; url = (d.homepage || '') + (d.homepage ? '' : '') } else error = 'registry 无此包或网络不可用'
    }
  } catch (e) {
    error = e.message
  }

  const result = {
    current: CURRENT,
    latest: latest || null,
    available: !!(latest && cmp(latest, CURRENT) > 0),
    url: url || '',
    checkedAt: Date.now(),
    error,
  }
  writeCache(result)
  return result
}
