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
  end_datetime = current_datetime.strftime("%Y-%m-%dT21:00")

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

  return_string = "It will feel coldest at " + coldest_hour_12h + " with a temperature of approximately " + str(round(coldest_temp)) + " celcius. It will feel hottest at " + hottest_hour_12h + " with a temperature of approximately " + str(round(hottest_temp)) + " celcius. It will be windiest at " + datetime.datetime.fromtimestamp(data['hourly']['wind_speed_180m'].index(max(data['hourly']['wind_speed_180m'])) * 3600).strftime("%l %p") + " with a wind speed of " + str(round(max(data['hourly']['wind_speed_180m']))) + " miles per hour, which is " + wind_speed_rating + "."

  if len(hours_with_rain) > 0:
    return_string += " It will rain at " + ", ".join([datetime.datetime.strftime(datetime.datetime.strptime(data['hourly']['time'][i], "%Y-%m-%dT%H:%M"), "%l %p") for i in hours_with_rain]) + "."

  if len(hours_with_showers) > 0:
    return_string += " It will shower at " + ", ".join([datetime.datetime.strftime(datetime.datetime.strptime(data['hourly']['time'][i], "%Y-%m-%dT%H:%M"), "%l %p") for i in hours_with_showers]) + "."

  return return_string
  
if args.latitude and args.longitude:
  print(weather(args.latitude, args.longitude))
