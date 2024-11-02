import os
import garminconnect
import pandas as pd
import altair as alt
import streamlit as st
from datetime import date

## Garmin login + credentials; hide before publishing 
email = st.secrets["GARMIN_EMAIL"]
password = st.secrets["GARMIN_PASSWORD"]
garmin = garminconnect.Garmin(email, password)
garmin.login()
# name = garmin.display_name

# ## Store session information
# GARTH_HOME = os.getenv("GARTH_HOME", "~/.garth")
# garmin.garth.dump(GARTH_HOME)

st.title("Weekly Activity Duration")

## Dates for API call
start_date = st.date_input("Select start date", date(2024,1,1))
today = date.today()

## API call and creatre data frame
activities_raw = garmin.get_activities_by_date(start_date, today)
activities_df = pd.DataFrame(activities_raw)

## Extract relevant columns and data transformation of DF
activities_df = activities_df[['activityType', 'distance', 'duration', 'startTimeLocal']]
activities_df['activityTypeKey'] = activities_df['activityType'].apply(lambda x: x.get('typeKey'))
activities_df['durationMinutes'] = (activities_df['duration'] % 3600) // 60
activities_df['distanceMiles'] = (activities_df['distance'] / 1609.344).round(1)
activities_df = activities_df.drop(columns = ['activityType', 'distance', 'duration'])
activities_df['startTimeLocal'] = pd.to_datetime(activities_df['startTimeLocal'])

activities_df['Year'] = activities_df['startTimeLocal'].dt.isocalendar().year
activities_df['Week'] = activities_df['startTimeLocal'].dt.isocalendar().week
activities_df['YearWeek'] = activities_df['Year'].astype(str) + '-W' + activities_df['Week'].astype(str).str.zfill(2)


# Create weekly summary with separate columns for each activity type and metric
weekly_duration = pd.pivot_table(
    activities_df,
    values='durationMinutes',
    index='YearWeek',
    columns='activityTypeKey',
    aggfunc='sum',
    fill_value=0
).add_suffix('_duration')

weekly_distance = pd.pivot_table(
    activities_df,
    values='distanceMiles',
    index='YearWeek',
    columns='activityTypeKey',
    aggfunc='sum',
    fill_value=0
).add_suffix('_distance')

# Combine the duration and distance DataFrames
weekly_summary = pd.concat([weekly_duration, weekly_distance], axis=1)
weekly_summary = weekly_summary.fillna(0)
st.write(weekly_summary.head())

# Create weekly column
# weekly_summary = activities_df.groupby('activityTypeKey').resample('W').sum()
# weekly_summary = weekly_summary.unstack(level=0).fillna(0)
# weekly_summary = weekly_summary.drop(colunms = ['activityTypeKey'])

# Clean up format of table
# weekly_summary.index = weekly_summary.index.strftime('%Y-%m-%d')

# Display transformed data
# st.write("Weekly Summed Duration by Activity Type", weekly_summary.head())

# Altair Bar Chart
# chart = alt.Chart(weekly_summary).mark_bar().encode(
#     x='startTimeLocal:T',
#     y='Duration (min):Q',
#     color='Activity Type:N'
# ).properties(title="Weekly Activity Duration")

# alt.Chart(weekly_summary)

# st.altair_chart(chart, use_container_width=True)

# st.set_page_config{
#     page_title = "Weekly Garmin Report"
#     page_icon = "🤘"
#     layout = "wide"
#     initial_sidebar = "expanded"
# }

alt.themes.enable('dark')

# Set up the Streamlit app 
# st.title("Weekly Activity Duration")
# st.write("This table displays the weekly summed duration (in minutes) for each activity type.")

# # Display the data as table
# st.dataframe(weekly_summary)


# # Plot
# sns.barplot(data=activities_df_summed, x='activityTypeKey', y='durationMinutes')
# plt.xticks(rotation=45)
# plt.show()

## Get Calories
# activities_calories = activities_df[['activityName','autoCalcCalories']]
# print(activities_calories[activities_calories['autoCalcCalories'] == True])
