"use client";

import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ChevronsUpDown, Check, Shuffle } from "lucide-react";
import { cn } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Team = {
  team: string;
  conference: string | null;
  spRating: number | null;
  spOffense: number | null;
  spDefense: number | null;
  elo: number | null;
};

type Game = {
  homeTeam: string;
  awayTeam: string;
  startDate: string | null;
  neutralSite: boolean;
  homeConference: string | null;
  awayConference: string | null;
  homeSPRating: number | null;
  awaySPRating: number | null;
  homePregameElo: number | null;
  awayPregameElo: number | null;
  vegasSpread: number | null;
  modelSpread: number | null;
  predictedCover: boolean | null;
  confidence: number | null;
};

type WeekData = {
  games: Game[];
  week: number | null;
  season: number | null;
  offseason: boolean;
};

type PredictionResult = {
  homeTeam: string;
  awayTeam: string;
  spread: number;
  modelSpread: number | null;
  predictedCover: boolean;
  confidence: number;
};

function TeamCombobox({
  teams,
  value,
  onChange,
  placeholder,
}: {
  teams: Team[];
  value: string;
  onChange: (val: string) => void;
  placeholder: string;
}) {
  const [open, setOpen] = useState(false);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between"
        >
          {value || placeholder}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-full p-0">
        <Command>
          <CommandInput placeholder="Search teams..." />
          <CommandList>
            <CommandEmpty>No team found.</CommandEmpty>
            <CommandGroup>
              {teams.map((t) => (
                <CommandItem
                  key={t.team}
                  value={t.team}
                  onSelect={(val) => {
                    onChange(val === value ? "" : val);
                    setOpen(false);
                  }}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      value === t.team ? "opacity-100" : "opacity-0",
                    )}
                  />
                  <span>{t.team}</span>
                  {t.conference && (
                    <span className="ml-auto text-xs text-muted-foreground">
                      {t.conference}
                    </span>
                  )}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

function formatGameDate(dateStr: string | null) {
  if (!dateStr) return "TBD";
  return new Date(dateStr).toLocaleDateString("en-US", {
    timeZone: "America/New_York",
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function shortName(team: string) {
  return team.split(" ").pop() ?? team;
}

function formatSpread(
  spread: number | null,
  homeTeam: string,
  awayTeam: string,
) {
  if (spread === null) return <span className="text-muted-foreground">—</span>;
  if (spread === 0) return <span>PK</span>;
  if (spread < 0)
    return (
      <span>
        {shortName(homeTeam)} {spread.toFixed(1)}
      </span>
    );
  return (
    <span>
      {shortName(awayTeam)} -{spread.toFixed(1)}
    </span>
  );
}

export default function PredictionsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [weekData, setWeekData] = useState<WeekData | null>(null);
  const [homeTeam, setHomeTeam] = useState("");
  const [awayTeam, setAwayTeam] = useState("");
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/teams`)
      .then((r) => r.json())
      .then(setTeams)
      .catch(() => setError("Could not load teams"));

    fetch(`${API_BASE}/api/predictions/week`)
      .then((r) => r.json())
      .then(setWeekData)
      .catch(() => console.error("Could not load week predictions"));
  }, []);

  function handleRandom() {
    const eligible = teams.filter((t) => t.spRating !== null && t.elo !== null);
    const shuffled = [...eligible].sort(() => Math.random() - 0.5);
    setHomeTeam(shuffled[0]?.team ?? "");
    setAwayTeam(shuffled[1]?.team ?? "");
    setResult(null);
  }

  async function handlePredict() {
    if (!homeTeam || !awayTeam) return;
    if (homeTeam === awayTeam) {
      setError("Please select two different teams");
      return;
    }

    const home = teams.find((t) => t.team === homeTeam);
    const away = teams.find((t) => t.team === awayTeam);

    if (!home || !away) return;
    if (!home.spRating || !away.spRating || !home.elo || !away.elo) {
      setError("One or both teams are missing rating data");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/api/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          homeTeam: home.team,
          awayTeam: away.team,
          spread: away.spRating - home.spRating,
          overUnder: 54,
          homeSPRating: home.spRating,
          awaySPRating: away.spRating,
          homeSPOffense: home.spOffense ?? 0,
          awaySPOffense: away.spOffense ?? 0,
          homeSPDefense: home.spDefense ?? 0,
          awaySPDefense: away.spDefense ?? 0,
          homePregameElo: home.elo,
          awayPregameElo: away.elo,
          isNeutral: 0,
        }),
      });

      if (!res.ok) throw new Error("Prediction failed");
      const data = await res.json();
      setResult(data);
    } catch {
      setError("Failed to generate prediction");
    } finally {
      setLoading(false);
    }
  }

  const homeData = teams.find((t) => t.team === homeTeam);
  const awayData = teams.find((t) => t.team === awayTeam);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Weekly Predictions</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Week {weekData?.week ?? "—"} · {weekData?.season ?? 2026} Season
        </p>
      </div>

      {/* Hypothetical Matchup Generator */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Hypothetical Matchup</CardTitle>
          <CardDescription>
            Select two teams to generate a predicted spread and cover
            probability
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium">Home Team</label>
              <TeamCombobox
                teams={teams}
                value={homeTeam}
                onChange={setHomeTeam}
                placeholder="Select home team..."
              />
              {homeData && (
                <p className="text-xs text-muted-foreground">
                  SP+ {homeData.spRating?.toFixed(1)} · Elo{" "}
                  {homeData.elo?.toFixed(0)}
                </p>
              )}
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium">Away Team</label>
              <TeamCombobox
                teams={teams}
                value={awayTeam}
                onChange={setAwayTeam}
                placeholder="Select away team..."
              />
              {awayData && (
                <p className="text-xs text-muted-foreground">
                  SP+ {awayData.spRating?.toFixed(1)} · Elo{" "}
                  {awayData.elo?.toFixed(0)}
                </p>
              )}
            </div>
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <div className="flex gap-2">
            <Button
              onClick={handlePredict}
              disabled={!homeTeam || !awayTeam || loading}
              className="flex-1"
            >
              {loading ? "Generating..." : "Generate Prediction"}
            </Button>
            <Button
              variant="outline"
              onClick={handleRandom}
              disabled={teams.length === 0}
            >
              <Shuffle className="h-4 w-4" />
            </Button>
          </div>

          {result && (
            <div className="rounded-lg border p-4 flex flex-col gap-3 mt-2">
              <div className="flex items-center justify-between">
                <span className="font-semibold">
                  {result.awayTeam} @ {result.homeTeam}
                </span>
                <Badge
                  variant={result.predictedCover ? "default" : "secondary"}
                >
                  {result.predictedCover ? "Home Covers" : "Away Covers"}
                </Badge>
              </div>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-xs text-muted-foreground">Model Spread</p>
                  <p className="text-lg font-semibold">
                    {result.modelSpread !== null
                      ? result.modelSpread < 0
                        ? `${shortName(result.homeTeam)} ${result.modelSpread.toFixed(1)}`
                        : `${shortName(result.awayTeam)} -${result.modelSpread.toFixed(1)}`
                      : "—"}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Confidence</p>
                  <p className="text-lg font-semibold">
                    {(result.confidence * 100).toFixed(1)}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Cover Pick</p>
                  <p className="text-lg font-semibold">
                    {result.predictedCover
                      ? shortName(result.homeTeam)
                      : shortName(result.awayTeam)}
                  </p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* This Week's Games */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">This Week's Games</CardTitle>
          <CardDescription>
            {weekData?.week
              ? `Week ${weekData.week} · ${weekData.season} Season`
              : "Loading..."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!weekData || weekData.games.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center gap-2">
              <p className="text-muted-foreground font-medium">
                No games scheduled
              </p>
              <p className="text-sm text-muted-foreground">
                The 2026 season kicks off August 29 — check back then for live
                predictions.
              </p>
            </div>
          ) : (
            <>
              <div className="hidden md:grid grid-cols-[1fr_130px_90px_90px_110px] gap-4 pb-2 mb-1 border-b text-xs text-muted-foreground font-medium">
                <span>Matchup</span>
                <span className="text-right">Date</span>
                <span className="text-right">Vegas</span>
                <span className="text-right">Model</span>
                <span className="text-right">Pick</span>
              </div>
              <div className="divide-y">
                {weekData.games.map((game, i) => (
                  <div
                    key={i}
                    className="py-3 grid grid-cols-1 md:grid-cols-[1fr_130px_90px_90px_110px] gap-2 md:gap-4 items-center"
                  >
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-sm">
                        {game.awayTeam}
                      </span>
                      <span className="text-muted-foreground text-xs">@</span>
                      <span className="font-medium text-sm">
                        {game.homeTeam}
                      </span>
                      {game.neutralSite && (
                        <Badge variant="outline" className="text-xs px-1">
                          Neutral
                        </Badge>
                      )}
                    </div>

                    <p className="text-xs text-muted-foreground text-right whitespace-nowrap">
                      {formatGameDate(game.startDate)}
                    </p>

                    <p className="text-xs text-right font-mono whitespace-nowrap">
                      {formatSpread(
                        game.vegasSpread,
                        game.homeTeam,
                        game.awayTeam,
                      )}
                    </p>

                    <p className="text-xs text-right font-mono whitespace-nowrap">
                      {formatSpread(
                        game.modelSpread,
                        game.homeTeam,
                        game.awayTeam,
                      )}
                    </p>

                    <div className="flex items-center justify-end gap-1">
                      {game.confidence !== null && (
                        <span className="text-xs text-muted-foreground">
                          {(game.confidence * 100).toFixed(0)}%
                        </span>
                      )}
                      {game.predictedCover !== null ? (
                        <Badge
                          variant={
                            game.predictedCover ? "default" : "secondary"
                          }
                          className="text-xs"
                        >
                          {game.predictedCover
                            ? shortName(game.homeTeam)
                            : shortName(game.awayTeam)}
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-xs">
                          —
                        </Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
