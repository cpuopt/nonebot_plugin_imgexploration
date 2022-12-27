import os
from nonebot.rule import Rule
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent
from nonebot_plugin_guild_patch import GuildMessageEvent
from loguru import logger
import nonebot, json


class PRIVATE_SW:
    async def __call__(self, event: PrivateMessageEvent) -> bool:
        private_on = getattr(nonebot.get_driver().config, "private_on", list)
        user_id = getattr(event, "user_id", int)
        if user_id in private_on:
            with open(f"{os.path.dirname(os.path.abspath(__file__))}/charge.json", "r") as file:
                record = file.read()
            record = json.loads(record)
            try:
                if record[str(user_id)] > 0:
                    return True
                else:
                    return False
            except KeyError as e:
                logger.error("qq号不在charge.json中,请先到charge.json中设置剩余次数")
                return False
        else:
            return False



class GROUP_SW:
    async def __call__(self, event: GroupMessageEvent) -> bool:
        group_on = getattr(nonebot.get_driver().config, "group_on", list)
        group = getattr(event, "group_id", int)
        if group in group_on:

            with open(f"{os.path.dirname(os.path.abspath(__file__))}/charge.json", "r") as file:
                record = file.read()
            record = json.loads(record)
            try:
                if record[str(group)] > 0:
                    return True
                else:
                    return False
            except KeyError as e:
                logger.error("群组不在charge.json中,请先到charge.json中设置剩余次数")
                return False
        else:
            return False

class GUILD_SW:
    async def __call__(self, event: GuildMessageEvent) -> bool:
        channel_on = getattr(nonebot.get_driver().config, "channel_on", list)
        sub_channel_on = getattr(nonebot.get_driver().config, "sub_channel_on", list)
        channel_id = event.guild_id
        sub_channel_id = event.channel_id
        if (sub_channel_id in sub_channel_on) and (channel_id in channel_on):
            with open(f"{os.path.dirname(os.path.abspath(__file__))}/charge.json", "r") as file:
                record = file.read()
            record = json.loads(record)
            try:
                if record[str(sub_channel_id)] > 0:
                    return True
                else:
                    return False
            except KeyError as e:
                logger.error("子频道号不在charge.json中,请先到charge.json中设置剩余次数")
                return False
        else:
            return False


class NOT_IN_BLACK_LIST:
    async def __call__(self, event: GroupMessageEvent) -> bool:
        qq = int(getattr(event, "user_id"))
        blacklist = getattr(nonebot.get_driver().config, "blacklist", list)
        if qq not in blacklist:
            return True
        else:
            return False


def PASS_GUILD() -> Rule:
    return Rule(GUILD_SW())


def PASS_GROUP() -> Rule:
    return Rule(GROUP_SW()) & Rule(NOT_IN_BLACK_LIST())


def PASS_PRIVATE() -> Rule:
    """检验消息来源私聊是否开启功能"""
    return Rule(PRIVATE_SW())

