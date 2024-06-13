# MagicMirror

資工二 黃偉祥 111010550  
資工二 李易 111010512  
資工二 陳先正 111010540  
資工二 阮銘福 111010552

## 使用說明

### 第一步：導入模組

在該專案下打開終端機，並輸入 `pip install -r requirements.txt` 。

### 第二步：設定環境

在該專案下新增 `.env` 文件，並輸入相關變數。格式如下：
```
OPENAI_API_KEY = "使用者 OpenAI API key"
SECRET = "使用者 Channel secret"
TOKEN = "使用者 Channel access token"
NGROK_URL = "使用者 ngrok forwarding URL"
```

### 第三步：啟動專案

1. 到 `ngrok` [官網](https://ngrok.com/download)
  - `Windows` : 下載安裝檔，並在解壓縮後將其執行檔放置到該專案下。  
  - `Mac` : 有 brew 的話在終端機輸入 `brew install ngrok/ngrok/ngrok`。
2. 放置完畢後，在該專案下打開執行檔，並輸入 `ngrok http 5000` 。  
3. 輸入完畢後，複製其生成的 `HTTPS` 位址，並黏貼到 `.env` 及 `LINE Bot Webhook URL` 上。  
4. 黏貼完畢後，在該專案下打開終端機，並輸入 `python main.py` 。

## 備註
### 安裝 `FFmpeg`
- 在 `Windows` 底下,相關教學請看[這裡](https://www.youtube.com/watch?v=IguLPa8aV-w)。
- 在 `Mac` 底下,相關教學請看[這裡](https://youtu.be/zl4vo0dhLRk)。

