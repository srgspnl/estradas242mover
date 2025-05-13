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
    "BR 101": {"arquivo": "estradaBA-BR101.csv", "km_inicio": 0,   "km_fim": 948},
    "BR 116": {"arquivo": "estradaBA-BR116.csv", "km_inicio": 2,   "km_fim": 928},
    "BR 110": {"arquivo": "estradaBA-BR110.csv", "km_inicio": 0,   "km_fim": 403},
}

@st.cache_data
def carregar_dados(caminho_arquivo):
    caminho = Path(__file__).parent / caminho_arquivo
    return pd.read_csv(caminho, sep=";", encoding="utf-8-sig")

def calcular_estatisticas(df, km_inicio=140, km_fim=900, passo=10):
    intervalos = [(i, i + passo) for i in range(km_inicio, km_fim, passo)]
    pontos_latlon_km = []
    soma_total_linhas = 0

    for inicio, fim in intervalos:
        faixa = df[(df['km'] >= inicio) & (df['km'] < fim)]
        if not faixa.empty:
            ponto = faixa.iloc[0]
            contagem = faixa['estado_fisico'].value_counts()
            obitos = contagem.get('Óbito', 0)
            leves = contagem.get('Lesões Leves', 0)
            graves = contagem.get('Lesões Graves', 0)
            tupla = (
                ponto['latitude'], ponto['longitude'], ponto['km'],
                len(faixa), obitos, leves, graves
            )
            pontos_latlon_km.append(tupla)
            soma_total_linhas += len(faixa)

    media = soma_total_linhas / len(pontos_latlon_km) if pontos_latlon_km else 0
    return pontos_latlon_km, media

def gerar_pie_chart(dados, labels, titulo, cores=None):
    total = sum(dados)
    if total == 0:
        dados = [1]
        labels = ["Sem dados"]
        cores = ["#d3d3d3"]

    if cores is None:
        cores = ['#d62728', '#ff7f0e', '#1f77b4']  # vermelho, laranja, azul

    fig, ax = plt.subplots()
    ax.pie(dados, labels=labels, autopct='%1.1f%%', colors=cores, startangle=90)
    ax.set_title(titulo)
    ax.axis('equal')  # formato circular
    return fig

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
pontos_info, media = calcular_estatisticas(df, km_inicio, km_fim)

# Criar o mapa
st.subheader("🗺️ Mapa de Acidentes")
mapa = folium.Map(location=[-12.5, -41.5], zoom_start=7)

for lat, lon, km, total, obitos, leves, graves in pontos_info:
    if pd.notna(lat) and pd.notna(lon):
        cor = "red"
        if total > media * 1.25:
            cor = "purple"
        elif total < media * 0.75:
            cor = "orange"

        tooltip_text = (
            f"Km {km}<br>"
            f"Total: {total}<br>"
            f"Óbitos: {obitos}<br>"
            f"Leves: {leves}<br>"
            f"Graves: {graves}"
        )

        folium.Marker(
            location=(lat, lon),
            tooltip=tooltip_text,
            popup=f"{tooltip_text}",
            icon=folium.Icon(color=cor)
        ).add_to(mapa)

# Exibir o mapa
retorno = st_folium(mapa, width=900, height=600)

# Gráficos ao clicar no marcador
if retorno and retorno.get("last_object_clicked_tooltip"):
    st.markdown("---")
    st.subheader("📊 Estatísticas do Ponto Selecionado")

    try:
        #texto_tooltip = retorno["last_object_clicked_tooltip"]
        #km_str = texto_tooltip.split("<br>")[0].replace("Km ", "").strip()
        #km_selecionado = int(float(km_str))
        

        texto_tooltip = retorno["last_object_clicked_tooltip"]
        match = re.search(r"Km\s*([\d\.]+)", texto_tooltip)

        if match:
            km_selecionado = int(float(match.group(1)))
            ponto = next((p for p in pontos_info if int(p[2]) == km_selecionado), None)
        else:
            st.warning("Não foi possível extrair o km do marcador.")
            ponto = None

        ponto = next((p for p in pontos_info if p[2] == km_selecionado), None)

        if ponto:
            lat, lon, km, total, obitos, leves, graves = ponto

            col1, col2 = st.columns(2)

            with col1:
                fig1 = gerar_pie_chart(
                    [obitos, leves, graves],
                    ['Óbitos', 'Lesões Leves', 'Lesões Graves'],
                    "Distribuição por Tipo de Lesão"
                )
                st.pyplot(fig1)

            with col2:
                fig2 = gerar_pie_chart(
                    [total - (obitos + leves + graves), obitos + leves + graves],
                    ['Sem Lesão', 'Com Lesões'],
                    "Proporção de Lesões"
                )
                st.pyplot(fig2)
    except Exception as e:
        st.error(f"Erro ao processar seleção: {e}")
else:
    st.info("Clique em um marcador no mapa para ver estatísticas detalhadas.")
