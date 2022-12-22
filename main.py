import os
import openai
import sqlite3
import requests
import speech_recognition as sr
from pydub import AudioSegment
from dotenv import load_dotenv
from gtts import gTTS
from urllib.parse import quote
from flask import Flask, request, abort, send_file
from flask_apscheduler import APScheduler
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextSendMessage, AudioMessage, AudioSendMessage
from deepface import DeepFace

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
line_bot_api = LineBotApi(os.getenv("TOKEN"))
handler = WebhookHandler(os.getenv("SECRET"))
ngrok_url = os.getenv("NGROK_URL")

app = Flask(__name__)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


@scheduler.task('cron', id='do_job', day='*', hour='8')
def job():
    broadcast(None, "早安你好")


@app.route("/")
def main():
    return ""


@app.route("/tts/<path:path>")
def tts(path):
    print("path : tts/"+path+".mp3")
    return send_file("tts/" + path + ".mp3", as_attachment=True)


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    # print("body : \n",body)#body2 = re.split('"', body)#print("body2 : \n",body2)
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid Signature Error")
        abort(400)
    return 'OK'


floor = 0
# message = TextMessage


@handler.add(MessageEvent)
def handle_message(event):
  global floor
  UserId = event.source.user_id
  #10=聊天,11=語音轉文字,12=天氣預報
  if (event.message.type == "image"):
    if(floor==13):deepface_f(event)
    else:
        line_reply = '走錯了吧。。。'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=line_reply))
  elif(event.message.type == "text"):
    mtext = event.message.text
    print("mtext : %s\nfloor : %s"%(mtext,floor))
    Input_text(event,mtext)
  elif(event.message.type == "audio"):
    UserID = event.source.user_id
    path ='audio/'+ UserID + ".wav"
    #print('path = ',path)
    audio_content = line_bot_api.get_message_content(event.message.id)
    with open(path, 'wb') as fd:
        for chunk in audio_content.iter_content():
            fd.write(chunk)

    #轉檔
    
    #AudioSegment.converter = 'C:\\Users\\ACER\\Downloads\\ffmpeg\\ffmpeg\\bin\\ffmpeg.exe'
    sound = AudioSegment.from_file_using_temporary_files(path)
    path = os.path.splitext(path)[0] + '.wav'
    sound.export(path, format="wav")
    

    #辨識
    r = sr.Recognizer()
    file_audio = sr.AudioFile(path)

    with file_audio as source:
        audio_text = r.record(source)
    text = r.recognize_google(audio_text, language='zh-Hant')
    line_reply = text
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=line_reply))
    
def Input_text(event,mtext):
    global floor
    print("mtext : %s\nfloor : %s"%(mtext,floor))
    if(mtext == "End"):
      floor = 0
      line_reply = '886~'
      line_bot_api.reply_message(event.reply_token, TextSendMessage(text=line_reply)) 
    elif(floor==0 and (mtext =='start'or mtext=='Start')):
        start(event)
    elif(floor==0 and (mtext =='broadcast'or mtext=='Broadcast')):
        broadcast(event, "廣播測試")
    elif (floor==1):
      try:
        if(int(mtext)==1):
          floor=10
          line_reply = '進入聊天模式。。。(請開始聊天,輸入"Quit"退出)'
          line_bot_api.reply_message(event.reply_token, TextSendMessage(text=line_reply))
        elif(int(mtext)==2):
          floor=11
          line_reply = '進入文字轉語音模式。。。(輸入"Quit"退出)'
          line_bot_api.reply_message(event.reply_token, TextSendMessage(text=line_reply))
        elif(int(mtext)==3):
          floor=12
          climate(event)
        elif(int(mtext)==4):
          floor=13
          line_reply='進入圖片檢測模式(輸入"Quit"退出)'
          line_bot_api.reply_message(event.reply_token, TextSendMessage(text=line_reply))
        else:
          line_reply = "Invalid input try again!"
          line_bot_api.reply_message(event.reply_token, TextSendMessage(text=line_reply))
    #profile = line_bot_api.get_profile(UserId)#print("UserId : \n",UserId)#print("profile : \n",profile)
      except:
        start(event)
    elif (floor==10):conversation(event)
    elif (floor==11):convert_T_to_A(event)
    elif (floor==12 or floor==22):climate(event)
    elif(floor==13):
        if(mtext == "Quit"):
            floor =1
            print('floor : ',floor)
            line_reply = 'Quit done!'
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=line_reply))
        else:
            line_reply = '請傳送圖片(輸入"Quit"退出)'
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=line_reply))
    else:
      line_reply='輸入 "start" 或 "Start" 來使用哦～ '
      line_bot_api.reply_message(event.reply_token, TextSendMessage(text=line_reply))

def broadcast(event, string):
  conn = sqlite3.connect("line.db")
  cursor = conn.cursor()
  cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id TEXT)")

  if event is not None:
    data = cursor.execute("SELECT rowid FROM users WHERE user_id = ?", (event.source.user_id,)).fetchall()
    if len(data) == 0:
      cursor.execute("INSERT INTO users (user_id) VALUES (?)", (event.source.user_id,))

  conn.commit()

  rows = cursor.execute("SELECT * FROM users").fetchall()
  for row in rows:
    line_bot_api.push_message(row[0], TextSendMessage(text=string))

  conn.close()

def start(event):
  global floor
  Fs = ['聊天','文字轉語音','天氣預報','圖片人物分析']
  line_reply = '你想幹嘛呢 : '
  for i in range(len(Fs)):line_reply += f'\n{i+1}.{Fs[i]}'
  floor = 1
  line_reply+= '\n(輸入"End"結束)'
  line_bot_api.reply_message(event.reply_token, TextSendMessage(text=line_reply))
