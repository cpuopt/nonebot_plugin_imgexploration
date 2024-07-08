import asyncio
import re
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
                    draw.text(xy=(text_x, vernier + text_ver), text="Title: ", fill=(160, 160, 160), font=font, anchor="la")
                    draw.text(xy=(text_x + 60, vernier + text_ver), text=f"{text[:20]}{'...' if len(text)>=20 else ''}", fill=(0, 0, 0), font=font, anchor="la")
                    text_ver = text_ver + font_size + margin / 2

                if ("similarity" in single) and single["similarity"]:  # saucenao
                    text = single["similarity"]
                    draw.text(xy=(text_x, vernier + text_ver), text="similarity: ", fill=(160, 160, 160), font=font, anchor="la")
                    draw.text(xy=(text_x + 115, vernier + text_ver), text=f"{text}", fill=(0, 0, 0), font=font, anchor="la")
                    text_ver = text_ver + font_size + margin / 2

                if ("description" in single) and single["description"]:
                    text = single["description"]
                    draw.text(xy=(text_x, vernier + text_ver), text=f"{text[:30]}{'...' if len(text)>=30 else ''}", fill=(0, 0, 0), font=font, anchor="la")
                    text_ver = text_ver + font_size + margin / 2

                if ("domain" in single) and single["domain"]:  # Yandex
                    text = single["domain"]
                    draw.text(xy=(text_x, vernier + text_ver), text="Source: ", fill=(160, 160, 160), font=font, anchor="la")
                    draw.text(xy=(text_x + 86, vernier + text_ver), text=f"{text}", fill=(0, 0, 0), font=font, anchor="la")
                    text_ver = text_ver + font_size + margin / 2

                if single["url"]:
                    url = single["url"]
                    draw.text(xy=(text_x, vernier + text_ver), text=f"{url[:80]}{'......' if len(url)>=80 else ''}", fill=(100, 100, 100), font=font3, anchor="la")
                vernier += height

            save = BytesIO()
            img.save(save, format="JPEG", quality=95)
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
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
            "Cookie": self.__google_cookies,
        }
        resList = []
        logger.info("google searching...")
        try:
            params = {
                "url": self.__imgopsUrl,
            }
            google_lens_text = (await self.client.get(f"https://lens.google.com/uploadbyurl", params=params, headers=google_header, follow_redirects=True, timeout=10)).text

            req_tex = re.findall(r"var AF_dataServiceRequests = (.+?); var AF_initDataChunkQueue", google_lens_text)
            if req_tex:
                ds1 = re.findall(r"'ds:1' : (.*)}", req_tex[0])
                if ds1:
                    ds = ds1[0]
                    # print(ds)
                    ds = (
                        ds.replace("id:", '"id":')
                        .replace("request:", '"request":')
                        .replace("'", '"')
                        .replace("[4,true],null,null,[],null", 'null,null,null,[],"000000"')
                        .replace("true", "1")
                        .replace("false", "0")
                        .replace("Asia/Kuching", "Asia/Hong_Kong")
                        .replace("[5,6,7,2]", "[5,6,2]")
                        .replace("[],[null,5],null,[5]", "[null,null],[null,5],null,[5],[]")
                    )
                    dic = json.loads(ds)
                    try:
                        dic["request"][1][-1].remove(1)
                    except Exception as e:
                        pass
                    dic["request"][-3].append(dic["request"][1])

            qest = [
                [
                    [
                        dic["id"],
                        json.dumps(dic["request"]),
                        None,
                        "generic",
                    ],
                ],
            ]
            postDate = {"f.req": json.dumps(qest)}
            post_headers = {
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                "Sec-Ch-Ua": '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
                "Referer": "https://lens.google.com/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
            }
            te = await self.client.post(url="https://lens.google.com/_/LensWebStandaloneUi/data/batchexecute?hl=zh-CN", data=postDate, headers=post_headers)

            res_j = json.loads(te.text.replace(r")]}'", "", 1))
            search_result = json.loads(res_j[0][2])[1][0][1][8][20][0][0]

            for singleDiv in search_result[:result_num]:
                try:
                    sin_di = {
                        "title": singleDiv[4],
                        "thumbnail_url": singleDiv[0][0],
                        "url": singleDiv[2][2][2],
                        "source": "Google",
                        "domain": singleDiv[1][2],
                    }
                except IndexError:
                    continue
                resList.append(sin_di)

            thumbnail_urls = [single["thumbnail_url"] for single in resList]
            thumbnail_bytes = await self.ImageBatchDownload(thumbnail_urls, self.client)
            i = 0
            for single in resList:
                single["thumbnail_bytes"] = thumbnail_bytes[i]
                i += 1
            return resList

        except Exception as e:
            logger.error(e)
            with open("Googlelens_error_page.html", "w+", encoding="utf-8") as file:
                file.write(google_lens_text)

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


if __name__ == "__main__":
    url = "https://p.inari.site/usr/369/63e89daabf5f5.jpg"
    google_cookies = ""
    proxy_port=7890
    async def main():
        async with httpx.AsyncClient(proxies=f"http://127.0.0.1:{proxy_port}") as client:
            aa = Imgexploration(
                pic_url=url,
                client=client,
                proxy=f"http://127.0.0.1:{proxy_port}",
                saucenao_apikey="c9b7e159baa5ec9e7334e81efdaed6213f9a8d55",
                google_cookies=google_cookies,
            )
            await aa.doSearch()
        img = Image.open(BytesIO(aa.getResultDict()["pic"]))
        img.show()
        img.save("00.jpg", format="JPEG", quality=100)

    asyncio.run(main())
