from nonebot import on_command
from nonebot.log import logger
from nonebot.typing import T_State
from nonebot.params import Arg, CommandArg
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment, GroupMessageEvent, PrivateMessageEvent
from nonebot_plugin_guild_patch import GuildMessageEvent
import json
from .picsearch import Picsearch
from .rule import PASS_BLACKLIST_MODE, PASS_GUILD, PRIVATE_in_SW
import nonebot

proxy_port = getattr(nonebot.get_driver().config, "proxy_port", int)
saucenao_apikey = getattr(nonebot.get_driver().config, "saucenao_apikey", str)


def private_charg(event: PrivateMessageEvent, charg=1):
    user_id = str(getattr(event, "user_id"))

    with open("charge.json", "r") as file:
        record = file.read()
    record = json.loads(record)
    try:
        if record[user_id]:
            record[user_id] -= 1
            logger.info(f"私聊{user_id}扣除1次,剩余{record[user_id]}次")
    except (KeyError):
        pass
    record = json.dumps(record)
    with open("charge.json", "w") as file:
        file.write(record)
    return True


def guild_charg(event: GuildMessageEvent, charg=1):
    sub_channel_id = str(event.channel_id)
    with open("charge.json", "r") as file:
        record = file.read()
    record = json.loads(record)
    try:
        if record[sub_channel_id]:
            record[sub_channel_id] -= charg
            logger.info(f"子频道{sub_channel_id}扣除{charg}次,剩余{record[sub_channel_id]}次")
    except (KeyError):
        pass
    record = json.dumps(record)
    with open("charge.json", "w") as file:
        file.write(record)
    return True


def charge(event):
    group = str(getattr(event, "group_id"))

    with open("charge.json", "r") as file:
        record = file.read()
    record = json.loads(record)
    try:
        if record[group]:
            record[group] -= 1
            logger.info(f"群组{group}扣除1次,剩余{record[group]}次")
    except (KeyError):
        pass
    record = json.dumps(record)
    with open("charge.json", "w") as file:
        file.write(record)
    return True


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
    print(r_li)
    return r_li


imgexploration = on_command(cmd="搜图", rule=PASS_BLACKLIST_MODE())


@imgexploration.handle()
async def cmd_receive(event: GroupMessageEvent, state: T_State, pic: Message = CommandArg()):
    if pic:
        state["Message_pic"] = pic


@imgexploration.got("Message_pic", prompt="请发送要搜索的图片")
async def get_pic(bot: Bot, event: GroupMessageEvent, state: T_State, msgpic: Message = Arg("Message_pic")):
    if msgpic[0].type == "image":
        pic_url: str = msgpic[0].data["url"]  # 图片链接
        logger.success(f"获取到图片: {pic_url}")
        search = Picsearch(pic_url=pic_url, proxy_port=proxy_port, saucenao_apikey=saucenao_apikey)
        await imgexploration.send(message=Message(MessageSegment.reply(event.message_id) + MessageSegment.text("搜索进行中……")))
        search.run()
        result_dict = search.getResultDict()
        state["result_dict"] = result_dict
        await imgexploration.send(message=Message(MessageSegment.reply(event.message_id) + MessageSegment.image(file=result_dict["pic"]) + MessageSegment.text("请在60s内发送序号以获得对应结果的链接，一次可以发送多个序号，例如：1 5 6")))

        charge(event)

    else:
        await imgexploration.reject("你发送的不是图片，请以“图片”形式发送！")


@imgexploration.got("need_num")
async def get_num(bot: Bot, event: GroupMessageEvent, state: T_State, nummsg: Message = Arg("need_num")):
    try:
        args = list(map(int, str(nummsg).split()))
        if args[0] == 0:
            await imgexploration.finish(message=Message(MessageSegment.reply(event.message_id) + MessageSegment.text("搜图结束")))
        msg = ""
        res_len = len(state["result_dict"]["info"])
        args = numspilt(str(nummsg), res_len)
        for no in args:
            url = state["result_dict"]["info"][no - 1]["url"]
            msg += f"{no} - {url}\n"
        await imgexploration.send(message=f"{msg}你还有机会发送序号以获取链接\n发送非数字消息或0以结束搜图")
        await imgexploration.reject()
    except (IndexError, ValueError):
        logger.error("参数错误，没有发送序号，搜图结束")
        await imgexploration.finish(message=Message(MessageSegment.reply(event.message_id) + MessageSegment.text(f"你没有发送序号，搜图结束！")))


guild_imgexploration = on_command(cmd="搜图", rule=PASS_GUILD())


@guild_imgexploration.handle()
async def cmd_receive(event: GuildMessageEvent, state: T_State, pic: Message = CommandArg()):
    if pic:
        state["Message_pic"] = pic


