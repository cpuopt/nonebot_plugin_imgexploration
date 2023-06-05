import nonebot
import httpx
from typing import Union
from nonebot import on_command,require
from nonebot.log import logger
from nonebot.typing import T_State
from nonebot.params import Arg, CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment, GroupMessageEvent, PrivateMessageEvent
require("nonebot_plugin_guild_patch")
from nonebot_plugin_guild_patch import GuildMessageEvent
from .imgexploration import Imgexploration


__plugin_meta__ = PluginMetadata(name="查找图片出处", description="通过saucenao、ascii2d、Google、Yandx查询图片出处", usage="command:搜图")

proxy_port = getattr(nonebot.get_driver().config, "proxy_port", None)
saucenao_apikey = getattr(nonebot.get_driver().config, "saucenao_apikey", "a778025bd4644780c9edd82970484548786fb583")
google_cookies = getattr(nonebot.get_driver().config, "google_cookies","")

proxies = f"http://127.0.0.1:{proxy_port}" if proxy_port else None


def numspilt(args: str, max: int):
    args_list = list(args.split())
    r_li = []
    for arg in args_list:
        if arg.isnumeric() and 1 <= int(arg) <= max:
            r_li.append(int(arg))
        elif arg.isnumeric() and int(arg) >= max:
            for i in arg:
                if i.isnumeric() and 1 <= int(i) <= max:
                    r_li.append(int(i))
    return r_li


imgexploration = on_command(cmd="搜图", priority=1, block=True)


@imgexploration.handle()
async def cmd_receive(event: Union[GroupMessageEvent, PrivateMessageEvent, GuildMessageEvent], state: T_State, pic: Message = CommandArg()):
    if pic:
        state["Message_pic"] = pic


@imgexploration.got("Message_pic", prompt="请发送要搜索的图片")
async def get_pic(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent, GuildMessageEvent], state: T_State, msgpic: Message = Arg("Message_pic")):
    for segment in msgpic:
        if segment.type == "image":
            pic_url: str = segment.data["url"]  # 图片链接
            logger.success(f"获取到图片: {pic_url}")
            async with httpx.AsyncClient(proxies=proxies) as client:
                search = Imgexploration(
                    pic_url=pic_url,
                    client=client,
                    proxy=proxies,
                    saucenao_apikey=saucenao_apikey,
                    google_cookies=google_cookies,
                )
                await imgexploration.send(message=Message(MessageSegment.text("搜索进行中……")), reply_message=True)
                await search.doSearch()
            result_dict = search.getResultDict()
            state["result_dict"] = result_dict
            await imgexploration.send(
                message=Message(
                    MessageSegment.image(file=result_dict["pic"]) + MessageSegment.text("请在180s内发送序号以获得对应结果的链接，一次可以发送多个序号，例如：1 5 6"),
                ),
                reply_message=True,
            )
            break

    else:
        await imgexploration.reject("你发送的不是图片，请以“图片”形式发送！")


@imgexploration.got("need_num")
async def get_num(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent, GuildMessageEvent], state: T_State, nummsg: Message = Arg("need_num")):
    try:
        args = list(map(int, str(nummsg).split()))
        if args[0] == 0:
            await imgexploration.finish(message=Message(MessageSegment.reply(event.message_id) + MessageSegment.text("搜图结束")))
        msg = MessageSegment.text("")
        res_len = len(state["result_dict"]["info"])
        args = numspilt(str(nummsg), res_len)
        for no in args:
            url = state["result_dict"]["info"][no - 1]["url"]
            msg += MessageSegment.text(f"{no} - {url}\n")
        await bot.send(event, message=Message(msg + "你还有机会发送序号以获取链接\n发送非数字消息或0以结束搜图"), reply_message=True)
        await imgexploration.reject()
    except (IndexError, ValueError):
        logger.error("参数错误，没有发送序号，搜图结束")
        await imgexploration.finish(message=Message(MessageSegment.text(f"你没有发送序号，搜图结束！")), reply_message=True)
