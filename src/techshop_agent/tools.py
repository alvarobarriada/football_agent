"""MaldinIA agent tools — """
from __future__ import annotations

import functools
import json
import unicodedata

import pandas as pd
from langfuse import get_client, observe
from pydantic import BaseModel, Field
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from strands import tool
from thefuzz import fuzz, process

from techshop_agent.config import load_stadistics, load_tfmkt_data
from techshop_agent.schemas.schemas import (
    InputLeaguePerformers,
    InputLeagueStats,
    InputSimilarPlayer,
    InputUser,
    PlayerResult,
)

# FBref only uses 4 position codes; map granular positions to their FBref equivalents
POSITION_MAP: dict[str, str] = {
    "FB": "DF", "LB": "DF", "RB": "DF", "CB": "DF",
    "DM": "MF", "CM": "MF", "LM": "MF", "RM": "MF", "WM": "MF",
    "LW": "FW", "RW": "FW", "AM": "MF",
}

client = get_client()


def match_names(name_to_find, list_of_names, threshold=60):
    """Encuentra el nombre más parecido en una lista si supera el umbral."""
    if pd.isna(name_to_find):
        return None
    match, score = process.extractOne(name_to_find, list_of_names)
    if score >= threshold:
        return match
    return None

@observe(name="clean_currency_value")
def clean_currency_value(value):
    if pd.isna(value) or value == "-":
        return 0
    value = str(value).lower()
    value = value.replace("â‚¬", "").replace("€", "").strip()
    try:
        if "m" in value:
            return int(float(value.replace("m", "")) * 1_000_000)
        elif "k" in value:
            return int(float(value.replace("k", "")) * 1_000)
        return int(float(value))
    except ValueError:
        return 0


def ui_league_to_comp(league: str) -> str | None:
    """Translates UI league display names to the Competition column values used in FBref CSV data."""
    mapping = {
        "LaLiga": "es La Liga",
        "Premier League": "eng Premier League",
        "Bundesliga": "de Bundesliga",
        "Serie A": "it Serie A",
        "Ligue 1": "fr Ligue 1",
    }
    return mapping.get(league)

@functools.lru_cache(maxsize=1)
def _load_merged_df() -> pd.DataFrame:
    """
    Builds a unified DataFrame combining FBref stats and Transfermarkt market values.
    Cached so the expensive CSV load + fuzzy matching only runs once per process.

    - FBref is the source of truth: all FBref players are kept (right join).
    - TKM names are fuzzy-matched to FBref names before merging to handle discrepancies.
    - Players without a TKM match appear with Value=0.
    - Age always comes from FBref (always available); TKM Age column is dropped.
    """
    print("Cargando datos de Transfermarkt...")
    df_market = load_tfmkt_data()

    print("Cargando estadísticas de FBref...")
    df_stats = load_stadistics()

    # Normalizamos unicode para evitar desajustes por acentos
    df_market["Name"] = df_market["Name"].str.normalize("NFKD")
    df_stats["Player"] = df_stats["Player"].str.normalize("NFKD")

    # Deduplicar: jugadores que cambiaron de equipo aparecen 2 veces; conservar el de más minutos
    df_stats["Min"] = pd.to_numeric(
        df_stats["Min"].astype(str).str.replace(",", ""), errors="coerce"
    )
    df_stats = (
        df_stats.sort_values("Min", ascending=False)
        .drop_duplicates(subset="Player", keep="first")
    )

    df_market["Value"] = df_market["Value"].apply(clean_currency_value)

    # Fuzzy matching de nombres TKM contra FBref ANTES del merge
    fbref_names = df_stats["Player"].dropna().unique().tolist()
    df_market["Matched_Player"] = df_market["Name"].apply(
        lambda x: match_names(x, fbref_names, threshold=60)
    )

    # Right join: todos los jugadores de FBref se conservan; se añaden datos TKM donde hay coincidencia
    merged = df_market.merge(
        df_stats, left_on="Matched_Player", right_on="Player", how="right"
    )

    # Eliminamos columnas redundantes o que causan problemas tras el merge
    cols_to_drop = [c for c in ["index", "Unnamed: 0", "Age_x"] if c in merged.columns]
    merged = merged.drop(cols_to_drop, axis=1)

    # Renombramos la edad de FBref para que sea inequívoca (Age_y si TKM también tiene Age)
    if "Age_y" in merged.columns:
        merged = merged.rename(columns={"Age_y": "Age"})

    # Jugadores sin coincidencia en TKM tendrán Value=NaN → lo ponemos a 0
    merged["Value"] = merged["Value"].fillna(0)

    # Deduplicar merged: varios registros TKM pueden haber hecho match al mismo jugador FBref
    merged = (
        merged.sort_values("Value", ascending=False)
        .drop_duplicates(subset="Player", keep="first")
    )

    return merged


