import os
import openai
import sqlite3
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
from Climate import Climate_

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
line_bot_api = LineBotApi(os.getenv("TOKEN"))
handler = WebhookHandler(os.getenv("SECRET"))
ngrok_url = os.getenv("NGROK_URL")

USER_Floor = {}

app = Flask(__name__)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


@scheduler.task('cron', id='do_job', day='*', hour='8')
def job():
    broadcast(None, "早安你好")
    Today_climate = broadclimate()
    if(int(Today_climate[1]) >= 8 and int(Today_climate[1]) <= 23):
        broadcast(None, f'今天{Today_climate[0]},記得帶傘哦~')
    if(int(Today_climate[2]) <= 20):
        broadcast(
            None, f'今天{Today_climate[0]}最低溫為 {Today_climate[2]}°C,記得穿多一點~')


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

# message = TextMessage


@handler.add(MessageEvent)
def handle_message(event):
    global USER_Floor
    UserId = event.source.user_id
    try:
        USER_Floor[UserId]
    except KeyError:
        USER_Floor[UserId] = 0
    # 10=聊天,11=語音轉文字,12=天氣預報,13=圖片檢測
    if (event.message.type == "image"):
        if(int(USER_Floor[UserId]) == 13):
            deepface_f(event)
        else:
            line_reply = '走錯了吧。。。'
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=line_reply))
    elif(event.message.type == "text"):
        mtext = event.message.text
        print("mtext : %s\nUid : %s\nfloor : %s" %
              (mtext, UserId, USER_Floor[UserId]))
        Input_text(event, mtext)
    elif(event.message.type == "audio"):
        UserID = event.source.user_id
        path = 'audio/' + UserID + ".wav"
        #print('path = ',path)
        audio_content = line_bot_api.get_message_content(event.message.id)
        with open(path, 'wb') as fd:
            for chunk in audio_content.iter_content():
                fd.write(chunk)
        # 轉檔
        #AudioSegment.converter = 'C:\\Users\\ACER\\Downloads\\ffmpeg\\ffmpeg\\bin\\ffmpeg.exe'
        sound = AudioSegment.from_file_using_temporary_files(path)
        path = os.path.splitext(path)[0] + '.wav'
        sound.export(path, format="wav")
        # 辨識
        r = sr.Recognizer()
        file_audio = sr.AudioFile(path)

        with file_audio as source:
            audio_text = r.record(source)
        text = r.recognize_google(audio_text, language='zh-Hant')
        audiotext = text
        print('audiotext = ', audiotext)
        Input_text(event, audiotext)


