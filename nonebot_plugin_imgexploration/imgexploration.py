import asyncio
import base64
import re
import traceback
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from PicImageSearch import Ascii2D, Network, SauceNAO
from lxml import etree
import httpx, json
from io import BytesIO
from loguru import logger
import PIL
import urllib


class Imgexploration:
    def __init__(self, pic_url, client: httpx.AsyncClient, proxy, saucenao_apikey, google_cookies):
        """
        Parameters
        ----------
            * pic_url : 图片url
            * proxy_port : 代理端口
            * saucenao_apikey : saucenao_apikey
        """
        self.client = client
        self.__proxy = proxy
        self.__pic_url = pic_url
        self.setFront(big_size=25, nomal_size=20, small_size=15)

        general_header = {
            "sec-ch-ua": '"Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"',
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
        }

        self.setHeadersCookieApikey(saucenao_apikey=saucenao_apikey, general_header=general_header, google_cookies=google_cookies)

    def setHeadersCookieApikey(self, saucenao_apikey, general_header, google_cookies):
        """
        Args:
        ----------
            * saucenao_apikey (str):
        """
        self.__saucenao_apikey = saucenao_apikey
        self.__generalHeader = general_header
        self.__google_cookies = google_cookies

    async def __getImgbytes(self):
        try:
            self.__pic_bytes = (await self.client.get(url=self.__pic_url, timeout=10)).content
            img = Image.open(BytesIO(self.__pic_bytes))
            img = img.convert("RGB")
            width = img.width
            height = img.height
            if width > 2000 or height > 2000:
                radius = width // 1000 if width > height else height // 1000
                img = img.resize((int(width / radius), int(height / radius)))
                res = BytesIO()
                img.save(res, format="JPEG")
                self.__pic_bytes = res.getvalue()
        except Exception as e:
            logger.error(e)

    async def __uploadToImgops(self):
        logger.info("图片上传到Imgops")
        try:
            files = {"photo": self.__pic_bytes}
            data = {"isAjax": "true"}
            headers = {
                "sec-ch-ua": '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
                "sec-ch-ua-platform": '"Windows"',
                "Origin": "https://imgops.com",
                "Referer": "https://imgops.com/",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "zh-CN,zh;q=0.9",
            }
            post = await self.client.post("https://imgops.com/store", files=files, data=data, headers=headers, timeout=10)

            self.__imgopsUrl = "https:/" + post.text
        except Exception as e:
            self.__imgopsUrl = self.__pic_url
            logger.error(e)

    def setFront(self, big_size: int, nomal_size: int, small_size: int):
        """
        Parameters
        ----------
            * big_size  大号字体字号
            * nomal_size : 中号字体字号
            * small_size : 小号字体字号

        """
        self.__font_b_size = big_size
        self.__font_b = ImageFont.truetype("HarmonyOS_Sans_SC_Regular", big_size)
        self.__font_n = ImageFont.truetype("HarmonyOS_Sans_SC_Bold", nomal_size)
        self.__font_s = ImageFont.truetype("HarmonyOS_Sans_SC_Light", small_size)

    @staticmethod
    async def ImageBatchDownload(urls: list, client: httpx.AsyncClient) -> list[bytes]:
        tasks = [asyncio.create_task(client.get(url)) for url in urls]
        return [((await task).content) for task in tasks]

    async def __draw(self) -> bytes:
        try:
            font_size = self.__font_b_size
            font = self.__font_b
            font2 = self.__font_n
            font3 = self.__font_s
            num = len(self.__result_info)
            width = 900
            height = 200
            total_height = height * num if num != 0 else 10
            line_width = 2
            line_fill = (200, 200, 200)
            text_x = 300
            logger.info(f"Drawing... total:{num}")
            img = Image.new(mode="RGB", size=(width, total_height), color=(255, 255, 255))

            draw = ImageDraw.Draw(img)
            margin = 20
            for i in range(1, num):
                draw.line(
                    (margin, i * height, width - margin, i * height),
                    fill=line_fill,
                    width=line_width,
                )

            vernier = 0
            seat = 0

            for single in self.__result_info:
                seat += 1

                if "thumbnail_bytes" in single:
                    thumbnail = single["thumbnail_bytes"]
                    try:
                        thumbnail = Image.open(fp=BytesIO(thumbnail)).convert("RGB")
                    except PIL.UnidentifiedImageError:
                        thumbnail = Image.new(mode="RGB", size=(200, 200), color=(255, 255, 255))

                    thumbnail = thumbnail.resize((int((height - 2 * margin) * thumbnail.width / thumbnail.height), height - 2 * margin))
                    if single["source"] == "ascii2d":
                        thumbnail = thumbnail.filter(ImageFilter.GaussianBlur(radius=3))

                    if thumbnail.width > text_x - 2 * margin:
                        thumbnail = thumbnail.crop((0, 0, text_x - 2 * margin, thumbnail.height))
                        img.paste(im=thumbnail, box=(margin, vernier + margin))
                    else:
                        img.paste(im=thumbnail, box=(text_x - thumbnail.width - margin, vernier + margin))

                text_ver = 2 * margin
                draw.text(
                    xy=(width - margin, vernier + 10),
                    text=f"NO.{seat} from {single['source']}",
                    fill=(150, 150, 150),
                    font=font2,
                    anchor="ra",
                )

                if single["title"]:
                    text = single["title"].replace("\n", "")
                    lw = font.getlength(text)
                    text = text if lw < 450 else f"{text[:int(len(text)*450/lw)]}..."
                    draw.text(xy=(text_x, vernier + text_ver), text="Title: ", fill=(160, 160, 160), font=font, anchor="la")
                    draw.text(xy=(text_x + 60, vernier + text_ver), text=text, fill=(0, 0, 0), font=font, anchor="la")
                    text_ver = text_ver + font_size + margin / 2

                if ("similarity" in single) and single["similarity"]:  # saucenao
                    text = single["similarity"]
                    draw.text(xy=(text_x, vernier + text_ver), text="similarity: ", fill=(160, 160, 160), font=font, anchor="la")
                    draw.text(xy=(text_x + 115, vernier + text_ver), text=f"{text}", fill=(0, 0, 0), font=font, anchor="la")
                    text_ver = text_ver + font_size + margin / 2

                if ("description" in single) and single["description"]:
                    text = single["description"]
                    lw = font.getlength(text)
                    text = text if lw < 520 else f"{text[:int(len(text)*520/lw)]}..."
                    draw.text(xy=(text_x, vernier + text_ver), text=text, fill=(0, 0, 0), font=font, anchor="la")
                    text_ver = text_ver + font_size + margin / 2

                if ("domain" in single) and single["domain"]:  # Yandex
                    text = single["domain"]
                    draw.text(xy=(text_x, vernier + text_ver), text="Source: ", fill=(160, 160, 160), font=font, anchor="la")
                    draw.text(xy=(text_x + 86, vernier + text_ver), text=f"{text}", fill=(0, 0, 0), font=font, anchor="la")
                    text_ver = text_ver + font_size + margin / 2

                if single["url"]:
                    url = single["url"]
                    lw = font3.getlength(url)
                    url = url if lw < 560 else f"{url[:int(len(url)*560/lw)]}..."
                    draw.text(xy=(text_x, vernier + text_ver), text=url, fill=(100, 100, 100), font=font3, anchor="la")
                vernier += height

            save = BytesIO()
            img.save(save, format="PNG", quality=100)
            return save.getvalue()
        except Exception as e:
            raise e

    async def __saucenao_build_result(self, result_num=10, minsim=60, max_num=5) -> dict:
        resList = []
        logger.info("saucenao searching...")
        try:
            async with Network(proxies=self.__proxy, timeout=20) as client:
                saucenao = SauceNAO(client=client, api_key=self.__saucenao_apikey, numres=result_num)
                saucenao_result = await saucenao.search(url=self.__imgopsUrl)

                thumbnail_urls = []
                for single in saucenao_result.raw:
                    if single.similarity < minsim or single.url == "" or single.thumbnail == "":
                        continue
                    thumbnail_urls.append(single.thumbnail)
                thumbnail_bytes = await self.ImageBatchDownload(thumbnail_urls, self.client)
                i = 0
                for single in saucenao_result.raw:
                    if single.similarity < minsim or single.url == "" or single.thumbnail == "":
                        continue
                    sin_di = {
                        "title": single.title,  # 标题
                        "thumbnail": single.thumbnail,  # 缩略图url
                        "url": urllib.parse.unquote(single.url),
                        "similarity": single.similarity,
                        "source": "saucenao",
                        "thumbnail_bytes": thumbnail_bytes[i],
                    }
                    i += 1
                    resList.append(sin_di)
                return resList
        except IndexError as e:
            logger.error(e)
            return []
        finally:
            logger.success(f"saucenao result:{len(resList)}")
            return resList

    async def __google_build_result(self, result_num=5) -> dict:
        google_header = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd:gzip, deflate, br, zstd",
            "accept-language": "zh-CN,zh-HK;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6:zh-CN,zh-HK;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6",
            "cache-control": "no-cache:no-cache",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }
        resList = []
        logger.info("google searching...")
        try:
            params = {
                "url": self.__imgopsUrl,
            }
            google_lens = await self.client.get(f"https://lens.google.com/uploadbyurl", params=params, headers=google_header, timeout=10, cookies=self.__google_cookies.cookies)
            self.__google_cookies.update(google_lens.headers)
            redirect_url = google_lens.headers.get("location")
            google_header["referer"] = str(google_lens.url)
            google_lens = await self.client.get(redirect_url, headers=google_header, timeout=10, cookies=self.__google_cookies.cookies)
            self.__google_cookies.update(google_lens.headers)
            google_lens_text = google_lens.text
            main_page = etree.HTML(google_lens_text)
            elements = main_page.xpath("//span[text()='查看完全匹配的结果']/ancestor::a[1]")
            if elements:
                href = "https://www.google.com" + elements[0].get("href")
                google_lens = await self.client.get(href, headers=google_header, timeout=10, cookies=self.__google_cookies.cookies)
                full_match_page = etree.HTML(google_lens.text)
                id_base64_mapping = parseBase64Image(full_match_page)
                with open("Googlelens_test.html", "w+", encoding="utf-8") as file:
                    file.write(google_lens.text)
                res_items = full_match_page.xpath("//div[@id='search']/div/div/div")
                for item in res_items:
                    link = item.xpath(".//a")[0].get("href")
                    img_id = item.xpath(".//a//img")[0].get("id")
                    title = item.xpath(".//a/div/div[2]/div[1]/text()")[0]
                    img_base64 = id_base64_mapping[img_id] if img_id in id_base64_mapping.keys() else None
                    img_bytes = base64.b64decode(img_base64) if img_base64 else None
                    if img_bytes != None:
                        sin_di = {
                            "title": title,
                            "thumbnail_bytes": img_bytes,
                            "url": link,
                            "source": "Google",
                        }
                        resList.append(sin_di)
            else:
                pass

            return resList

        except Exception as e:
            logger.error(traceback.format_exc())
            with open("Googlelens_error_page.html", "w+", encoding="utf-8") as file:
                file.write(google_lens_text)
            raise e

        finally:
            logger.success(f"google result:{len(resList)}")
            return resList

    def __ascii2d_get_external_url(self, rawhtml):
        rawhtml = str(rawhtml)
        external_url_li = etree.HTML(rawhtml).xpath('//div[@class="external"]/a[1]/@href')
        if external_url_li:
            return external_url_li[0]  # 可能的手动登记结果:list
        else:
            return False

    async def __ascii2d_build_result(self, sh_num: int = 2, tz_num: int = 3) -> dict:
        """
        Parameters
        ----------
            * sh_num : 色和搜索获取结果数量
            * tz_num : 特征搜索获取结果数量

        """
        logger.info("ascii2d searching...")
        result_li = []
        try:
            async with Network(proxies=self.__proxy, timeout=20) as client:
                ascii2d_sh = Ascii2D(client=client, bovw=False)

                # ascii2d_sh_result = await ascii2d_sh.search(url=self.__pic_url)

                ascii2d_tz = Ascii2D(client=client, bovw=True)
                # ascii2d_tz_result = await ascii2d_tz.search(url=self.__pic_url)

                ascii2d_sh_result = await asyncio.create_task(ascii2d_sh.search(url=self.__imgopsUrl))
                ascii2d_tz_result = await asyncio.create_task(ascii2d_tz.search(url=self.__imgopsUrl))

                thumbnail_urls = []
                for single in ascii2d_tz_result.raw[0:tz_num] + ascii2d_sh_result.raw[0:sh_num]:
                    external_url_li = self.__ascii2d_get_external_url(single.origin)
                    if not external_url_li and not single.url:
                        continue
                    elif single.url:
                        url = single.url
                    else:
                        url = external_url_li
                    sin_di = {
                        "title": single.title,
                        "thumbnail": single.thumbnail,
                        "url": urllib.parse.unquote(url),
                        "source": "ascii2d",
                    }
                    thumbnail_urls.append(single.thumbnail)
                    result_li.append(sin_di)
                thumbnail_bytes = await self.ImageBatchDownload(thumbnail_urls, self.client)
                i = 0
                for single in result_li:
                    single["thumbnail_bytes"] = thumbnail_bytes[i]
                    i += 1
        except Exception as e:
            logger.error(e)
            return []
        finally:
            logger.success(f"ascii2d result:{len(result_li)}")
            return result_li

    async def __yandex_build_result(self, result_num=5) -> dict:
        """
        Parameter:
        ---------
            * result_num : 需要的结果数量
        """
        logger.info("yandex searching...")
        try:
            yandexurl = f"https://yandex.com/images/search"
            data = {
                "rpt": "imageview",
                "url": self.__imgopsUrl,
            }
            result_li = []

            yandexPage = await self.client.get(url=yandexurl, params=data, headers=self.__generalHeader, timeout=20)
            yandexHtml = etree.HTML(yandexPage.text)
            InfoJSON = yandexHtml.xpath('//*[@class="cbir-section cbir-section_name_sites"]/div/@data-state')[0]
            result_dict = json.loads(InfoJSON)
            thumbnail_urls = []
            for single in result_dict["sites"][:result_num]:
                thumbnail_urls.append("https:" + single["thumb"]["url"])
            thumbnail_bytes = await self.ImageBatchDownload(thumbnail_urls, self.client)
            i = 0
            for single in result_dict["sites"][:result_num]:
                sin_di = {
                    "source": "Yandex",
                    "title": single["title"],  # 标题
                    "thumbnail": "https:" + single["thumb"]["url"],  # 预览图url
                    "url": urllib.parse.unquote(single["url"]),  # 来源网址
                    "description": single["description"],  # 描述
                    "domain": single["domain"],  # 来源网站域名
                    "thumbnail_bytes": thumbnail_bytes[i],
                }
                i += 1
                result_li.append(sin_di)
            logger.success(f"yandex result:{len(result_li)}")
            return result_li
        except Exception as e:
            raise e
            logger.error(e)
        finally:
            return result_li

    async def doSearch(self) -> dict:
        await self.__getImgbytes()
        await self.__uploadToImgops()
        task_saucenao = asyncio.create_task(self.__saucenao_build_result())
        task_ascii2d = asyncio.create_task(self.__ascii2d_build_result())
        task_google = asyncio.create_task(self.__google_build_result())
        task_yandex = asyncio.create_task(self.__yandex_build_result())

        # self.__result_info = (await task_saucenao) + (await task_ascii2d) + (await task_google) + (await task_yandex)
        self.__result_info = (await task_saucenao) + (await task_ascii2d) + (await task_google) + (await task_yandex)
        result_pic = await self.__draw()

        self.__picNinfo = {
            "pic": result_pic,
            "info": self.__result_info,
        }

    def getResultDict(self):
        """
        Returns
        ----------
        {
            "pic": bytes,
            "info": list,
        }
        """
        return self.__picNinfo


