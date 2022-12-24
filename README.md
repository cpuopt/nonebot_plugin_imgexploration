# nonebot_plugin_imgsearch  
## 一.安装
### 1.下载
将`nonebot_plugin_imgsearch`文件夹放置于 `bot根目录/plugins/` 下  
然后在bot.py中添加
```
nonebot.load_plugins('./plugins/')
```
或其他任意加载方式
### 2.依赖
```
pip install -r requirements.txt
```

## 二.配置  
### 1.env中的配置
```
group_on=[123456,321654]  #开启搜图功能的群号
guild_on=[123456789,987654321]  #开启搜图功能的频道号
sub_channel_on=[1234568,6543216]  #开启搜图功能的子频道号
blacklist=[11111111,2222222,333333]  #黑名单用户qq号
proxy_port=7890  #代理端口号
saucenao_apikey=xxxxx  #saucenao apikey
```  
### 2.charge.json  
在bot根目录新建charge.json文件并填入以下内容  
```
  {
    "群号1": 功能可用次数, 
    "子频道号": 100,
    "例如22222": 899, 
  }
```