def Input_text(event, mtext):
    global USER_Floor
    UserId = event.source.user_id
    print("mtext : %s\nUid : %s\nfloor : %s" %
          (mtext, UserId, USER_Floor[UserId]))
    if(mtext == "End" or mtext == "結束"):
        USER_Floor[UserId] = 0
        line_reply = '886~'
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=line_reply))
    elif(int(USER_Floor[UserId]) == 0 and (mtext == 'start' or mtext == 'Start' or mtext == "開始")):
        start(event)
    elif(int(USER_Floor[UserId]) == 0 and (mtext == 'broadcast' or mtext == 'Broadcast')):
        broadcast(event, "廣播測試")
    elif (int(USER_Floor[UserId]) == 1):
        if mtext.isdigit():
            try:
                if(int(mtext) == 1):
                    USER_Floor[UserId] = 10
                    line_reply = '進入聊天模式。。。(請開始聊天,輸入"Quit"退出)'
                    line_bot_api.reply_message(
                        event.reply_token, TextSendMessage(text=line_reply))
                elif(int(mtext) == 2):
                    USER_Floor[UserId] = 11
                    line_reply = '進入文字轉語音模式。。。(輸入"Quit"退出)'
                    line_bot_api.reply_message(
                        event.reply_token, TextSendMessage(text=line_reply))
                elif(int(mtext) == 3):
                    USER_Floor[UserId] = 12
                    climate(event, mtext)
                elif(int(mtext) == 4):
                    USER_Floor[UserId] = 13
                    line_reply = '進入圖片檢測模式(輸入"Quit"退出)'
                    line_bot_api.reply_message(
                        event.reply_token, TextSendMessage(text=line_reply))
                else:
                    line_reply = "Invalid input try again!"
                    line_bot_api.reply_message(
                        event.reply_token, TextSendMessage(text=line_reply))
        # profile = line_bot_api.get_profile(UserId)#print("UserId : \n",UserId)#print("profile : \n",profile)
            except:
                start(event)
        elif(mtext == "聊天"):
            USER_Floor[UserId] = 10
            line_reply = '進入聊天模式。。。(請開始聊天,輸入"Quit"退出)'
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=line_reply))
        elif(mtext == "文字轉語音"):
            USER_Floor[UserId] = 11
            line_reply = '進入文字轉語音模式。。。(輸入"Quit"退出)'
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=line_reply))
        elif(mtext == "天氣預報"):
            USER_Floor[UserId] = 12
            climate(event, mtext)
        else:
            start(event)

    elif (USER_Floor[UserId] == 10):
        conversation(event,mtext)
    elif (USER_Floor[UserId] == 11):
        convert_T_to_A(event)
    elif (USER_Floor[UserId] == 12 or USER_Floor[UserId] == 22):
        climate(event, mtext)
    elif(USER_Floor[UserId] == 13):
        if(mtext == "Quit"):
            USER_Floor[UserId] = 1
            print('UserId : %s \nfloor : %s' % (UserId, USER_Floor[UserId]))
            line_reply = 'Quit done!'
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=line_reply))
        else:
            line_reply = '請傳送圖片(輸入"Quit"退出)'
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=line_reply))
    else:
        line_reply = '輸入 "start" 或 "Start" 來使用哦～ '
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=line_reply))


def broadclimate():
    CL = Climate_()
    Msg = CL['金門地區']['Code'][0]
    Msg2 = CL['金門地區']['Weather'][0]
    Msg3 = CL['金門地區']['MinTemperature'][0]
    List = []
    List.append(Msg2)
    List.append(Msg)
    List.append(Msg3)
    return List


def broadcast(event, string):
    conn = sqlite3.connect("line.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id TEXT)")

    if event is not None:
        data = cursor.execute(
            "SELECT rowid FROM users WHERE user_id = ?", (event.source.user_id,)).fetchall()
        if len(data) == 0:
            cursor.execute("INSERT INTO users (user_id) VALUES (?)",
                           (event.source.user_id,))

    conn.commit()

    rows = cursor.execute("SELECT * FROM users").fetchall()
    for row in rows:
        line_bot_api.push_message(row[0], TextSendMessage(text=string))

    conn.close()


def start(event):
    global USER_Floor
    UserId = event.source.user_id
    Fs = ['聊天', '文字轉語音', '天氣預報', '圖片人物分析']
    line_reply = '你想幹嘛呢 : '
    for i in range(len(Fs)):
        line_reply += f'\n{i+1}.{Fs[i]}'
    USER_Floor[UserId] = 1
    line_reply += '\n(輸入"End"結束)'
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text=line_reply))


def conversation(event,mtext):
    global USER_Floor
    UserId = event.source.user_id
    #msg = event.message.text
    print("mtext : %s UserId : %s floor : %s" %
          (mtext, UserId, USER_Floor[UserId]))
    if(mtext == 'Quit'):
        USER_Floor[UserId] = 1
        line_reply = 'Quit done!'
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=line_reply))
    else:
        response = openai.Completion.create(model="text-davinci-003",
                                            prompt="Q: " + mtext +
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
    global USER_Floor
    global ngrok_url
    UserId = event.source.user_id
    msg = event.message.text
    print("mtext : %s\nUserId : %s\nfloor : %s" %
          (msg, UserId, USER_Floor[UserId]))
    if(msg == 'Quit'):
        USER_Floor[UserId] = 1
        line_reply = 'Quit done!'
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=line_reply))
    else:
        tts = gTTS(text=msg, lang="zh-tw")
        tts.save("tts/" + msg + ".mp3")
        line_bot_api.reply_message(
            event.reply_token,
            AudioSendMessage(
                original_content_url=ngrok_url+"/tts/" +
                quote(msg),
                duration=2000))


