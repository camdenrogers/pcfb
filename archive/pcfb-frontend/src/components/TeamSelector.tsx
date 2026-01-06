import React, { useState } from "react";

function TeamSelector() {
  const teams = [
    { id: 1, name: "Georgia Bulldogs" },
    { id: 2, name: "Alabama Crimson Tide" },
    { id: 3, name: "Michigan Wolverines" },
    { id: 4, name: "Michigan State Spartanss" },
    { id: 5, name: "Georgia Tech Yellow Jackets" },
  ];

  const [selectedValue, setSelectedValue] = useState<string>("");

  function handleChange(event: React.ChangeEvent<HTMLSelectElement>) {
    setSelectedValue(event.target.value);
  }

  const [homeTeamId, setHomeTeamId] = useState<number | "">("");
  const [awayTeamId, setAwayTeamId] = useState<number | "">("");

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const homeTeam = teams.find((t) => t.id === homeTeamId);
    const awayTeam = teams.find((t) => t.id === awayTeamId);

    if (!homeTeam || !awayTeam) {
      alert("Please select both teams.");
      return;
    }

    console.log("Home Team ID:", homeTeam.id);
    console.log("Away Team ID:", awayTeam.id);
  }

  return (
    <form onSubmit={handleSubmit} style={{ padding: "1rem" }}>
      <div style={{ marginBottom: "1rem" }}>
        <label htmlFor="home-team">Home Team:</label>
        <select
          id="home-team"
          value={homeTeamId}
          onChange={(e) => setHomeTeamId(Number(e.target.value))}
        >
          <option value="">-- Select Home Team --</option>
          {teams.map((team) => (
            <option key={team.id} value={team.id}>
              {team.name}
            </option>
          ))}
        </select>
      </div>

      <div style={{ marginBottom: "1rem" }}>
        <label htmlFor="away-team">Away Team:</label>
        <select
          id="away-team"
          value={awayTeamId}
          onChange={(e) => setAwayTeamId(Number(e.target.value))}
        >
          <option value="">-- Select Away Team --</option>
          {teams.map((team) => (
            <option key={team.id} value={team.id}>
              {team.name}
            </option>
          ))}
        </select>
      </div>

      <button type="submit">Submit</button>
    </form>

    // <div style={{ padding: "1rem" }}>
    //   <label htmlFor="dropdown">Home Team</label>
    //   <select id="dropdown" value={selectedValue} onChange={handleChange}>
    //     {teams.map((team) => (
    //       <option key={team} value={team}>
    //         {team}
    //       </option>
    //     ))}
    //   </select>
    //   {selectedValue && <p>You selected: {selectedValue}</p>}
    // </div>
  );
}

export default TeamSelector;
