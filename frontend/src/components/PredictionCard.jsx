import TeamLogo from './TeamLogo.jsx'
import { distinctColors, line, pct, signed } from '../format.js'

function Row({ label, a, b, fmt = signed, higherIsBetter = true }) {
  const aBetter = higherIsBetter ? a > b : a < b
  const bBetter = higherIsBetter ? b > a : b < a
  return (
    <tr>
      <td className={aBetter ? 'better' : ''}>{fmt(a)}</td>
      <th>{label}</th>
      <td className={bBetter ? 'better' : ''}>{fmt(b)}</td>
    </tr>
  )
}

export default function PredictionCard({ prediction }) {
  const { team_a: a, team_b: b, spread, total } = prediction
  const [aColor, bColor] = distinctColors(a, b)
  const lineA = spread.team_a_line
  const lineB = lineA === 0 ? 0 : -lineA

  return (
    <section className="prediction">
      <div className="headline">
        <div className="headline-label">Predicted spread · neutral site</div>
        <div className="headline-spread">{spread.display}</div>
        <div className="headline-sub">
          Model margin {signed(prediction.margin)} for {a.school} · Total {total.toFixed(1)}
        </div>
      </div>

      <div className="scoreboard">
        <div className="score-team">
          <TeamLogo team={a} size={72} />
          <div className="score-school">{a.school}</div>
          <div className="score-line">{line(lineA)}</div>
          <div className="score-points" style={{ color: aColor }}>
            {a.projected_points.toFixed(1)}
          </div>
        </div>
        <div className="score-vs">vs</div>
        <div className="score-team">
          <TeamLogo team={b} size={72} />
          <div className="score-school">{b.school}</div>
          <div className="score-line">{line(lineB)}</div>
          <div className="score-points" style={{ color: bColor }}>
            {b.projected_points.toFixed(1)}
          </div>
        </div>
      </div>

      <div className="winprob">
        <div className="winprob-labels">
          <span>
            {a.abbreviation || a.school} {pct(a.win_probability)}
          </span>
          <span>Win probability</span>
          <span>
            {pct(b.win_probability)} {b.abbreviation || b.school}
          </span>
        </div>
        <div className="winprob-bar">
          <div style={{ width: `${a.win_probability * 100}%`, background: aColor }} />
          <div style={{ width: `${b.win_probability * 100}%`, background: bColor }} />
        </div>
      </div>

      <table className="compare">
        <thead>
          <tr>
            <th>{a.school}</th>
            <th />
            <th>{b.school}</th>
          </tr>
        </thead>
        <tbody>
          <Row label="Power rank" a={a.rank} b={b.rank} fmt={(x) => `#${x}`} higherIsBetter={false} />
          <Row label="Net rating" a={a.rating} b={b.rating} />
          <Row label="Offense (pts vs avg)" a={a.offense} b={b.offense} />
          <Row label="Defense (pts saved vs avg)" a={a.defense} b={b.defense} />
          <Row label="Games this season" a={a.games_played} b={b.games_played} fmt={(x) => x} />
        </tbody>
      </table>
    </section>
  )
}
