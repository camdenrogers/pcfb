import React, { useState } from "react";

function App() {
  const [homeElo, setHomeElo] = useState("");
  const [awayElo, setAwayElo] = useState("");
  const [spread, setSpread] = useState(null);

  const handlePredict = async () => {
    const response = await fetch("http://localhost:8000/predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        homePregameElo: parseFloat(homeElo),
        awayPregameElo: parseFloat(awayElo)
      })
    });

    const data = await response.json();
    setSpread(data.predicted_spread);
  };

  return (
    <div style={{ padding: "2rem" }}>
      <h2>College Football Spread Predictor</h2>
      <input
        type="number"
        placeholder="Home Elo"
        value={homeElo}
        onChange={(e) => setHomeElo(e.target.value)}
      />
      <br />
      <input
        type="number"
        placeholder="Away Elo"
        value={awayElo}
        onChange={(e) => setAwayElo(e.target.value)}
      />
      <br />
      <button onClick={handlePredict}>Predict Spread</button>
      {spread !== null && (
        <p>🏈 Predicted Spread: {spread.toFixed(2)} points</p>
      )}
    </div>
  );
}

export default App;