class Cookies:

    cookies = httpx.Cookies()
    filepath: str
    cookies_json = []

    def __init__(self, filepath):
        self.filepath = filepath

        with open(filepath, "r") as f:
            self.cookies_json = json.loads(f.read())

        for cookie in self.cookies_json:
            self.cookies.set(cookie["name"], cookie["value"], cookie["domain"])

    def update(self, response_headers: httpx.Headers):
        set_cookies = response_headers.get_list("set-cookie")

        if not set_cookies:
            return self.cookies

        new_cookies = httpx.Cookies()
        for cookie in self.cookies.jar:
            new_cookies.set(cookie.name, cookie.value, cookie.domain)

        for cookie_str in set_cookies:
            cookie_parts = cookie_str.split(";")
            if not cookie_parts:
                continue

            name_value = cookie_parts[0].strip().split("=", 1)
            if len(name_value) != 2:
                continue

            name, value = name_value

            for part in cookie_parts[1:]:
                if part.strip().lower().startswith("domain="):
                    domain = part.split("=", 1)[1].strip()
                    break

            new_cookies.set(name, value, domain)
            for cookie in self.cookies_json:
                if cookie["name"] == name:
                    cookie = {"domain": domain, "name": name, "value": value}

        self.cookies = new_cookies
        self.save()

    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.cookies_json, f, ensure_ascii=False, indent=4)

