import requests
import argparse
import datetime


parser = argparse.ArgumentParser()
parser.add_argument('--latitude', type=float, default=0)
parser.add_argument('--longitude', type=float, default=0)
args = parser.parse_args()

def weather(latitude, longitude):
  current_datetime = datetime.datetime.now()
  start_datetime = current_datetime.strftime("%Y-%m-%dT%H:00")
  end_datetime = current_datetime.strftime("%Y-%m-%dT23:59")

  response = requests.get("https://api.open-meteo.com/v1/forecast?latitude="+str(latitude)+"&longitude="+str(longitude)+"&hourly=apparent_temperature,rain,showers,wind_speed_180m&wind_speed_unit=mph&start_hour="+start_datetime+"&end_hour="+end_datetime)

  data = response.json()

  if response.status_code != 200:
    return response.text
  
  coldest_temp = min(data['hourly']['apparent_temperature'])
  hottest_temp = max(data['hourly']['apparent_temperature'])

  coldest_hour_index = data['hourly']['apparent_temperature'].index(coldest_temp)

  coldest_hour = data['hourly']['time'][coldest_hour_index]

  coldest_hour_12h = datetime.datetime.strptime(coldest_hour, "%Y-%m-%dT%H:%M").strftime("%l %p")

  hottest_hour_index = data['hourly']['apparent_temperature'].index(hottest_temp)

  hottest_hour_12h = datetime.datetime.strptime(data['hourly']['time'][hottest_hour_index], "%Y-%m-%dT%H:%M").strftime("%l %p")
  
  hours_with_rain = [i for i, x in enumerate(data['hourly']['rain']) if x > 0]

  hours_with_showers = [i for i, x in enumerate(data['hourly']['showers']) if x > 0]

  wind_speed_rating = "calm"

  if max(data['hourly']['wind_speed_180m']) > 10:
    wind_speed_rating = "breezy"
  if max(data['hourly']['wind_speed_180m']) > 20:
    wind_speed_rating = "fairly strong"
  if max(data['hourly']['wind_speed_180m']) > 30:
    wind_speed_rating = "very strong"

  is_hours_with_rain_in_morning = any([i > 0 and i < 12 for i in hours_with_rain])
  is_hours_with_rain_in_afternoon = any([i >= 12 and i < 18 for i in hours_with_rain])
  is_hours_with_rain_in_evening = any([i >= 18 for i in hours_with_rain])

  is_hours_with_showers_in_morning = any([i > 0 and i < 12 for i in hours_with_showers])
  is_hours_with_showers_in_afternoon = any([i >= 12 and i < 18 for i in hours_with_showers])
  is_hours_with_showers_in_evening = any([i >= 18 for i in hours_with_showers])
  
  return_string = "The temperature will range from " + str(round(coldest_temp)) + " celcius to " + str(round(hottest_temp)) + " celcius. It will be windiest at " + datetime.datetime.fromtimestamp(data['hourly']['wind_speed_180m'].index(max(data['hourly']['wind_speed_180m'])) * 3600).strftime("%l %p") + " with a wind speed of " + str(round(max(data['hourly']['wind_speed_180m']))) + " miles per hour, which is " + wind_speed_rating + "."

  if is_hours_with_rain_in_morning | is_hours_with_showers_in_morning:
    return_string += " It will rain this morning."
  if is_hours_with_rain_in_afternoon | is_hours_with_showers_in_afternoon:
    return_string += " It will rain this afternoon."
  if is_hours_with_rain_in_evening | is_hours_with_showers_in_evening:
    return_string += " It will rain this evening."

  return return_string
  
if args.latitude and args.longitude:
  print(weather(args.latitude, args.longitude))
