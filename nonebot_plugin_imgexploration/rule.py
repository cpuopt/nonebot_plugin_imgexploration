from nonebot.rule import Rule
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent,PrivateMessageEvent
from plugins.nonebot_plugin_guild_patch import GuildMessageEvent
from loguru import logger
import nonebot, json

class PRIVATE_SW:
    async def __call__(self, event: PrivateMessageEvent) -> bool:
        private_on = getattr(nonebot.get_driver().config, "private_on", list)
        if not private_on:
            logger.error("配置文件中没有private_on字段,要开启功能必须添加该字段!")
        user = getattr(event, "user_id", int)
        if user in private_on:
            return True
        else:
            return False


def PRIVATE_in_SW() -> Rule:
    """检验消息来源私聊是否开启功能"""
    return Rule(PRIVATE_SW())

class GROUP_SW:
    async def __call__(self, event: GroupMessageEvent) -> bool:
        group_on = getattr(nonebot.get_driver().config, "group_on", list)
        if not group_on:
            logger.error("配置文件中没有group_on字段,要开启功能必须添加该字段!")
        group = getattr(event, "group_id", int)
        if group in group_on:
            return True
        else:
            return False


def GROUP_in_SW() -> Rule:
    """检验消息来源群组是否开启功能"""
    return Rule(GROUP_SW())


class GROUP_CHARGE:
    async def __call__(self, bot: Bot, event: GroupMessageEvent) -> bool:
        group = str(getattr(event, "group_id"))

        with open("charge.json", "r") as file:
            record = file.read()
        record = json.loads(record)
        try:
            if record[group] > 0:
                return True
            else:
                return False
        except KeyError as e:
            logger.error("该群组不在charge.json中,请先到charge.json中设置剩余次数")
            return False


class NOT_IN_BLACK_LIST:
    async def __call__(self, bot: Bot, event: GroupMessageEvent) -> bool:
        qq = int(getattr(event, "user_id"))
        blacklist = getattr(nonebot.get_driver().config, "blacklist", list)
        if qq not in blacklist:
            return True
        else:
            return False


def QQ_not_in_BLACKLIST() -> Rule:
    return Rule(NOT_IN_BLACK_LIST())


def PASS_BLACKLIST_MODE() -> Rule:
    return Rule(GROUP_SW()) & Rule(NOT_IN_BLACK_LIST()) & Rule(GROUP_CHARGE())


class GUILD_SW:
    async def __call__(self, bot: Bot, event: GuildMessageEvent) -> bool:
        channel_on = getattr(nonebot.get_driver().config, "channel_on", list)
        sub_channel_on = getattr(nonebot.get_driver().config, "sub_channel_on", list)
        channel_id = event.guild_id
        sub_channel_id = event.channel_id
        if (sub_channel_id in sub_channel_on) and (channel_id in channel_on):
            return True
        else:
            return False


def PASS_GUILD() -> Rule:
    return Rule(GUILD_SW())
