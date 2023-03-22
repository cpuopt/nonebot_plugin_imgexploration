<div align="center">
<a href="https://v2.nonebot.dev/"><img src="https://v2.nonebot.dev/logo.png" width="200" height="200" alt="nonebot"></a>

# nonebot_plugin_imgexploration 

_✨ [Nonebot2](https://github.com/nonebot/nonebot2) 插件，Google、Yandx和基于PicImageSearch的saucenao、ascii2d搜图  ✨_



</div> 

**需要能稳定访问Google等网站的代理**  
## 一.**安装**
### 1.使用nb-cli安装
依次执行
```
nb plugin install nonebot_plugin_guild_patch
```
```
nb plugin install nonebot-plugin-imgexploration
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

### 3.依赖  (nb-cli或pip安装无需配置依赖)
<details>
<summary>展开/收起</summary>

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
</details>

## 二.**配置**  
### 1.env中的配置
```
#代理端口号(不使用本地代理可缺省，例如：使用软路由透明代理、程序运行在境外)
proxy_port=xxxx  

#saucenao apikey 在https://saucenao.com/user.php?page=search-api注册获取
saucenao_apikey=xxxxx 

#等待用户回复的超时时间(可选) https://v2.nonebot.dev/docs/api/config#Config-session_expire_timeout
SESSION_EXPIRE_TIMEOUT=180 
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
