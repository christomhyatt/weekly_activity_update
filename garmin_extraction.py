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

## Dates for API call
start_date = st.date_input("Select start date", date('2024-01-01'))
today = date.today()

## API call and creatre data frame
activities_raw = garmin.get_activities_by_date(start_date, today)
activities_df = pd.DataFrame(activities_raw)

## Extract relevant columns and data transformation of DF
activities_mins = activities_df[['activityType', 'duration', 'startTimeLocal']]
activities_mins['activityTypeKey'] = activities_mins['activityType'].apply(lambda x: x.get('typeKey'))
activities_mins['durationMinutes'] = (activities_mins['duration'] % 3600) // 60
activities_mins = activities_mins.drop(columns = ['activityType', 'duration'])
activities_mins['startTimeLocal'] = pd.to_datetime(activities_mins['startTimeLocal'])
activities_mins.set_index('startTimeLocal', inplace=True)

# Convert the duration (seconds) into minutes
# activities_mins.insert(1, 'activityTypeKey', activities_mins.pop('activityTypeKey')) 

# Create weekly column
weekly_duration = activities_mins.groupby('activityTypeKey')['durationMinutes'].resample('W').sum()
weekly_duration = weekly_duration.unstack(level=0).fillna(0)

# Display raw data and transformed data
st.write("Raw Activities Data", activities_df.head())
st.write("Weekly Summed Duration by Activity Type", weekly_duration.head())

# Altair Bar Chart
chart = alt.Chart(weekly_duration).mark_bar().encode(
    x='startTimeLocal:T',
    y='Duration (min):Q',
    color='Activity Type:N'
).properties(title="Weekly Activity Duration")

st.altair_chart(chart, use_container_width=True)


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
# st.dataframe(weekly_duration)


# # Plot
# sns.barplot(data=activities_mins_summed, x='activityTypeKey', y='durationMinutes')
# plt.xticks(rotation=45)
# plt.show()

## Get Calories
# activities_calories = activities_df[['activityName','autoCalcCalories']]
# print(activities_calories[activities_calories['autoCalcCalories'] == True])
