import os
import garminconnect
import pandas as pd
import altair as alt
import streamlit as st
from datetime import date, timedelta

# Set up the Streamlit app 
st.set_page_config(
    page_title = "Weekly Garmin Report",
    page_icon = "🤘",
    layout = "wide",
    menu_items = {
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)
st.title("Weekly Garmin Report")
alt.themes.enable('dark')

## Garmin login + credentials; hide before publishing 
email = st.secrets["GARMIN_EMAIL"]
password = st.secrets["GARMIN_PASSWORD"]
garmin = garminconnect.Garmin(email, password)
garmin.login()
# name = garmin.display_name

# ## Store session information
# GARTH_HOME = os.getenv("GARTH_HOME", "~/.garth")
# garmin.garth.dump(GARTH_HOME)

## Dates for API call
today = date.today()
with st.container():
    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start Date", date(2024,1,1))
    end_date = col2.date_input("End Date", today)

## API call and creatre data frame
activities_raw = garmin.get_activities_by_date(start_date, end_date)
activities_df = pd.DataFrame(activities_raw)
# st.write("Raw Data: ", activities_df.head())

## Extract relevant columns and data transformation of DF
activities_df = activities_df[['activityType', 'distance', 'duration', 'calories', 'startTimeLocal']]
activities_df['activityTypeKey'] = activities_df['activityType'].apply(lambda x: x.get('typeKey'))
activities_df['durationMinutes'] = (activities_df['duration'] % 3600) // 60
activities_df['distanceMiles'] = (activities_df['distance'] / 1609.344).round(1)
activities_df = activities_df.drop(columns = ['activityType', 'distance', 'duration'])
activities_df['startTimeLocal'] = pd.to_datetime(activities_df['startTimeLocal'])

activities_df['Year'] = activities_df['startTimeLocal'].dt.isocalendar().year
activities_df['Week'] = activities_df['startTimeLocal'].dt.isocalendar().week
activities_df['YearWeek'] = activities_df['Year'].astype(str) + '-W' + activities_df['Week'].astype(str).str.zfill(2)

# Dictionary for activity type name mapping
activity_name_mapping = {
    'backcountry_skiing': 'BC Ski',
    'resort_skiing': 'Resort Ski',
    'walking': 'Walk',
    'cycling': 'Road Bike',
    'hiking': 'Hike',
    'running': 'City Run',
    'multi_sport': 'MURPH',
    'trail_running': 'Trail Run',
}

# Map the activity types to new names
activities_df['activityTypeKey'] = activities_df['activityTypeKey'].map(activity_name_mapping).fillna(activities_df['activityTypeKey'])

# Create weekly summary with separate columns for each activity type and metric
weekly_duration = pd.pivot_table(
    activities_df,
    values='durationMinutes',
    index='YearWeek',
    columns='activityTypeKey',
    aggfunc='sum',
    fill_value=0
).add_suffix(' (mins)')

weekly_distance = pd.pivot_table(
    activities_df,
    values='distanceMiles',
    index='YearWeek',
    columns='activityTypeKey',
    aggfunc='sum',
    fill_value=0
)

# Combine the duration and distance DataFrames
weekly_summary = pd.concat([weekly_duration, weekly_distance], axis=1)
weekly_summary = weekly_summary.fillna(0)

## Distance Chart
# Reset index to make YearWeek a column
weekly_distance_reset = weekly_distance.reset_index()

# Melt pivots into dataframe for Altair
melted_df = pd.melt(
    weekly_distance_reset, 
    id_vars=['YearWeek'],
    var_name='Activity',
    value_name='Distance'
)

# Distance Line chart
distance_chart = alt.Chart(melted_df).mark_line(point=True).encode(
    x=alt.X('YearWeek:N', title='Week', axis=alt.Axis(labelAngle=-45)),
    y=alt.Y('Distance:Q', title='Distance (miles)'),
    color=alt.Color('Activity:N', title='Activity Type'),
    tooltip=['YearWeek', 'Activity', 'Distance']
).properties(
    width=800,
    height=400,
    title='Weekly Activity Distance'
).interactive()

## Calories Chart
# DF for only Calories data
weekly_calories = activities_df[['YearWeek', 'activityTypeKey', 'calories']]

# Line chart
calories_chart = alt.Chart(weekly_calories).mark_bar().encode(
    x=alt.X('YearWeek:N', title='Week', axis=alt.Axis(labelAngle=-45)),
    y=alt.Y('calories:Q', title='Calories Burned'),
    color=alt.Color('activityTypeKey:N', title='Activity Type'),
    tooltip=['YearWeek', 'activityTypeKey', 'calories']
).properties(
    width=800,
    height=400,
    title='Weekly Calories Burned by Activity'
).interactive()

## SUM of miles for the week 
with st.container(border=True):
    current_week = today.strftime('%Y-W%W')
    if current_week in weekly_distance.index:
        current_week_total = weekly_distance.loc[current_week].sum().sum()
        st.write(f"Miles this week: {round(current_week_total, 2)}.")
    else:
        previous_week = (today - timedelta(days=7)).strftime('%Y-W%W')
        current_week_total = weekly_distance.loc[previous_week].sum().sum()
        st.write(f"No miles this week. Last week's miles: {round(current_week_total, 2)}.")
    st.write(f"Last Weeks Total Miles: {round(weekly_distance.loc[(today - timedelta(days=7)).strftime('%Y-W%W')].sum().sum(), 2)}.")

# Display the charts
col3, col4 = st.columns([3,4])
with col3:
    st.altair_chart(distance_chart, use_container_width=True)
with col4:
    st.altair_chart(calories_chart, use_container_width=True)

## Display Table for Duration / Distance of Activities by Week
st.write("Weekly Summed Duration by Activity Type", weekly_summary)