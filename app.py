import streamlit as st
import pandas as pd
import plotly.express as px
import geopandas as gpd
import folium
from streamlit.components.v1 import html
from streamlit_folium import folium_static

no = pd.read_csv("Book.csv")
gjson = gpd.read_file('Africa_NO2.geojson')
name_map = {
    "Ivory Coast":"Côte d'Ivoire"
}
no["NAME"] = no["NAME"].replace(name_map)
merge_df = gjson.merge(no, on="NAME")

color_dict = {
    "Decrease": "#1f78b4",        # blue
    "Slight Decrease": "#ffcc00", # yellow
    "Increase": "#e31a1c"         # red
}
# ---------- STREAMLIT SETTINGS ----------
st.set_page_config(layout="wide", page_title="NO₂ Dashboard")
# ---------- SIDEBAR NAVIGATION ----------
page = st.sidebar.radio("📁 Navigate", ["Introduction 🗒️", "Change Map 🗺️", "Line Chart 📈", "Bar Chart 📊"])

# ---------- PAGE 1: INTRODUCTION ----------
if page == "Introduction 🗒️":
    st.title("🌍 African NO₂ Dashboard")
    st.subheader("📖 Project Overview")

    st.markdown("""
    This dashboard analyzes **Nitrogen dioxide (NO₂)** levels across African countries using data from **Sentinel-5P**.

    ### 🔍 Data Source
    - **Satellite:** Sentinel-5P (Copernicus)
    - **Band:** `NO2_column_number_density`
    - **Source:** Google Earth Engine (GEE)
    
    ### ⚙️ Workflow Summary
    1. Africa shapefile or GeoJSON loaded
    2. Nitrogen dioxide (NO₂) levels were obtained from Google Earth Engine for the years 2018, 2020, 2022, and 2024 and exported as CSV
    3. Processed and Cleaned in **Jupyter Notebook**
    4. Visualized using **Streamlit**

    The goal is to compares NO₂ trends across countries, to identify changes—both increases and decreases from 2018 to 2024.
    """)

#st.title("🌍 African NO₂ Dashboard (2018-2024)")
#st.markdown("Compare nitrogen dioxide (NO₂) trends across Africa using change maps and charts.")

# ---------- PAGE 2: CHANGE MAP ----------
elif page == "Change Map 🗺️":
    st.title("🗺️ NO₂ Change Map (2018 - 2024)")

    # Categorize the NO₂ Change values
    def classify_change(val):
        if val < -0.000005:
            return "Decrease"
        elif -0.000005 <= val <= 0.000000:
            return "Slight Decrease"
        else:
            return "Increase"

    merge_df["Change_Category"] = merge_df["2024 - 2018"].apply(classify_change)

    # Convert GeoDataFrame to GeoJSON
    gjs = merge_df.to_json()
    # Create base map
    m = folium.Map(location=[0, 20], zoom_start=3, tiles="cartodb positron")

    # Add styled GeoJson layer
    folium.GeoJson(
        gjs,
        name="NO₂ Change",
        style_function=lambda feature: {
            "fillColor": color_dict.get(feature["properties"]["Change_Category"], "gray"),
            "color": "black",
            "weight": 0.5,
            "fillOpacity": 0.7,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["NAME", "Change_Category"],
            aliases=["Country:", "Category:"],
            localize=True
        )
    ).add_to(m)
    
    # 🧭 Custom HTML legend
    legend_html = """
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        width: 160px;
        height: 110px;
        background-color: white;
        border:2px solid grey;
        z-index:9999;
        font-size:14px;
        padding: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
    <b>NO₂ Change Legend</b><br>
    <div style='margin-top: 5px;'>
    <span style="background:#1f78b4; width:12px; height:12px; display:inline-block; border-radius:2px;"></span>
    Decrease
    </div>
    <div>
    <span style="background:#ffcc00; width:12px; height:12px; display:inline-block; border-radius:2px;"></span>
    Slight Decrease
    </div>
    <div>
    <span style="background:#e31a1c; width:12px; height:12px; display:inline-block; border-radius:2px;"></span>
    Increase
    </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Display in Streamlit
    m.save("change_map.html")
    with open("change_map.html", "r", encoding="utf-8") as f:
        map_html = f.read()
    st.components.v1.html(map_html, height=600)


# ---------- PAGE 3: Line Chart ----------
elif page == 'Line Chart 📈':
    st.markdown("---")
    st.subheader("📈 NO₂ Trend Analysis (2018 - 2024)")

    # Prepare long-format dataframe
    trend_df = no.melt(
        id_vars="NAME",
        value_vars=["2018_mean", "2020_mean", "2022_mean", "2024_mean"],
        var_name="Year", value_name="NO2"
    )
    trend_df["Year"] = trend_df["Year"].str.replace("_mean", "").astype(int)

    # ========== SINGLE COUNTRY LINE CHART ==========
    st.markdown("### 🔹 Single Country Trend")

    one_country = st.selectbox("Select a country to view trend:", sorted(no["NAME"].unique()))

    country_data = trend_df[trend_df["NAME"] == one_country]

    fig1 = px.line(
        country_data,
        x="Year",
        y="NO2",
        title=f"NO₂ Trend for {one_country}",
        markers=True,
        labels={"NO2": "NO₂ (mol/m²)", "Year": "Year"}
    )
    fig1.update_traces(mode="lines+markers", line=dict(color='teal'))
    fig1.update_layout(height=400)

    st.plotly_chart(fig1, use_container_width=True)

    # ========== MULTIPLE COUNTRY COMPARISON ==========
    st.markdown("### 🔸 Multi-Country Comparison")

    selected_countries = st.multiselect(
        "Select countries to compare:",
        sorted(no["NAME"].unique()),
        default=["Nigeria", "South Africa"]
    )

    if selected_countries:
        filtered_df = trend_df[trend_df["NAME"].isin(selected_countries)]

        fig2 = px.line(
            filtered_df,
            x="Year",
            y="NO2",
            color="NAME",
            markers=True,
            title="NO₂ Trend Comparison (Multiple Countries)",
            labels={"NO2": "NO₂ (mol/m²)", "Year": "Year"}
        )
        fig2.update_traces(mode="lines+markers")
        fig2.update_layout(height=500)

        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Please select at least one country to display the comparison chart.")


# ---------- PAGE 4: BAR CHART ----------
elif page == "Bar Chart 📊":
    st.title("📊 NO₂ Change Bar Chart (2018 - 2024)")


    countries = no["NAME"].unique()
    selected_country = st.selectbox("Select a country", countries)

    # Extract and reshape data
    row = no[no["NAME"] == selected_country]
    years = ["2018_mean", "2020_mean", "2022_mean", "2024_mean"]
    values = row[years].values.flatten().tolist()

    chart_no = pd.DataFrame({
        "Year": years,
        "NO₂ (mol/m²)": values
    })

    fig = px.bar(chart_no, x="Year", y="NO₂ (mol/m²)",
                title=f"NO₂ Trend for {selected_country}",
                color="NO₂ (mol/m²)",
                color_continuous_scale="OrRd")

    st.plotly_chart(fig, use_container_width=True)