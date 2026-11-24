import { useState } from 'react'
import { teamColor } from '../format.js'

export default function TeamLogo({ team, size = 32 }) {
  const [broken, setBroken] = useState(false)
  if (!team) return <span className="logo-fallback" style={{ width: size, height: size }} />
  if (team.logo && !broken) {
    return (
      <img
        className="team-logo"
        src={team.logo}
        alt=""
        width={size}
        height={size}
        loading="lazy"
        onError={() => setBroken(true)}
      />
    )
  }
  return (
    <span
      className="logo-fallback"
      style={{ width: size, height: size, background: teamColor(team), fontSize: size * 0.32 }}
    >
      {(team.abbreviation || team.school).slice(0, 4)}
    </span>
  )
}