def climate(event, mtext):
    CL = Climate_()
    global USER_Floor
    UserId = event.source.user_id
    if (USER_Floor[UserId] == 12):
        print("mtext : %s\nUserId : %s\nfloor : %s" %
              (mtext, UserId, USER_Floor[UserId]))
        # if (mtext == 'climate' or mtext=='Climate'):
        # print("Climate locations : \n",climate_data['Locations'])
        climate_data = CL
        line_reply = ''
        for i in range(len(climate_data["Locations"])):
            line_reply += f'{i+1}.{climate_data["Locations"][i]}\n'
        line_reply += '(Type "Quit" to exit!)'
        USER_Floor[UserId] = 22
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=line_reply))
        # else:
        # line_reply = 'Enter "Climate" or "climate" to start~'
        # line_bot_api.reply_message(event.reply_token, TextSendMessage(text=line_reply))
    elif (USER_Floor[UserId] == 22):
        print("mtext : %s\nUserId : %s\nfloor : %s" %
              (mtext, UserId, USER_Floor[UserId]))
        line_reply = ''
        climate_data = CL
        if mtext == 'quit' or mtext == 'Quit' or mtext == "退出":
            USER_Floor[UserId] = 1
            print('floor : ', USER_Floor[UserId])
            line_reply = 'Quit done!'
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=line_reply))
        # try:
        elif (mtext.isdigit() and int(mtext) >= 1 and int(mtext) <= 25):
            tmp = int(mtext) - 1
            tmp_location = climate_data['Locations'][tmp]
            line_reply += f'{climate_data["Locations"][tmp]}'
            for i in range(7):
                temp_data = climate_data[tmp_location]['Weather'][i]+"|氣溫:" + \
                    climate_data[tmp_location]['MinTemperature'][i] + "~" + \
                    climate_data[tmp_location]['MaxTemperature'][i]+"°C"
                line_reply += f'\n第{i}天:{temp_data}'
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=line_reply))
        elif(mtext.isdigit() == False):
            #print('climate_data = ',climate_data)
            try:
                tmp_location = mtext
                print('tmp_location', tmp_location)
                line_reply += f'{tmp_location}'
                for i in range(7):
                    temp_data = climate_data[tmp_location]['Weather'][i]+"|氣溫:" + \
                        climate_data[tmp_location]['MinTemperature'][i] + "~" + \
                        climate_data[tmp_location]['MaxTemperature'][i]+"°C"
                    line_reply += f'\n第{i}天:{temp_data}'
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text=line_reply))
            except:
                line_reply = "Invalid input try again!!!"
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text=line_reply))
        else:
            line_reply = "Invalid input try again!!!"
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=line_reply))
    """except:
    line_reply='Invalid input try again!!!'
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=line_reply))"""


def deepface_f(event):
    UserId = event.source.user_id
    if (event.message.type == "image"):
        #test = os.getcwd()
        #print('test = ',test)
        #print('Image event')
        SendImage = line_bot_api.get_message_content(event.message.id)
        #print('test = ',test)
        path = 'Images/' + UserId + '.png'
        #print('path = ',path)

        with open(path, 'wb') as fd:
            for chenk in SendImage.iter_content():
                fd.write(chenk)

        face_analysis = DeepFace.analyze(img_path=path)
        print('Face Analysis', face_analysis)
        emotion = face_analysis["dominant_emotion"]
        gender = face_analysis["gender"]
        age = face_analysis["age"]
        race = face_analysis["dominant_race"]
        print('Done analyzed')
        line_reply = ''
        line_reply += f'Emotion : {emotion}\nGender : {gender}\nAge : {age}\nRace : {race}'
        print('line reply : ', line_reply)
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=line_reply))


if __name__ == '__main__':
    app.run()

# pyinstaller main.py -F --paths="/home/runner/Chap10/venv/lib/python3.8/site-packages/cv2"