@observe(name="build_merged_df")
def _build_merged_df() -> pd.DataFrame:
    return _load_merged_df()

@tool
@observe(name="search_talent")
def search_talent(input: InputUser) -> list[PlayerResult]:
    """
    Searches across all datasets (FBref stats + Transfermarkt values) for players
    who meet the scouting input provided by the user. Returns a structured list
    of PlayerResult objects.
    """
    merged = _build_merged_df()

    fbref_pos = POSITION_MAP.get(input.position, input.position)
    resultado = merged[
        (merged["Pos"].str.contains(fbref_pos, case=False, na=False)) &
        (merged["Value"].astype(float) <= input.price_max) &
        (merged["Age"].astype(float) >= input.min_age) &
        (merged["Age"].astype(float) <= input.max_age) &
        (merged[input.key_metric].astype(float) >= input.min_value_key)
    ]

    players = []
    for _, row in resultado.iterrows():
        players.append(PlayerResult(
            player=str(row["Player"]),
            squad=str(row.get("Squad", "")),
            age=int(float(row["Age"])),
            position=str(row["Pos"]),
            value=int(float(row["Value"])),
            key_metric_name=input.key_metric,
            key_metric_value=float(row[input.key_metric]),
        ))

    return players

@tool
@observe(name="get_league_top_performers")
def get_league_top_performers(league_input: InputLeaguePerformers) -> list[dict] | str:
    """
    Returns the top N players in a league ranked by a chosen metric (goals, assists, G+A).
    Useful for finding top scorers or most productive players in a specific league.
    """
    try:
        merged = _build_merged_df()
        competition = ui_league_to_comp(league_input.league)
        if not competition:
            return f"Liga no reconocida: {league_input.league}"

        league_df = merged[merged["Comp"] == competition].copy()
        for col in ["Gls", "Ast", "G+A", "G/Sh", "MP"]:
            if col in league_df.columns:
                league_df[col] = pd.to_numeric(league_df[col], errors="coerce").fillna(0)

        top = league_df.sort_values(league_input.metric, ascending=False).head(league_input.top_n)

        result = []
        for _, row in top.iterrows():
            result.append({
                "name": str(row["Player"]),
                "team": str(row.get("Squad", "")),
                "pos": str(row.get("Pos", "")),
                "age": int(float(row.get("Age", 0) or 0)),
                "goals": int(float(row.get("Gls", 0) or 0)),
                "assists": int(float(row.get("Ast", 0) or 0)),
                "g_plus_a": int(float(row.get("G+A", 0) or 0)),
                "apps": int(float(row.get("MP", 0) or 0)),
                "g_per_sh": round(float(row.get("G/Sh", 0) or 0), 3),
            })
    except Exception as exc:
        return f"Error al obtener top performers: {exc}"
    else:
        return result


