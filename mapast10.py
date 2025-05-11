import pandas as pd
import folium
import streamlit as st
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
from pathlib import Path

st.set_page_config(layout="wide")

# ======================
# Funções utilitárias
# ======================

@st.cache_data
def carregar_dados():
    caminho = Path(__file__).parent / "estradaBA-BR242.csv"
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

def gerar_pie_chart(dados, labels, titulo):
    fig, ax = plt.subplots()
    ax.pie(dados, labels=labels, autopct='%1.1f%%')
    ax.set_title(titulo)
    return fig

# ======================
# Streamlit UI
# ======================

df = carregar_dados()
pontos_info, media = calcular_estatisticas(df)

st.subheader("Mapa de Acidentes")
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
            popup=f"{km}",
            icon=folium.Icon(color=cor)
        ).add_to(mapa)

# Exibe o mapa com área suficiente para os gráficos abaixo
retorno = st_folium(mapa, width=900, height=600)

# Mostrar gráficos abaixo do mapa
if retorno and retorno.get("last_object_clicked_tooltip"):
    st.markdown("---")
    st.subheader("Estatísticas do Ponto Selecionado")

    try:
        texto_tooltip = retorno["last_object_clicked_tooltip"]
        km_selecionado = int(float(texto_tooltip.split()[1]))  # extrai km do tipo "Km 150"
        ponto = next((p for p in pontos_info if p[2] == km_selecionado), None)

        if ponto:
            lat, lon, km, total, obitos, leves, graves = ponto

            col1, col2 = st.columns(2)

            with col1:
                fig1 = gerar_pie_chart(
                    [obitos, leves, graves],
                    ['Óbitos', 'Leves', 'Graves'],
                    "Tipos de Lesões"
                )
                st.pyplot(fig1)

            with col2:
                fig2 = gerar_pie_chart(
                    [total - obitos - leves - graves, obitos + leves + graves],
                    ['Outros', 'Com Lesões'],
                    "Gravidade"
                )
                st.pyplot(fig2)
    except Exception as e:
        st.error(f"Erro ao processar seleção: {e}")
else:
    st.info("Clique em um marcador do mapa para ver os gráficos.")
