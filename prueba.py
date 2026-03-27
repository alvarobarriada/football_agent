from typing import Literal

import ScraperFC as sfc
from pydantic import BaseModel, Field
import pandas as pd

from pydantic import BaseModel, Field
from typing import Literal
import yaml


with open('./archivo.yaml','r') as file:
    data = yaml.safe_load(file)



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

def search_talent(input: InputUser):
        """This tool searches for candidates who meet the criteria entered by the user"""
        print("Obteniendo valores de Transfermarkt...")
        df_market= pd.read_csv(data.get('mkt_path','./src/techshop_agent/data/tkm_data.csv'),sep=";")

        print("Obteniendo métricas de FBref...")
        df_stats = pd.read_csv(data.get('csv_path','./src/techshop_agent/data/players_data_light-2025_2026.csv'))
        df_market['Name'] = df_market['Name'].str.normalize("NFKD")
        df_stats['Player'] = df_stats['Player'].str.normalize("NFKD")
        df_market['Value'] = df_market['Value'].apply(clean_currency_value)


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

input = InputUser(price_max=20000000, key_metric="Gls", min_value_key=1,position="AM", min_age=24, max_age=30 )

gangas = search_talent(input)

print(gangas)