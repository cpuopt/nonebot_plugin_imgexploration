# nonebot_plugin_imgexploration 
Google、Yandx和基于PicImageSearch的saucenao、ascii2d搜图  
需要能稳定访问Google等网站的代理  
## 一.安装
### 1.下载
```
pip install nonebot-plugin-imgexploration
```
然后在bot.py中添加(注意顺序)
```
nonebot.load_plugin('nonebot_plugin_guild_patch')
nonebot.load_plugin('nonebot_plugin_imgexploration')
```
或其他任意加载方式
### 2.依赖  (使用pip安装无需以下步骤)
```
pip install -r requirements.txt
```
go-cqhttp 频道支持适配补丁`nonebot-plugin-guild-patch`  
安装命令
```
pip install nonebot-plugin-guild-patch
```
在bot.py中添加
```
nonebot.load_plugin('nonebot_plugin_guild_patch')
```
### 3.需要字体    
```
HarmonyOS_Sans_SC_Regular.ttf  
HarmonyOS_Sans_SC_Bold.ttf  
HarmonyOS_Sans_SC_Light.ttf
```
https://developer.harmonyos.com/cn/docs/design/des-guides/font-0000001157868583
## 二.配置  
### 1.env中的配置
```
proxy_port=xxxx  #代理端口号
saucenao_apikey=xxxxx  #saucenao apikey
```  