def conversation(event):
  global floor
  msg = event.message.text
  print("mtext : %s\nfloor : %s"%(msg,floor))
  if(msg == 'Quit'):
    floor = 1
    line_reply = 'Quit done!'
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=line_reply))
  else:
    response = openai.Completion.create(model="text-davinci-003",
                                      prompt="Q: " + event.message.text +
                                      "\nA:",
                                      max_tokens=4000,
                                      temperature=0,
                                      top_p=1,
                                      frequency_penalty=0.0,
                                      presence_penalty=0.0,
                                      stop=["\n"])
  
    line_bot_api.reply_message(
      event.reply_token, TextSendMessage(text=response["choices"][0]["text"]))
def convert_T_to_A(event):
  global floor
  global ngrok_url
  msg = event.message.text
  print("mtext : %s\nfloor : %s"%(msg,floor))
  if(msg == 'Quit'):
    floor=1
    line_reply = 'Quit done!'
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=line_reply))
  else:
    tts = gTTS(text=msg, lang="zh-tw")
    tts.save("tts/" + msg + ".mp3")
    line_bot_api.reply_message(
      event.reply_token,
      AudioSendMessage(
        original_content_url=ngrok_url+"/tts/"+
        quote(msg),
        duration=2000))
def climate(event):
  global floor
  if (floor==12):
    mtext = event.message.text
    print("mtext : %s\nfloor : %s"%(mtext,floor))
    #if (mtext == 'climate' or mtext=='Climate'):
    climate_data = Climate()#print("Climate locations : \n",climate_data['Locations'])
    line_reply=''
    for i in range(len(climate_data["Locations"])):
      line_reply+=f'{i+1}.{climate_data["Locations"][i]}\n'
    line_reply+='(Type "Quit" to exit!)'
    floor = 22
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=line_reply))
    #else:
    # line_reply = 'Enter "Climate" or "climate" to start~'
    # line_bot_api.reply_message(event.reply_token, TextSendMessage(text=line_reply))
  elif (floor==22):
    mtext = event.message.text
    print("mtext : %s\nfloor : %s"%(mtext,floor))
    line_reply=''
    if mtext == 'quit' or mtext =='Quit':
      floor = 1
      print('floor : ',floor)
      line_reply = 'Quit done!'
      line_bot_api.reply_message(event.reply_token, TextSendMessage(text=line_reply))
    #try:
    elif (mtext.isdigit() and int(mtext)>=1 and int(mtext)<=25):
      climate_data = Climate()
      tmp = int(mtext) - 1
      tmp_location = climate_data['Locations'][tmp]
      line_reply += f'{climate_data["Locations"][tmp]}'
      for i in range(7):
        temp_data = climate_data[tmp_location]['Weather'][i]+"|氣溫:"+ climate_data[tmp_location]['MinTemperature'][i] +"~"+ climate_data[tmp_location]['MaxTemperature'][i]+"°C"
        line_reply+=f'\n第{i}天:{temp_data}'
      line_bot_api.reply_message(event.reply_token, TextSendMessage(text=line_reply))
    else: 
      line_reply = "Invalid input try again!!!"
      line_bot_api.reply_message(event.reply_token, TextSendMessage(text=line_reply))
  """except:
    line_reply='Invalid input try again!!!'
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=line_reply))"""
def data():
  import sqlite3
  con=sqlite3.connect(r'data.db')
  cur = con.cursor()
  cur.execute("CREATE TABLE IF NOT EXISTS movie (title, year, score)")
  cur.execute("INSERT INTO movie VALUES('Monty Python and the Holy Grail', 1975, 8.2),('And Now for Something Completely Different', 1971, 7.5)")
  con.commit()
  cur.execute('SELECT * FROM movie')
  test = cur.fetchall()
  print("testdb : ",test)
  return test
def deepface_f(event):
  UserId = event.source.user_id
  if (event.message.type == "image"):
    #test = os.getcwd()
    #print('test = ',test)
    #print('Image event')
    SendImage = line_bot_api.get_message_content(event.message.id)
    #print('test = ',test)
    path ='Images/'+ UserId + '.png'
    #print('path = ',path)

    with open(path, 'wb') as fd:
        for chenk in SendImage.iter_content():
            fd.write(chenk)

    face_analysis = DeepFace.analyze(img_path=path)
    print('Face Analysis',face_analysis)
    emotion = face_analysis["dominant_emotion"]
    gender = face_analysis["gender"]
    age = face_analysis["age"]
    race = face_analysis["dominant_race"]
    print('Done analyzed')
    line_reply =''
    line_reply +=f'Emotion : {emotion}\nGender : {gender}\nAge : {age}\nRace : {race}'
    print('line reply : ',line_reply)
    line_bot_api.reply_message(event.reply_token,TextSendMessage(text=line_reply))
def Climate():
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
def images_open(event,url):
  line_reply= url
  line_bot_api.reply_message(event.reply_token, TextSendMessage(text=line_reply))
  """from PIL import Image
  print("URL : ",url)
  im = Image.open(url) 
  im.show() 
  print(im)
  face_analysis = DeepFace.analyze(img_path=url)
  emotion = face_analysis["dominant_emotion"]
  gender = face_analysis["gender"]
  age = face_analysis["age"]
  race = face_analysis["dominant_race"]
  
  line_bot_api.reply_message(
    event.reply_token,
    TextSendMessage(text="Emotion: " + emotion + "\n" + "Gender: " + gender +
                    "\n" + "Age: " + age + "\n" + "Race: " + race + "\n"))"""

if __name__ == '__main__':
    app.run()

# pyinstaller main.py -F --paths="/home/runner/Chap10/venv/lib/python3.8/site-packages/cv2"