@guild_imgexploration.got("Message_pic", prompt="请发送要搜索的图片")
async def get_pic(bot: Bot, event: GuildMessageEvent, state: T_State, msgpic: Message = Arg("Message_pic")):
    if msgpic[0].type == "image":
        pic_url: str = msgpic[0].data["url"]  # 图片链接
        logger.success(f"获取到图片: {pic_url}")
        search = Picsearch(pic_url=pic_url, proxy_port=proxy_port, saucenao_apikey=saucenao_apikey)
        await guild_imgexploration.send(message=Message(MessageSegment.reply(event.message_id) + MessageSegment.text("搜索进行中……")))
        search.run()
        result_dict = search.getResultDict()
        state["result_dict"] = result_dict
        await guild_imgexploration.send(message=Message(MessageSegment.reply(event.message_id) + MessageSegment.image(file=result_dict["pic"]) + MessageSegment.text("请在60s内发送序号以获得对应结果的链接，一次可以发送多个序号，例如：1 5 6")))

        guild_charg(event, 1)

    else:
        await guild_imgexploration.reject("你发送的不是图片，请以“图片”形式发送！")


@guild_imgexploration.got("need_num")
async def get_num(bot: Bot, event: GuildMessageEvent, state: T_State, nummsg: Message = Arg("need_num")):
    try:
        args = list(map(int, str(nummsg).split()))
        if args[0] == 0:
            await guild_imgexploration.finish(message=Message(MessageSegment.reply(event.message_id) + MessageSegment.text("搜图结束")))
        msg = ""
        res_len = len(state["result_dict"]["info"])
        args = numspilt(str(nummsg), res_len)
        for no in args:
            url = state["result_dict"]["info"][no - 1]["url"]
            msg += f"{no} - {url}\n"
        await guild_imgexploration.send(message=f"{msg}你还有机会发送序号以获取链接\n发送非数字消息或0以结束搜图")
        await guild_imgexploration.reject()
    except (IndexError, ValueError):
        logger.error("参数错误，没有发送序号，搜图结束")
        await guild_imgexploration.finish(message=Message(MessageSegment.reply(event.message_id) + MessageSegment.text(f"你没有发送序号，搜图结束！")))


private_imgexploration = on_command(cmd="搜图", rule=PRIVATE_in_SW())


@private_imgexploration.handle()
async def cmd_receive(event: PrivateMessageEvent, state: T_State, pic: Message = CommandArg()):
    if pic:
        state["Message_pic"] = pic


@private_imgexploration.got("Message_pic", prompt="请发送要搜索的图片")
async def get_pic(bot: Bot, event: PrivateMessageEvent, state: T_State, msgpic: Message = Arg("Message_pic")):
    if msgpic[0].type == "image":
        pic_url: str = msgpic[0].data["url"]  # 图片链接
        logger.success(f"获取到图片: {pic_url}")
        search = Picsearch(pic_url=pic_url, proxy_port=proxy_port, saucenao_apikey=saucenao_apikey)
        await private_imgexploration.send(message=Message(MessageSegment.reply(event.message_id) + MessageSegment.text("搜索进行中……")))
        search.run()
        result_dict = search.getResultDict()
        state["result_dict"] = result_dict
        await private_imgexploration.send(message=Message(MessageSegment.reply(event.message_id) + MessageSegment.image(file=result_dict["pic"]) + MessageSegment.text("请在60s内发送序号以获得对应结果的链接，一次可以发送多个序号，例如：1 5 6")))

        private_charg(event, 1)

    else:
        await private_imgexploration.reject("你发送的不是图片，请以“图片”形式发送！")


@private_imgexploration.got("need_num")
async def get_num(bot: Bot, event: PrivateMessageEvent, state: T_State, nummsg: Message = Arg("need_num")):
    try:
        args = list(map(int, str(nummsg).split()))
        if args[0] == 0:
            await private_imgexploration.finish(message=Message(MessageSegment.reply(event.message_id) + MessageSegment.text("搜图结束")))
        msg = ""
        res_len = len(state["result_dict"]["info"])
        args = numspilt(str(nummsg), res_len)
        for no in args:
            url = state["result_dict"]["info"][no - 1]["url"]
            msg += f"{no} - {url}\n"
        await private_imgexploration.send(message=f"{msg}你还有机会发送序号以获取链接\n发送非数字消息或0以结束搜图")
        await private_imgexploration.reject()
    except (IndexError, ValueError):
        logger.error("参数错误，没有发送序号，搜图结束")
        await private_imgexploration.finish(message=Message(MessageSegment.reply(event.message_id) + MessageSegment.text(f"你没有发送序号，搜图结束！")))
