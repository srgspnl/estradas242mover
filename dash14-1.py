import pandas as pd
import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

# ============================
# Configurações iniciais
# ============================
st.set_page_config(layout="wide")
st.title("🚧 Painel de Acidentes nas Rodovias da Bahia")

RODOVIAS_INFO = {
    "BR242": {"arquivo": "estradaBA-BR242.csv", "km_inicio": 140, "km_fim": 901},
    "BR324": {"arquivo": "estradaBA-BR324.csv", "km_inicio": 486, "km_fim": 627},
    "BR101": {"arquivo": "estradaBA-BR101.csv", "km_inicio": 0,   "km_fim": 948},
    "BR116": {"arquivo": "estradaBA-BR116.csv", "km_inicio": 2,   "km_fim": 928},
    "BR110": {"arquivo": "estradaBA-BR110.csv", "km_inicio": 0,   "km_fim": 403},
}

rodovia = st.sidebar.selectbox("Selecione a rodovia", list(RODOVIAS_INFO.keys()))
info = RODOVIAS_INFO[rodovia]

# ============================
# Carregamento e preprocessamento
# ============================
df = pd.read_csv(info["arquivo"], sep=';', encoding='utf-8-sig')
df['km'] = pd.to_numeric(df['km'], errors='coerce')
df['data_inversa'] = pd.to_datetime(df['data_inversa'], errors='coerce')
df.dropna(subset=['km', 'latitude', 'longitude'], inplace=True)
df = df[(df['km'] >= info['km_inicio']) & (df['km'] <= info['km_fim'])]
df['km_faixa'] = (df['km'] // 10 * 10).astype(int)

# ============================
# Estatísticas por trecho
# ============================
grupado_km = df.groupby('km_faixa').agg({
    'id': 'count',
    'mortos': 'sum',
    'latitude': 'first',
    'longitude': 'first'
}).rename(columns={'id': 'acidentes'})

top10_acidentes = grupado_km.nlargest(10, 'acidentes')
top10_mortos = grupado_km.nlargest(10, 'mortos')

# ============================
# Gráficos
# ============================
top_semanas = df['data_inversa'].dt.isocalendar().week.value_counts().nlargest(10)
tipo_veiculo = df['tipo_veiculo'].value_counts()
cond_meteo = df['condicao_metereologica'].value_counts()

# ============================
# Exibição em 3 colunas
# ============================
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 Top 10 Trechos com Mais Acidentes")
    st.dataframe(top10_acidentes.reset_index())

    st.markdown("### 🌧️ Condição Meteorológica (Pie Chart)")
    fig1, ax1 = plt.subplots()
    ax1.pie(cond_meteo, labels=cond_meteo.index, autopct='%1.1f%%')
    ax1.set_title("Distribuição das Condições Climáticas")
    st.pyplot(fig1)

with col2:
    st.markdown("### 💀 Top 10 Trechos com Mais Óbitos")
    st.dataframe(top10_mortos.reset_index())

    st.markdown("### 👩‍🚗 Tipos de Veículo Envolvidos")
    st.bar_chart(tipo_veiculo)

st.markdown("### 🕛 10 Semanas com Mais Acidentes")
st.bar_chart(top_semanas)

# ============================
# Mapa com top 10 trechos
# ============================
st.markdown("### 🌍 Mapa dos Top 10 Trechos Críticos")
mapa = folium.Map(location=[-12.5, -41.5], zoom_start=7)
cluster = MarkerCluster().add_to(mapa)

for idx, row in top10_acidentes.iterrows():
    folium.Marker(
        location=(row['latitude'], row['longitude']),
        tooltip=f"Km {idx} - Acidentes: {row['acidentes']}\nÓbitos: {row['mortos']}",
        icon=folium.Icon(color='red', icon='exclamation-sign')
    ).add_to(cluster)

st_folium(mapa, width=900, height=500)