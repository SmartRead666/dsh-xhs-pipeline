// 小红书内容流水线 · 浏览器半边
// 两个入口，职责不同：
//   1) 左侧图标「小红书内容流水线」= 主面板（全屏工作台），点开时中间区域显示看板
//   2) 右侧栏标签「小红书」= 和对话并排的辅助面板，可从右侧栏 + / 指南里打开
window.__ModuleLoader__.load({
  id: 'dsh-xhs-pipeline',
  factory: (require) => {
    var module = { exports: {} }
    var exports = module.exports
    Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' })

    const React = require('react')
    const h = React.createElement
    const PANEL = 'xhs-pipeline'
    const LABEL = '小红书内容流水线'
    const TAB_LABEL = '小红书'
    const SRC = '/xhs-pipeline/'

    function XhsIcon(props) {
      const s = (props && props.size) || 18
      return h('svg', {
        width: s, height: s, viewBox: '0 0 24 24', fill: 'none',
        stroke: 'currentColor', strokeWidth: 1.5, strokeLinecap: 'round', strokeLinejoin: 'round',
      },
        h('rect', { x: 3, y: 4, width: 13, height: 16, rx: 2 }),
        h('path', { d: 'M6.5 8.5h6M6.5 12h6M6.5 15.5h4' }),
        h('path', { d: 'M19.5 8.5l2 2L17 15l-2.4.4.4-2.4 4.5-4.5z' }))
    }

    function Panel() {
      return h('iframe', {
        src: SRC,
        title: LABEL,
        allow: 'fullscreen',
        style: { width: '100%', height: '100%', border: 0, display: 'block', background: '#0f1116' },
      })
    }

    function apply(ctx) {
      // 打开右侧栏浏览器到这个网址（不同版本 API 形状不同，逐个试探）
      function openInRight(url) {
        let sr = null
        try { sr = ctx.get('sidebarRight') } catch {}
        if (sr && typeof sr.openResource === 'function') {
          const tries = [
            [{ kind: 'url', url }, { title: '小红书' }],
            [{ kind: 'link', url }, { title: '小红书' }],
            [{ url }, { title: '小红书' }],
            [{ kind: 'url', url }, undefined],
          ]
          for (const [res, opt] of tries) {
            try { sr.openResource(res, opt); return true } catch (err) {}
          }
        }
        return false
      }
      try {
        addEventListener('message', (e) => {
          if (e.origin !== location.origin) return
          const m = e.data
          if (!m || m.type !== 'xhs:open-url' || typeof m.url !== 'string') return
          const ok = openInRight(m.url)
          try { e.source && e.source.postMessage({ type: 'xhs:open-url-result', ok, url: m.url }, location.origin) } catch {}
        })
      } catch (err) {
        console.error('[xhs-pipeline] 监听 open-url 失败', err)
      }

      // 主面板：左侧图标点开后在中间全屏显示
      ctx.slots.inject('sidebar.panellist', () =>
        ctx.slots.register({ name: 'sidebar.panellist', id: PANEL, order: 7, label: () => LABEL }, XhsIcon))
      ctx.slots.inject('main', () => ctx.slots.register({ name: 'main', key: PANEL }, Panel))

      // 右侧栏标签：和对话并排
      try {
        ctx.inject(['sidebarRightTabs'], (c) => {
          const reg = c.sidebarRightTabs
          if (!reg || typeof reg.register !== 'function') return
          const d1 = reg.register({
            id: PANEL,
            kind: PANEL,
            title: () => TAB_LABEL,
            guide: [{
              id: PANEL,
              order: 7,
              title: () => LABEL,
              description: () => '出图 / 定时发布 / 互动监测',
              icon: XhsIcon,
            }],
          })
          const d2 = c.slots.inject('sidebar.right.pane.tab', () =>
            c.slots.register({ name: 'sidebar.right.pane.tab', key: PANEL }, () => h(Panel)))
          const d3 = c.slots.inject('sidebar.right.pane.tab.title', () =>
            c.slots.register({ name: 'sidebar.right.pane.tab.title', key: PANEL }, () => h('span', null, TAB_LABEL)))
          ctx.effect(() => () => { [d1, d2, d3].forEach((x) => { try { x && x() } catch {} }) })
        })
      } catch (err) {
        console.error('[xhs-pipeline] 注册右侧栏失败', err)
      }
    }

    exports.isPlugin = true
    exports.inject = ['slots']
    exports.apply = apply
    return module.exports
  },
})
