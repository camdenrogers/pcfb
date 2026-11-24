export const signed = (x, digits = 1) => {
  if (x === null || x === undefined || Number.isNaN(x)) return '—'
  const v = Number(x).toFixed(digits)
  return x > 0 ? `+${v}` : v
}

export const pct = (x) => `${Math.round(x * 100)}%`

export const line = (x) => (x === 0 ? 'PK' : x > 0 ? `+${x}` : `${x}`)

const normHex = (c) => (c && /^#?[0-9a-f]{6}$/i.test(c) ? (c.startsWith('#') ? c : `#${c}`) : null)

export const teamColor = (team, fallback = '#475569') => normHex(team?.color) || fallback

const rgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16))
const dist = (x, y) => Math.hypot(...rgb(x).map((v, i) => v - rgb(y)[i]))
const luminance = (hex) => rgb(hex).reduce((s, v, i) => s + v * [0.2126, 0.7152, 0.0722][i], 0) / 255

// Two colors that are distinguishable side by side (e.g. Georgia red vs Ohio State red).
export function distinctColors(a, b) {
  const ca = teamColor(a, '#334155')
  const cb = teamColor(b, '#94a3b8')
  if (dist(ca, cb) >= 110) return [ca, cb]
  const alt = normHex(b?.alt_color)
  if (alt && dist(ca, alt) >= 110 && luminance(alt) > 0.2) return [ca, alt]
  return [ca, dist(ca, '#94a3b8') >= 110 ? '#94a3b8' : '#e2e8f0']
}
