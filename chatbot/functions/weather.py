import requests
import argparse
import datetime

parser = argparse.ArgumentParser()
parser.add_argument('--latitude', type=float, default=0)
parser.add_argument('--longitude', type=float, default=0)
args = parser.parse_args()

def weather(latitude, longitude):
  response = requests.get("https://api.open-meteo.com/v1/forecast?latitude="+str(latitude)+"&longitude="+str(longitude)+"&hourly=apparent_temperature,rain,showers,wind_speed_180m&wind_speed_unit=mph&forecast_days=1")
  data = response.json()
  
  coldest_temp = min(data['hourly']['apparent_temperature'])
  hottest_temp = max(data['hourly']['apparent_temperature'])

  coldest_hour_12h = datetime.datetime.fromtimestamp(data['hourly']['apparent_temperature'].index(coldest_temp) * 3600).strftime("%l %p")
  hottest_hour_12h = datetime.datetime.fromtimestamp(data['hourly']['apparent_temperature'].index(hottest_temp) * 3600).strftime("%l %p")
  
  hours_with_rain = [i for i, x in enumerate(data['hourly']['rain']) if x > 0]

  hours_with_showers = [i for i, x in enumerate(data['hourly']['showers']) if x > 0]

  wind_speed_rating = "calm"

  if max(data['hourly']['wind_speed_180m']) > 10:
    wind_speed_rating = "breezy"
  if max(data['hourly']['wind_speed_180m']) > 20:
    wind_speed_rating = "fairly strong"
  if max(data['hourly']['wind_speed_180m']) > 30:
    wind_speed_rating = "very strong"

  return_string = "It will feel coldest at " + coldest_hour_12h + " with a temperature of approximately " + str(coldest_temp) + " celcius. It will feel hottest at " + hottest_hour_12h + " with a temperature of approximately " + str(hottest_temp) + " celcius. It will be windiest at " + datetime.datetime.fromtimestamp(data['hourly']['wind_speed_180m'].index(max(data['hourly']['wind_speed_180m'])) * 3600).strftime("%l %p") + " with a wind speed of " + str(max(data['hourly']['wind_speed_180m'])) + " mph, which is " + wind_speed_rating + "."

  if len(hours_with_rain) > 0:
    return_string += " It will rain at " + ", ".join([datetime.datetime.fromtimestamp(i * 3600).strftime("%l %p") for i in hours_with_rain]) + "."

  if len(hours_with_showers) > 0:
    return_string += " It will shower at " + ", ".join([datetime.datetime.fromtimestamp(i * 3600).strftime("%l %p") for i in hours_with_showers]) + "."

  return return_string
  
if args.latitude and args.longitude:
  print(weather(args.latitude, args.longitude))
