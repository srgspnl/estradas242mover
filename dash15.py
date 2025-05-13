import pandas as pd
import folium
import streamlit as st
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
from pathlib import Path
import re

st.set_page_config(layout="wide")

# ======================
# Funções utilitárias
# ======================

RODOVIAS_INFO = {
    "BR 242": {"arquivo": "estradaBA-BR242.csv", "km_inicio": 140, "km_fim": 901},
    "BR 324": {"arquivo": "estradaBA-BR324.csv", "km_inicio": 486, "km_fim": 627},
    "BR 101": {"arquivo": "estradaBA-BR101.csv", "km_inicio": 0, "km_fim": 948},
    "BR 116": {"arquivo": "estradaBA-BR116.csv", "km_inicio": 2, "km_fim": 928},
    "BR 110": {"arquivo": "estradaBA-BR110.csv", "km_inicio": 0, "km_fim": 403},
}

@st.cache_data
def carregar_dados(caminho_arquivo):
    caminho = Path(__file__).parent / caminho_arquivo
    return pd.read_csv(caminho, sep=";", encoding="utf-8-sig")

def coordenadas_por_km(df, coluna_contagem):
    """
    Agrupa os dados por km e retorna um dicionário com:
    km -> (latitude média, longitude média, contagem da coluna desejada)
    """
    coords = {}
    grupo_km = df.groupby("km")
    for km, grupo in grupo_km:
        if pd.notna(km) and not grupo.empty:
            lat = grupo["latitude"].mean()
            lon = grupo["longitude"].mean()
            contagem = grupo[coluna_contagem].sum() if coluna_contagem == 'mortos' else grupo[coluna_contagem].count()
            coords[km] = (lat, lon, contagem)
    return coords

# ======================
# Interface Streamlit
# ======================

st.title("🚧 Visualização de Acidentes nas Rodovias da Bahia")

# Sidebar para filtros
with st.sidebar:
    st.header("🛣️ Filtros")
    rodovia_selecionada = st.selectbox("Selecione a Rodovia", list(RODOVIAS_INFO.keys()))
    info_rodovia = RODOVIAS_INFO[rodovia_selecionada]
    km_inicio, km_fim = st.slider(
        "Intervalo de quilômetros",
        min_value=0, max_value=1000,
        value=(info_rodovia["km_inicio"], info_rodovia["km_fim"]),
        step=10
    )

# Carregar dados
df = carregar_dados(info_rodovia["arquivo"])

# Obter coordenadas por km (acidentes)
coords_acidentes = coordenadas_por_km(df, 'id')

# Obter coordenadas por km (óbitos)
coords_mortos = coordenadas_por_km(df, 'mortos')

# Criar o mapa
st.subheader("🗺️ Mapa dos Top 10 Trechos Críticos")
mapa = folium.Map(location=[-12.5, -41.5], zoom_start=7)

# Exibir os top 10 trechos com mais acidentes
top10_km_acidentes = sorted(coords_acidentes.items(), key=lambda x: x[1][2], reverse=True)[:10]
for km, (lat, lon, total) in top10_km_acidentes:
    folium.Marker(
        location=(lat, lon),
        tooltip=f"Top Acidente - Km {km} ({total} acidentes)",
        icon=folium.Icon(color="red", icon="warning")
    ).add_to(mapa)

# Exibir os top 10 trechos com mais óbitos
top10_km_mortos = sorted(coords_mortos.items(), key=lambda x: x[1][2], reverse=True)[:10]
for km, (lat, lon, mortos) in top10_km_mortos:
    folium.Marker(
        location=(lat, lon),
        tooltip=f"Top Óbito - Km {km} ({mortos} mortos)",
        icon=folium.Icon(color="black", icon="info-sign")
    ).add_to(mapa)

# Exibir o mapa
retorno = st_folium(mapa, width=900, height=600)

# Gráficos
st.subheader("📊 Estatísticas de Acidentes")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Acidentes por Tipo de Veículo")
    tipo_veiculo = df['tipo_veiculo'].value_counts()
    fig1, ax1 = plt.subplots()
    ax1.pie(tipo_veiculo, labels=tipo_veiculo.index, autopct='%1.1f%%', startangle=90)
    ax1.set_title("Distribuição por Tipo de Veículo")
    st.pyplot(fig1)

with col2:
    st.markdown("### Acidentes por Condição Meteorológica")
    condicao_meteorologica = df['condicao_metereologica'].value_counts()
    fig2, ax2 = plt.subplots()
    ax2.pie(condicao_meteorologica, labels=condicao_meteorologica.index, autopct='%1.1f%%', startangle=90)
    ax2.set_title("Distribuição por Condição Meteorológica")
    st.pyplot(fig2)

# Gráficos das 10 semanas mais críticas
st.subheader("🗓️ Top 10 Semanas Mais Críticas")
# Garantir que a coluna 'data_inversa' esteja no formato de data
df['data_inversa'] = pd.to_datetime(df['data_inversa'], errors='coerce')
# Agora, extraímos a semana
df['semana'] = df['data_inversa'].dt.isocalendar().week
#df['semana'] = pd.to_datetime(df['data_inversa']).dt.week
semana_critica = df.groupby('semana').size().sort_values(ascending=False).head(10)
fig3, ax3 = plt.subplots()
semana_critica.plot(kind='bar', ax=ax3)
ax3.set_title("Top 10 Semanas com Mais Acidentes")
ax3.set_ylabel("Número de Acidentes")
st.pyplot(fig3)

