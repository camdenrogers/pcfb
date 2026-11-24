const BASE = import.meta.env.VITE_API_BASE || ''

async function getJSON(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      if (body?.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      /* not JSON */
    }
    throw new Error(detail)
  }
  return res.json()
}

export const fetchModel = () => getJSON('/api/model')
export const fetchTeams = () => getJSON('/api/teams')
export const fetchPrediction = (a, b) =>
  getJSON(`/api/predict?team_a=${encodeURIComponent(a)}&team_b=${encodeURIComponent(b)}`)
