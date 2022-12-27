# nonebot_plugin_imgexploration with Rules
Google、Yandx和基于PicImageSearch的saucenao、ascii2d搜图  
需要能稳定访问Google等网站的代理  
## 一.安装
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
### 3.依赖  (使用pip安装无需以下步骤)
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

## 二.配置  
### 1.env中的配置
```
proxy_port=xxxx  #代理端口号
saucenao_apikey=xxxxx  #saucenao apikey
group_on=[123456]  #开启搜图的群号
guild_on=[123456]  #开启搜图的频道号
sub_channel_on=[123456]  #开启搜图的子频道号
blacklist=[123456]  #黑名单qq号
private_on=[123456]  #开启私聊搜图的qq号
```  
### 2.charge.json中的配置
```  
{
    "群号":次数,
    "qq号":次数,
    "子频道号":次数
}
```  
## 三.使用  
### 
```
/搜图
/搜图 <图片>
```  