def parseBase64Image(document: etree.Element) -> dict[str, str]:
    """从HTML文档中解析id和对应的图片base64
    """
    res_dic = {}
    for script in document.xpath("//script[@nonce]"):
        func = script.xpath("./text()")
        func_text: str = func[0] if func and len(func) > 0 else ""

        id_match = re.search(r"\['(.*?)'\]", func_text)
        id = id_match.group(1) if id_match else None

        base64_match = re.search(r"data:image/jpeg;base64,(.*?)'", func_text)
        b64 = base64_match.group(1).replace(r"\x3d", "=") if base64_match else None

        if id != None and b64 != None:

            if "','" in id:
                for dimg in id.split("','"):
                    res_dic[dimg] = b64
            else:
                res_dic[id] = b64

    return res_dic


if __name__ == "__main__":
    url = r"https://p.inari.site/usr/369/67821385a0fe3.jpg"
    google_cookies = Cookies("googleaCookies.json")
    proxy_port = 7890

    async def main():
        async with httpx.AsyncClient(
            proxies=f"http://127.0.0.1:{proxy_port}",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            },
        ) as client:

            aa = Imgexploration(
                pic_url=url,
                client=client,
                proxy=f"http://127.0.0.1:{proxy_port}",
                saucenao_apikey="",
                google_cookies=google_cookies,
            )
            await aa.doSearch()
        img = Image.open(BytesIO(aa.getResultDict()["pic"]))
        img.show()
        img.save("00.jpg", format="JPEG", quality=100)

    asyncio.run(main())
