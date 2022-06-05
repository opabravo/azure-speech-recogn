# 說明

簡單的語音轉文字CLI工具，使用AZURE語音服務

### 因有人問起，在此聲明: 
* 本專案為用CLI實現使用Azure語音服務功能的POC，供特定人士試用後決定是否採用，再把模組包裝成API server or wrapper供其他專案更輕易的調用

* 並非是為抄襲而成立的專案(說明裡已有Refer主要程式碼來原處)，放上Github僅供學術性質參考

### 已包裝程式下載

 [按此下載](https://github.com/opabravo/azure-speech-recogn/releases/download/1.1/vtt.exe)

# 開發環境

 * python 3.10

`pip install -r requirements.txt`

# Compile
 * 引入Azure語音服務套件所需的DLL
 
```pyinstaller main.spec```

# Refers
 * SDK Portal For 各程式語言開發者 :

[github.com/Azure-Samples/cognitive-services-speech-sdk/tree/master/quickstart](https://github.com/Azure-Samples/cognitive-services-speech-sdk/tree/master/quickstart)