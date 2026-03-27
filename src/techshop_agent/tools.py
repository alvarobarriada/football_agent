"""MaldinIA agent tools — """

from __future__ import annotations

from pydantic import BaseModel, Field
import pandas as pd
from typing import Literal
from thefuzz import process
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

from strands import tool

from techshop_agent.config import load_tfmkt_data, load_stadistics


class InputUser(BaseModel):
    """Model that contains information about a user request for scouting undervalued players."""

    price_max: int = Field(
        description="Maximum market value of the player in euros (e.g., 10000000 for €10M)"
    )
    min_age: int = Field(
        default=15, ge=14, le=50,
        description="Minimum age of the player"
    )
    max_age: int = Field(
        default=23, ge=14, le=50,
        description="Maximum age of the player"
    )
    key_metric: Literal[
        "Gls", "Ast", "G+A", "G-PK", "PK", "PKatt", "CrdY", "CrdR", "G+A-PK",
        "Sh", "SoT", "SoT%", "Sh/90", "SoT/90", "G/Sh", "G/SoT",
        "PK_stats_shooting", "PKAtt_stats_shooting", "Crs", "TklW", "Int",
        "Fld", "CrdY_stats_misc", "CrdR_stats_misc", "2CrdY", "Fls", "OG",
        "GA", "GA90", "SoTA", "Saves", "Save%", "W", "D", "L", "CS", "CS%",
        "PKatt_stats_keeper", "PKA", "PKsv", "PKm"
    ] = Field(description="Key performance metric")
    min_value_key: float = Field(
        description="Minimum threshold for the key metric (can be decimal, e.g., 0.35 or 85.5)"
    )
    position: Literal[
        "GK", "DF", "MF", "FW", "FB", "LB", "RB", "CB", "DM", "CM",
        "LM", "RM", "WM", "LW", "RW", "AM"
    ] = Field(
        description="Tactical position. Common formats: 'GK', 'DF', 'MF', 'FW' or specific ones like 'Right-Back'"
    )


class InputSimilarPlayer(BaseModel):
    """Model that contains information about a user request for finding similar players."""

    target_player: str = Field(
        description="Name of the player you want to find similar profiles for (e.g., 'Jude Bellingham')"
    )
    price_max: int = Field(
        description="Maximum market value of the similar players in euros"
    )
    max_age: int = Field(
        default=25,
        description="Maximum age of the similar players"
    )


class PlayerResult(BaseModel):
    """Structured result for a single player returned by search_talent."""

    player: str = Field(description="Player name")
    squad: str = Field(description="Current club")
    age: int = Field(description="Player age")
    position: str = Field(description="Player position")
    value: int = Field(description="Market value in euros (0 if unknown)")
    key_metric_name: str = Field(description="Name of the evaluated metric")
    key_metric_value: float = Field(description="Value of the evaluated metric")


def match_names(name_to_find, list_of_names, threshold=60):
    """Encuentra el nombre más parecido en una lista si supera el umbral."""
    if pd.isna(name_to_find):
        return None
    match, score = process.extractOne(name_to_find, list_of_names)
    if score >= threshold:
        return match
    return None


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


def translate_league_name(league_id: str) -> str:
    """Translates soccerdata/FBref league IDs to full descriptive names."""
    mapping = {
        "ENG-Premier League": "England Premier League",
        "FRA-Ligue 1": "France Ligue 1",
        "GER-Bundesliga": "Germany Bundesliga",
        "ITA-Serie A": "Italy Serie A",
        "ESP-La Liga": "Spain La Liga",
        "Big 5 European Leagues Combined": "Europe Big 5 Combined",
    }
    return mapping.get(league_id, league_id)


def _build_merged_df() -> pd.DataFrame:
    """
    Builds a unified DataFrame combining FBref stats and Transfermarkt market values.

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

    return merged


@tool
def search_talent(input: InputUser) -> list[PlayerResult]:
    """
    Searches across all datasets (FBref stats + Transfermarkt values) for players
    who meet the scouting input provided by the user. Returns a structured list
    of PlayerResult objects.
    """
    merged = _build_merged_df()

    resultado = merged[
        (merged["Pos"].str.contains(input.position, case=False, na=False)) &
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
def find_similar_player(input: InputSimilarPlayer) -> pd.DataFrame | str:
    """
    Finds players with similar statistical profiles to a target player,
    acting as a replacement finder.
    """
    merged = _build_merged_df()

    target_name_matched = match_names(
        input.target_player, merged["Player"].tolist(), threshold=70
    )

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
    merged["Similarity_Score"] = similarities

    resultado = merged[
        (merged["Player"] != target_name_matched) &
        (merged["Value"].astype(float) <= input.price_max) &
        (merged["Age"].astype(float) <= input.max_age)
    ]

    top_5 = resultado.sort_values(by="Similarity_Score", ascending=False).head(5)

    return top_5[["Player", "Squad", "Age", "Pos", "Value", "Similarity_Score"]]
