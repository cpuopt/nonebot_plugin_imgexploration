# nonebot_plugin_imgexploration 
Google、Yandx和基于PicImageSearch的saucenao、ascii2d搜图  
需要能稳定访问Google等网站的代理  
## 一.**安装**
### 1.安装
```
pip install nonebot-plugin-imgexploration
```
然后在bot.py中添加(注意顺序)
```
nonebot.load_plugin('nonebot_plugin_guild_patch')
nonebot.load_plugin('nonebot_plugin_imgexploration')
```
或其他任意加载方式
### 2.需要字体    
```
HarmonyOS_Sans_SC_Regular.ttf  
HarmonyOS_Sans_SC_Bold.ttf  
HarmonyOS_Sans_SC_Light.ttf
```
https://developer.harmonyos.com/cn/docs/design/des-guides/font-0000001157868583   
安装到系统字体即可
### 3.依赖  (使用pip安装无需以下步骤)
```
pip install -r requirements.txt
```
go-cqhttp 频道支持适配补丁`nonebot-plugin-guild-patch`  
```
pip install nonebot-plugin-guild-patch
```
在加载本插件前添加
```
nonebot.load_plugin('nonebot_plugin_guild_patch')
```

## 二.**配置**  
### 1.env中的配置
```
proxy_port=xxxx  #代理端口号
saucenao_apikey=xxxxx  #saucenao apikey
SESSION_EXPIRE_TIMEOUT=180 #等待用户回复的超时时间(可选) https://v2.nonebot.dev/docs/api/config#Config-session_expire_timeout
```  
## 三.**使用**  
### 
```
/搜图
/搜图 <图片>
```  
### **使用示例**   

<div align=center>
    <img decoding="async" align="middle" src="https://p.inari.site/usr/369/63b6cfe0cd8a8.jpg" width="80%">
</div>

### 搜图结果

<div align=center>
    <img decoding="async" align="middle" src="https://p.inari.site/usr/369/63b6cd6f24abc.jpg" height="1280px">
</div>