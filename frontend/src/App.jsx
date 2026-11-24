import { useCallback, useEffect, useState } from 'react'
import { fetchModel, fetchPrediction, fetchTeams } from './api.js'
import TeamPicker from './components/TeamPicker.jsx'
import PredictionCard from './components/PredictionCard.jsx'
import Rankings from './components/Rankings.jsx'

export default function App() {
  const [status, setStatus] = useState('loading') // loading | ready | not_ready | error
  const [model, setModel] = useState(null)
  const [teams, setTeams] = useState([])
  const [teamA, setTeamA] = useState(null)
  const [teamB, setTeamB] = useState(null)
  const [prediction, setPrediction] = useState(null)
  const [predicting, setPredicting] = useState(false)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    try {
      const m = await fetchModel()
      setModel(m)
      if (!m.ready) {
        setStatus('not_ready')
        return
      }
      setTeams(await fetchTeams())
      setStatus('ready')
      setError(null)
    } catch (e) {
      setError(e.message)
      setStatus('error')
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  // While the backend is bootstrapping (first ingest + train), poll until it's ready.
  useEffect(() => {
    if (status !== 'not_ready' && status !== 'error') return
    const id = setInterval(load, 10000)
    return () => clearInterval(id)
  }, [status, load])

  useEffect(() => {
    if (!teamA || !teamB || teamA.id === teamB.id) {
      setPrediction(null)
      return
    }
    let cancelled = false
    setPredicting(true)
    setError(null)
    fetchPrediction(teamA.id, teamB.id)
      .then((p) => !cancelled && setPrediction(p))
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setPredicting(false))
    return () => {
      cancelled = true
    }
  }, [teamA, teamB])

  function swap() {
    setTeamA(teamB)
    setTeamB(teamA)
  }

  function pickFromRankings(team) {
    if (team.id === teamA?.id || team.id === teamB?.id) return
    if (!teamA) setTeamA(team)
    else if (!teamB) setTeamB(team)
    else setTeamB(team)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const bt = model?.metrics?.backtest

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">PCFB</span>
          <span className="brand-sub">College Football Spread Model</span>
        </div>
        {model?.ready && (
          <div className="model-chip" title={`Model run #${model.run_id}`}>
            {model.season} season · through {model.through}
          </div>
        )}
      </header>

      <main>
        {status === 'loading' && <div className="notice">Loading model…</div>}

        {status === 'not_ready' && (
          <div className="notice">
            <strong>{model?.refreshing ? 'Building the model…' : 'No model trained yet.'}</strong>
            <p>
              {model?.refreshing
                ? 'Pulling games from CollegeFootballData.com and fitting ratings. This page refreshes automatically.'
                : 'Set CFBD_API_KEY and run `python -m app.cli refresh` in the backend (see README).'}
            </p>
          </div>
        )}

        {status === 'error' && (
          <div className="notice error">
            <strong>Can't reach the API.</strong>
            <p>{error}</p>
          </div>
        )}

        {status === 'ready' && (
          <>
            <section className="matchup">
              <h1>If they played today…</h1>
              <p className="muted">Pick any two FBS teams to get a predicted point spread on a neutral field.</p>
              <div className="pickers">
                <TeamPicker label="Team A" teams={teams} value={teamA} onChange={setTeamA} excludeId={teamB?.id} />
                <button className="swap" onClick={swap} disabled={!teamA && !teamB} title="Swap teams" aria-label="Swap teams">
                  ⇄
                </button>
                <TeamPicker label="Team B" teams={teams} value={teamB} onChange={setTeamB} excludeId={teamA?.id} />
              </div>
            </section>

            {error && <div className="notice error">{error}</div>}
            {predicting && !prediction && <div className="notice">Crunching numbers…</div>}
            {prediction && <PredictionCard prediction={prediction} />}
            {!prediction && !predicting && (
              <div className="notice subtle">Select two teams to generate a spread.</div>
            )}

            <Rankings teams={teams} onPick={pickFromRankings} />
          </>
        )}
      </main>

      <footer className="footer">
        {model?.ready && (
          <div>
            Home-field advantage {model.home_field_advantage} pts · avg team scores {model.league_avg_points} ·
            margin σ {model.sigma}
            {bt?.n > 0 && (
              <>
                {' '}
                · Walk-forward backtest ({model.metrics.backtest_seasons.join(', ')}): MAE {bt.mae.toFixed(2)}, straight-up{' '}
                {(bt.winner_accuracy * 100).toFixed(1)}% over {bt.n} games
              </>
            )}
          </div>
        )}
        <div className="muted">
          Data: <a href="https://collegefootballdata.com" target="_blank" rel="noreferrer">CollegeFootballData.com</a>.
          For entertainment purposes.
        </div>
      </footer>
    </div>
  )
}
