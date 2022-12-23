import requests

def Climate_():
  url = 'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/F-C0032-003?Authorization=CWB-4A7A9103-5DEF-43B3-A60E-2ADA85799195&downloadType=WEB&format=JSON'
  data = requests.get(url) 
  data_json = data.json()   
  location = data_json['cwbopendata']['dataset']['location']
  All_Data={}
  Locations=[]
  for i in location:
      locationName = i['locationName']
      All_Data[locationName]={}
      Locations.append(locationName)
      WeatherElement =i['weatherElement']
      Wx = WeatherElement[0]['time']#{0=Wx,1=MaxT,2=MinT}['time']{0=day_1,6=day_7}
      Weather=[]
      for day in Wx:
          weather=day['parameter']['parameterName']
          Weather.append(weather)
      MaxT = WeatherElement[1]['time']
      MaxTemperature=[]
      for day in MaxT:
          maxt=day['parameter']['parameterName']
          MaxTemperature.append(maxt)
      MinT = WeatherElement[2]['time']
      MinTemperature=[]
      for day in MinT:
          mint=day['parameter']['parameterName']
          MinTemperature.append(mint)
      All_Data[locationName]['Weather']=Weather
      All_Data[locationName]['MaxTemperature']=MaxTemperature
      All_Data[locationName]['MinTemperature']=MinTemperature
  All_Data["Locations"] = Locations#print(All_Data['Locations'])
  return All_Data
