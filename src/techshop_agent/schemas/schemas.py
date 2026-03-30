import pandas as pd
from pydantic import BaseModel, Field
from typing import Literal


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
        "PK_stats_shooting", "PKatt_stats_shooting", "Crs", "TklW", "Int",
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


class InputLeaguePerformers(BaseModel):
    """Input for fetching top performers in a specific league."""

    league: Literal["LaLiga", "Premier League", "Bundesliga", "Serie A", "Ligue 1"] = Field(
        description="League name to query"
    )
    top_n: int = Field(default=5, ge=1, le=20, description="Number of top players to return")
    metric: Literal["Gls", "Ast", "G+A"] = Field(
        default="Gls", description="Metric used to rank players"
    )


class InputLeagueStats(BaseModel):
    """Input for fetching aggregate stats for a specific league."""

    league: Literal["LaLiga", "Premier League", "Bundesliga", "Serie A", "Ligue 1"] = Field(
        description="League name to query"
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