@tool
@observe(name="get_league_stats")
def get_league_stats(league_input: InputLeagueStats) -> dict | str:
    """
    Returns aggregate statistics for a league: total goals, top scorer,
    average goals per player, and shooting efficiency (G/Sh).
    """
    try:
        merged = _build_merged_df()
        competition = ui_league_to_comp(league_input.league)
        if not competition:
            return f"Liga no reconocida: {league_input.league}"

        league_df = merged[merged["Comp"] == competition].copy()
        for col in ["Gls", "Ast", "G/Sh", "90s"]:
            if col in league_df.columns:
                league_df[col] = pd.to_numeric(league_df[col], errors="coerce").fillna(0)

        total_goals = int(league_df["Gls"].sum())
        total_players = len(league_df)
        avg_goals = round(float(league_df["Gls"].mean()), 2)

        top_scorer_idx = league_df["Gls"].idxmax()
        top_scorer_row = league_df.loc[top_scorer_idx]
        top_scorer = str(top_scorer_row["Player"])
        top_scorer_goals = int(top_scorer_row["Gls"])
        top_scorer_team = str(top_scorer_row.get("Squad", ""))

        active = league_df[league_df["90s"] >= 1]
        if len(active) > 0:
            avg_g_per_90 = round(float((active["Gls"] / active["90s"]).mean()), 3)
        else:
            avg_g_per_90 = 0.0

        shooters = league_df[league_df["G/Sh"] > 0]
        avg_g_per_sh = round(float(shooters["G/Sh"].mean()), 3) if len(shooters) > 0 else 0.0

        stats = {
            "league": league_input.league,
            "total_players": total_players,
            "total_goals": total_goals,
            "avg_goals_per_player": avg_goals,
            "avg_goals_per_90": avg_g_per_90,
            "avg_shooting_efficiency": avg_g_per_sh,
            "top_scorer": top_scorer,
            "top_scorer_goals": top_scorer_goals,
            "top_scorer_team": top_scorer_team,
        }
    except Exception as exc:
        return f"Error al obtener estadísticas de liga: {exc}"
    else:
        return stats


class InputPlayerStats(BaseModel):
    """Input for fetching statistics of a specific player by name."""

    player_name: str = Field(
        description="Name of the player to look up (e.g., 'Federico Viñas', 'Mbappé')"
    )


@tool
@observe(name="get_player_stats")
def get_player_stats(player_input: InputPlayerStats) -> dict | str:
    """
    Returns all available statistics for a specific player by name.
    Use this when the user asks about a concrete player's stats
    (goals, assists, minutes played, etc.).
    Uses fuzzy matching to handle name variations and accents.
    """
    try:
        if isinstance(player_input, dict):
            player_input = InputPlayerStats(**player_input)
        merged = _build_merged_df()
        normalized_name = unicodedata.normalize("NFKD", player_input.player_name)
        matched = process.extractOne(
            normalized_name,
            merged["Player"].tolist(),
            scorer=fuzz.WRatio,
            score_cutoff=75,
        )
        matched = matched[0] if matched else None
        if not matched:
            return f"No se encontró a '{player_input.player_name}' en la base de datos."
        row = merged[merged["Player"] == matched].iloc[0]
        # Use to_json/loads to convert numpy types to JSON-native Python types
        return json.loads(row.dropna().to_json())
    except Exception as exc:
        return f"Error al obtener datos del jugador: {exc}"


@tool
@observe(name="find_similar_player")
def find_similar_player(input: InputSimilarPlayer) -> list[dict] | str:
    """
    Finds players with similar statistical profiles to a target player,
    acting as a replacement finder.
    """
    try:
        merged = _build_merged_df()

        _match = process.extractOne(
            unicodedata.normalize("NFKD", input.target_player),
            merged["Player"].tolist(),
            scorer=fuzz.WRatio,
            score_cutoff=75,
        )
        target_name_matched = _match[0] if _match else None

        if not target_name_matched:
            return f"No se pudo encontrar a {input.target_player} en la base de datos conjunta."

        metrics_to_compare = ["Gls", "Ast", "Sh/90", "Crs", "TklW", "Int"]
        valid_metrics = [m for m in metrics_to_compare if m in merged.columns]

        target_data = merged[merged["Player"] == target_name_matched][valid_metrics].fillna(0)
        all_players_data = merged[valid_metrics].fillna(0)

        scaler = StandardScaler()
        all_players_scaled = scaler.fit_transform(all_players_data)
        target_scaled = scaler.transform(target_data)

        similarities = cosine_similarity(target_scaled, all_players_scaled)[0]
        # Work on a copy to avoid mutating the cached DataFrame
        result_df = merged.copy()
        result_df["Similarity_Score"] = similarities

        resultado = result_df[
            (result_df["Player"] != target_name_matched) &
            (result_df["Value"].astype(float) <= input.price_max) &
            (result_df["Age"].astype(float) <= input.max_age)
        ]

        top_5 = resultado.sort_values("Similarity_Score", ascending=False).head(5)
        cols = ["Player", "Squad", "Age", "Pos", "Value", "Similarity_Score"]
        # Use to_json/loads to convert numpy types to JSON-native Python types
        return json.loads(top_5[cols].to_json(orient="records") or "[]")
    except Exception as exc:
        return f"Error al buscar jugadores similares: {exc}"
