"""MaldinIA agent tools — """

from __future__ import annotations
from json import load

from pydantic import BaseModel, Field
import pandas as pd
from typing import Literal
from thefuzz import process
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

from strands import tool

from techshop_agent.config import load_tfmkt_data, load_stadistics

_SIMILARITY_THRESHOLD = 0.6



class InputUser(BaseModel):
    """Model that contains information about a user request for scouting undervalued players."""
    
    # Corrected 'prize' to 'price' (monetary value)
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
    
    # Changed to float to support metrics like xG, xA, or percentages (e.g., 0.35)
    key_metric: Literal["Gls","Ast","G+A","G-PK","PK","PKatt","CrdY","CrdR","G+A-PK","Sh","SoT","SoT%","Sh/90","SoT/90","G/Sh","G/SoT","PK_stats_shooting","PKAtt_stats_shooting","Crs","TklW","Int","Fld","CrdY_stats_misc","CrdR_stats_misc","2CrdY","Fls","OG","GA","GA90","SoTA","Saves","Save%","W","D","L","CS","CS%","PKatt_stats_keeper","PKA","PKsv","PKm"] = Field(
        description="Key performance metric"
    )
    
    min_value_key: float = Field(
        description="Minimum threshold for the key metric (can be decimal, e.g., 0.35 or 85.5)"
    )
    position: Literal["GK","DF","MF","FW","FB","LB","RB","CB","DM","CM","LM","RM","WM","LW","RW","AM"] = Field(
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

def match_names(name_to_find, list_of_names, threshold=60):
    """Encuentra el nombre más parecido en una lista si supera el umbral."""
    if pd.isna(name_to_find):
        return None
    
    # process.extractOne devuelve una tupla: (mejor_coincidencia, puntuacion)
    match, score = process.extractOne(name_to_find, list_of_names)
    
    if score >= threshold:
        return match
    return None


def clean_currency_value(value):
    if pd.isna(value) or value == '-':
        return 0
    
    # Convertimos a string y pasamos a minúsculas
    value = str(value).lower()
    
    # Limpiamos el ruido del símbolo de moneda (incluyendo el error de encoding)
    value = value.replace('â‚¬', '').replace('€', '').strip()
    
    try:
        if 'm' in value:
            return int(float(value.replace('m', '')) * 1_000_000)
        elif 'k' in value:
            return int(float(value.replace('k', '')) * 1_000)
        return int(float(value))
    except ValueError:
        return 0


def translate_league_name(league_id: str) -> str:
    """
    Translates soccerdata/FBref league IDs to full descriptive names.
    """
    mapping = {
        'ENG-Premier League': 'England Premier League',
        'FRA-Ligue 1': 'France Ligue 1',
        'GER-Bundesliga': 'Germany Bundesliga',
        'ITA-Serie A': 'Italy Serie A',
        'ESP-La Liga': 'Spain La Liga',
        'Big 5 European Leagues Combined': 'Europe Big 5 Combined'
    }
    
    # .get() handles cases where the league might not be in the dict
    return mapping.get(league_id, league_id)

@tool
def search_talent(input: InputUser):
        """This tool searches for candidates who meet the criteria entered by the user"""
        print("Obteniendo valores de Transfermarkt...")
        df_market= load_tfmkt_data()

        print("Obteniendo métricas de FBref...")
        df_stats = load_stadistics()
        df_market['Name'] = df_market['Name'].str.normalize("NFKD")
        df_stats['Player'] = df_stats['Player'].str.normalize("NFKD")
        df_market['Value'] = df_market['Value'].apply(clean_currency_value)

        fbref_names = df_stats['Player'].dropna().unique().tolist()
        df_market['Matched_Player'] = df_market['Name'].apply(
        lambda x: match_names(x, fbref_names, threshold=60)
    )

        merged = pd.merge(df_market, df_stats, left_on='Name',right_on='Player', how='right')
        merged.drop(['index','Unnamed: 0'],inplace=True, axis=1)
        
        merged.to_csv('prueba.csv', index=False, encoding='utf-8')

        # 4. Lógica de filtrado (El "Filtro de Gangas")
        # Ejemplo para: Lateral Derecho, < 23 años, < 10M€, Centros > 35%
        resultado = merged[
            (merged['Pos'].str.contains(input.position, case=False)) &
            (merged['Value'].astype(float) <= input.price_max) &
            (merged['Age_x'].astype(float) >= input.min_age) &
            (merged['Age_x'].astype(float) <= input.max_age) &
            (merged[input.key_metric].astype(float) >= input.min_value_key)
        ]
        print(resultado.head)

        return resultado[['Player', 'Squad', 'Age_x','Pos', 'Value', input.key_metric]]



@tool
def find_similar_player(input: InputSimilarPlayer):
    """This tool finds players with similar statistical profiles to a target player, acting as a replacement finder."""
    df_market = load_tfmkt_data()
    df_stats = load_stadistics()
    
    # Limpieza básica
    df_market['Value'] = df_market['Value'].apply(clean_currency_value)
    
    # Asumimos que ya aplicaste el fuzzy matching del paso anterior o un merge directo
    # Para este ejemplo, haremos un merge directo simplificado
    merged = pd.merge(df_market, df_stats, left_on='Name', right_on='Player', how='inner')
    
    # Buscamos al jugador objetivo (usando thefuzz para no fallar si el usuario lo escribe un poco mal)
    target_name_matched = match_names(input.target_player, merged['Player'].tolist(), threshold=70)
    
    if not target_name_matched:
        return f"No se pudo encontrar a {input.target_player} en la base de datos conjunta."

    # Seleccionamos las columnas numéricas relevantes para comparar (puedes añadir o quitar)
    metrics_to_compare = ['Gls', 'Ast', 'Sh/90', 'Crs', 'TklW', 'Int', 'PassCompletionPct'] 
    
    # Filtramos solo las columnas que existan en el dataframe
    valid_metrics = [m for m in metrics_to_compare if m in merged.columns]
    
    # Extraemos los datos del jugador objetivo
    target_data = merged[merged['Player'] == target_name_matched][valid_metrics].fillna(0)
    
    # Preparamos los datos del resto de jugadores (y rellenamos NaNs con 0)
    all_players_data = merged[valid_metrics].fillna(0)
    
    # Normalizamos los datos estadísticos para que goles y porcentajes pesen igual
    scaler = StandardScaler()
    all_players_scaled = scaler.fit_transform(all_players_data)
    target_scaled = scaler.transform(target_data)
    
    # Calculamos la similitud del coseno (0 a 1, donde 1 es idéntico)
    similarities = cosine_similarity(target_scaled, all_players_scaled)[0]
    
    # Añadimos la puntuación de similitud al dataframe
    merged['Similarity_Score'] = similarities
    
    # Filtramos por las reglas del usuario (quitando al propio jugador objetivo)
    resultado = merged[
        (merged['Player'] != target_name_matched) &
        (merged['Value'].astype(float) <= input.price_max) &
        (merged['Age_x'].astype(float) <= input.max_age)
    ]
    
    # Ordenamos por los más parecidos y devolvemos el top 5
    top_5 = resultado.sort_values(by='Similarity_Score', ascending=False).head(5)
    
    return top_5[['Player', 'Squad', 'Age_x', 'Pos', 'Value', 'Similarity_Score']]