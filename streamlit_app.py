import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse

# --- Load and Clean Dataset ---
df = pd.read_csv("cleaned_spotify_dataset.csv", low_memory=False)
df.drop(columns=[col for col in df.columns if 'Unnamed' in col], inplace=True)
df = df[df['Weeknum'].notna()]
df['Weeknum'] = df['Weeknum'].astype(str)
df['Markets'] = df['Markets'].astype(str)


# --- Sidebar Filters ---
st.sidebar.title("Spotify Top 50 Explorer")

countries = sorted(df['Country'].dropna().unique())
country_option = ["All"] + countries
selected_country = st.sidebar.selectbox("Select Country", country_option)

weeks = sorted(df['Weeknum'].unique())
week_option = ["All"] + weeks
selected_week = st.sidebar.selectbox("Select Week", week_option)

artists = sorted(df['Artist Name'].dropna().unique())
selected_artist = st.sidebar.selectbox("Select Artist", ["All"] + artists)

# Filter logic
filtered_df = df.copy()

if selected_country != "All":
    filtered_df = filtered_df[filtered_df['Country'] == selected_country]

if selected_week != "All":
    filtered_df = filtered_df[filtered_df['Weeknum'] == selected_week]

if selected_artist != "All":
    filtered_df = filtered_df[filtered_df['Artist Name'] == selected_artist]

tracks = sorted(filtered_df['Track Name'].dropna().unique())
selected_track = st.sidebar.selectbox("Select Track", ["All"] + tracks)

if selected_track != "All":
    filtered_df = filtered_df[filtered_df['Track Name'] == selected_track]

# --- Page Title ---
display_country = selected_country if selected_country != "All" else "All Countries"
display_country_name = df[df['Country'] == selected_country]['Country Name'].iloc[0] if selected_country != "All" else "All Countries"
display_week = selected_week if selected_week != "All" else "All Weeks"
st.title(f"🎧 Spotify Top 50 - {display_country_name} ({display_week})")

# --- Metric Selector for Bar Chart ---
st.subheader("🔝 Top 10 Songs Chart")
metric_options = ["Popularity", "Danceability", "Energy", "Acousticness", "Instrumentalness", "Positiveness"]
selected_metric = st.selectbox("Select metric to display", metric_options)

# Drop duplicate track-artist combinations to avoid duplicates across weeks
filtered_top = (
    filtered_df
    .drop_duplicates(subset=['Track Name', 'Artist Name'])
    .sort_values(by=selected_metric, ascending=False)
    .head(10)
)

fig_top10 = px.bar(
    filtered_top,
    x='Track Name',
    y=selected_metric,
    color='Artist Name',
    title=f'Top {len(filtered_top)} Songs by {selected_metric}',
)

# Fix Y-axis if metric is Popularity (should be 0–100)
if selected_metric == "Popularity":
    fig_top10.update_yaxes(range=[0, 100])

st.plotly_chart(fig_top10)


# --- Song or Artist Detail Section ---
if selected_track != "All":
    st.subheader(f"🎵 Selected Song Details - {selected_track}")

    # Spotify button
    track = df[df['Track Name'] == selected_track].iloc[0]
    search_query = urllib.parse.quote(f"{track['Track Name']} {track['Artist Name']}")
    spotify_url = f"https://open.spotify.com/search/{search_query}"
    st.markdown(f"[🔗 Listen on Spotify]({spotify_url})")

    all_time_song = df[df['Track Name'] == selected_track].copy()

    week_counts = all_time_song.groupby('Country Name')['Weeknum'].nunique().reset_index(name='Weeks Featured')
    best_ranking = all_time_song.groupby('Country Name')['ranking'].min().reset_index(name='Best Ranking')
    stats_df = pd.merge(week_counts, best_ranking, on='Country Name')

    st.markdown("**🌍 Song Stats Across Countries**")
    st.dataframe(stats_df.sort_values(by='Weeks Featured', ascending=False), use_container_width=True, hide_index=True)

    # Radar Chart of Audio Features
    st.subheader("🧬 Audio Features Radar")
    features = ['Danceability', 'Acousticness', 'Energy', 'Instrumentalness', 'Liveness', 'Speechiness', 'Positiveness']
    feature_values = all_time_song[features].mean().values

    fig_radar = go.Figure(data=[
        go.Scatterpolar(
            r=feature_values,
            theta=features,
            fill='toself',
            name=selected_track
        )
    ])
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        showlegend=False,
        title="Audio Features"
    )
    st.plotly_chart(fig_radar)

    # Feature tags
    tags = [f"{feature} = {round(value, 3)}" for feature, value in zip(features, feature_values)]
    st.markdown("**Feature Values:** " + " | ".join(tags))

    # Trend over Time
    st.subheader("📈 Popularity Trend Over Time")
    trend_df = df[(df['Track Name'] == selected_track)]
    if selected_country != "All":
        trend_df = trend_df[trend_df['Country'] == selected_country]
    trend_df = trend_df.sort_values('Weeknum')
    fig_trend = px.line(trend_df, x='Weeknum', y='Popularity', title=f'Popularity Trend of {selected_track}')
    st.plotly_chart(fig_trend)

else:
    st.subheader("🎵 Music Details (Averages)")
    st.markdown("Showing average audio features for selected filters.")

    features = ['Danceability', 'Acousticness', 'Energy', 'Instrumentalness', 'Liveness', 'Speechiness', 'Positiveness']
    feature_values = filtered_df[features].mean().values

    fig_radar = go.Figure(data=[
        go.Scatterpolar(
            r=feature_values,
            theta=features,
            fill='toself',
            name="Average"
        )
    ])
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        showlegend=False,
        title="Average Audio Features"
    )
    st.plotly_chart(fig_radar)

    # Feature tags
    tags = [f"{feature} = {round(value, 3)}" for feature, value in zip(features, feature_values)]
    st.markdown("**Feature Averages:** " + " | ".join(tags))

# --- Raw Data ---
with st.expander("🔍 See raw data"):
    st.dataframe(filtered_df, use_container_width=True)
