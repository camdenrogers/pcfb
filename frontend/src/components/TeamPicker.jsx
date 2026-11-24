import { useEffect, useMemo, useRef, useState } from 'react'
import TeamLogo from './TeamLogo.jsx'
import { signed, teamColor } from '../format.js'

export default function TeamPicker({ label, teams, value, onChange, excludeId }) {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [highlight, setHighlight] = useState(0)
  const wrapRef = useRef(null)
  const inputRef = useRef(null)
  const listRef = useRef(null)

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return teams.filter(
      (t) =>
        t.id !== excludeId &&
        (!q ||
          t.school.toLowerCase().includes(q) ||
          (t.abbreviation || '').toLowerCase().includes(q) ||
          (t.mascot || '').toLowerCase().includes(q) ||
          (t.conference || '').toLowerCase().includes(q)),
    )
  }, [teams, query, excludeId])

  useEffect(() => setHighlight(0), [query])

  useEffect(() => {
    const onDoc = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [])

  useEffect(() => {
    const el = listRef.current?.children[highlight]
    el?.scrollIntoView({ block: 'nearest' })
  }, [highlight])

  function select(team) {
    onChange(team)
    setQuery('')
    setOpen(false)
    inputRef.current?.blur()
  }

  function onKeyDown(e) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setOpen(true)
      setHighlight((h) => Math.min(h + 1, filtered.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setHighlight((h) => Math.max(h - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (open && filtered[highlight]) select(filtered[highlight])
    } else if (e.key === 'Escape') {
      setOpen(false)
    }
  }

  return (
    <div className="picker" ref={wrapRef} style={{ '--team': teamColor(value) }}>
      <div className="picker-label">{label}</div>

      <div className={`picker-card ${value ? 'selected' : ''}`} onClick={() => inputRef.current?.focus()}>
        <TeamLogo team={value} size={56} />
        <div className="picker-card-text">
          {value ? (
            <>
              <div className="picker-school">{value.school}</div>
              <div className="picker-meta">
                {value.mascot} · {value.conference} · #{value.rank} ({signed(value.rating)})
              </div>
            </>
          ) : (
            <div className="picker-placeholder">Choose a team</div>
          )}
        </div>
      </div>

      <input
        ref={inputRef}
        className="picker-input"
        type="text"
        placeholder={value ? 'Search to change team…' : 'Search team, mascot, or conference…'}
        value={query}
        onChange={(e) => {
          setQuery(e.target.value)
          setOpen(true)
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKeyDown}
        role="combobox"
        aria-expanded={open}
        aria-label={label}
      />

      {open && (
        <ul className="picker-list" ref={listRef} role="listbox">
          {filtered.length === 0 && <li className="picker-empty">No matching FBS teams</li>}
          {filtered.map((t, i) => (
            <li
              key={t.id}
              role="option"
              aria-selected={i === highlight}
              className={`picker-option ${i === highlight ? 'active' : ''}`}
              onMouseEnter={() => setHighlight(i)}
              onMouseDown={(e) => {
                e.preventDefault()
                select(t)
              }}
            >
              <TeamLogo team={t} size={24} />
              <span className="opt-school">{t.school}</span>
              <span className="opt-conf">{t.conference}</span>
              <span className="opt-rank">#{t.rank}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
