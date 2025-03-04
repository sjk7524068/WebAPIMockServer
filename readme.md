## CODE WITH AI
## powered by ME and GEMINI （主要由我出主意，GEMINI负责实现）

功能：记录并还原chrome浏览器的所有HAR类型【GET、POST。。。。。】的接口，也支持图片下载，其他二进制数据文件暂未测试


#### 怎么捕捉har文件：
1. chrome浏览器打开dev-tool【F12】模式, 打开【Preserve log】,打开【Disable cache】
2. 然后正常浏览，所有数据都采集完后点击下载【xxxx.har】


### 怎么启动服务
1. pip install -r requirements.txt\
2. python har_server.py





