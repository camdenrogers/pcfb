import TeamLogo from './TeamLogo.jsx'
import { signed } from '../format.js'

export default function Rankings({ teams, onPick, limit = 25 }) {
  const top = [...teams].sort((x, y) => x.rank - y.rank).slice(0, limit)
  return (
    <section className="rankings">
      <h2>Power ratings · Top {limit}</h2>
      <p className="muted">Net rating = expected margin vs. an average FBS team on a neutral field. Click a team to add it to the matchup.</p>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Team</th>
            <th className="num">Rating</th>
            <th className="num">Off</th>
            <th className="num">Def</th>
          </tr>
        </thead>
        <tbody>
          {top.map((t) => (
            <tr key={t.id} onClick={() => onPick(t)} className="clickable">
              <td>{t.rank}</td>
              <td>
                <div className="rk-team">
                  <TeamLogo team={t} size={20} />
                  <span>{t.school}</span>
                  <span className="muted small">{t.conference}</span>
                </div>
              </td>
              <td className="num strong">{signed(t.rating)}</td>
              <td className="num">{signed(t.offense)}</td>
              <td className="num">{signed(t.defense)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
