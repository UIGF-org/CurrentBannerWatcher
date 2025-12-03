import os
import requests
import re
import json
from bs4 import BeautifulSoup
from push import create_banner
from BannerMeta import BannerMeta
from colorama import init, Fore, Back, Style

# Initialize colorama
init(autoreset=True)

RUN_MODE = os.getenv("run_mode", "production")
DEBUG = True if RUN_MODE == "debug" else False

CHINESE_VERSION_MAP = {
    "「月之一」": "6.0",
    "「月之二」": "6.1",
    "「月之三」": "6.2",
    "「月之四」": "6.3",
    "「月之五」": "6.4",
    "「月之六」": "6.5",
    "「月之七」": "6.6",
    "「月之八」": "6.7",
    "「月之九」": "6.8"
}
# Global counter for announcement separator
ANNOUNCEMENT_COUNT = 1

def print_separator():
    global ANNOUNCEMENT_COUNT
    separator = f"\n{Fore.WHITE}{Back.BLACK}╔══════════════════ Announcement {ANNOUNCEMENT_COUNT} ══════════════════╗{Style.RESET_ALL}"
    print(separator)
    ANNOUNCEMENT_COUNT += 1

def convert_chinese_version(version_text):
    """Convert Chinese version format to numeric version"""
    if DEBUG:
        print(f"{Fore.LIGHTYELLOW_EX}[Conversion] Converting Chinese version: {version_text}")
    for chinese_ver, numeric_ver in CHINESE_VERSION_MAP.items():
        if chinese_ver in version_text:
            return numeric_ver
    return version_text  # Return original if no match found


def get_item_id_by_name(name: str) -> int:
    url = "https://api.uigf.org/translate/"
    body = {
        "lang": "zh-cn",
        "type": "normal",
        "game": "genshin",
        "item_name": name
    }
    this_result = requests.post(url, json=body)
    if DEBUG:
        print(f"{Fore.BLUE}[API] UIGF API result: {name} -> {this_result.json()}")
    try:
        return this_result.json().get("item_id")
    except KeyError:
        return 0


def get_banner_name_by_subtitle(subtitle: str) -> str:
    # CHS
    subtitle = subtitle.replace("」祈愿", "")
    subtitle = subtitle.replace("「", "")
    # EN-US
    subtitle = subtitle.replace("Event Wish - ", "")
    # CHT
    subtitle = subtitle.replace("」祈願", "")
    subtitle = subtitle.replace("「", "")
    # JP
    subtitle = subtitle.replace(r"イベント祈願<br />", "")
    subtitle = subtitle.replace("集録祈願<br />", "")
    subtitle = subtitle.replace("」", "")
    # KO
    subtitle = subtitle.replace("「", "")
    subtitle = subtitle.replace("」 기원", "")
    subtitle = subtitle.replace(" 기원", "")
    # ES
    subtitle = subtitle.replace("Gachapón «", "")
    subtitle = subtitle.replace("»", "")
    # FR
    subtitle = subtitle.replace("Vœux « ", "")
    subtitle = subtitle.replace("Vœux « ", "")
    subtitle = subtitle.replace(" »", "")
    subtitle = subtitle.replace(" ", "")
    # RU
    subtitle = subtitle.replace("Молитва «", "")
    subtitle = subtitle.replace("»", "")
    subtitle = subtitle.replace("Молитва: ", "")
    # TH
    subtitle = subtitle.replace("การอธิษฐาน \"", "")
    subtitle = subtitle.replace("\"", "")
    # VI
    subtitle = subtitle.replace("Cầu Nguyện \"", "")
    subtitle = subtitle.replace("\"", "")
    subtitle = subtitle.replace("Cầu Nguyện ", "")
    # DE
    subtitle = subtitle.replace("Gebet „", "")
    subtitle = subtitle.replace("“", "")
    # ID
    subtitle = subtitle.replace("Event Permohonan \"", "")
    subtitle = subtitle.replace("\"", "")
    subtitle = subtitle.replace("Event Permohonan ", "")
    # PT
    subtitle = subtitle.replace("Oração \"", "")
    subtitle = subtitle.replace("\"", "")
    subtitle = subtitle.replace("Oração ", "")
    # TR
    subtitle = subtitle.replace("\" Etkinliği Dileği", "")
    subtitle = subtitle.replace(" Etkinliği Dileği", "")
    subtitle = subtitle.replace("\"", "")
    # IT
    subtitle = subtitle.replace("Desiderio ", "")
    return subtitle


def announcement_to_banner_meta(chs_ann: dict, all_announcements: list) -> list[BannerMeta] | None:
    """
    Convert an announcement to a list of BannerMeta objects, each list represent a banner in different language.
    Uses the CHS announcement as the base to parse most of the data and other languages data inherit from CHS.
    """
    print_separator()
    banner_meta_list = []
    uigf_pool_type = 0

    banner_name = get_banner_name_by_subtitle(chs_ann["subtitle"])  # BannerMeta.name
    banner_image_url = chs_ann.get("banner", "")  # BannerMeta.banner_image_url
    content_text = BeautifulSoup(chs_ann["content"], "html.parser").text
    print(f"{Fore.GREEN}[Content] Content text: {content_text}")
    if "概率UP" in chs_ann["title"]:
        print("")
        if "概率提升角色" in content_text:
            if "※ 本祈愿属于「角色活动祈愿」" in content_text:
                uigf_pool_type = 301
            elif "※ 本祈愿属于「角色活动祈愿-2」" in content_text:
                uigf_pool_type = 400
            # Character Banner
            characters_re_list = re.findall(r"[\u4e00-\u9fa5]+(?=\(风\)|\(火\)|\(水\)|\(冰\)|\(雷\)|\(岩\)|\(草\))", content_text)
            characters_list = []
            [characters_list.append(x) for x in characters_re_list if x not in characters_list]
            characters_id_list = [get_item_id_by_name(x) for x in characters_list]
            print(f"\n{Fore.MAGENTA}[Character Parsing] Characters list: {characters_list}")
            print(f"{Fore.MAGENTA}[Character Parsing] Characters ID list: {characters_id_list}")
            if len(characters_id_list) != 4:
                raise RuntimeError("Character banner must have 4 characters")
            orange_id_list = [characters_id_list[0]]
            purple_id_list = characters_id_list[1:]
            print(f"{Fore.MAGENTA}[Character Parsing] Orange ID: {orange_id_list}")
            print(f"{Fore.MAGENTA}[Character Parsing] Purple ID: {purple_id_list}\n")
        elif "神铸赋形" in chs_ann["subtitle"]:
            uigf_pool_type = 302
            weapon_re_list = re.findall(r"·([\u4e00-\u9fa5]+)", content_text)
            weapon_list = []
            [weapon_list.append(x) for x in weapon_re_list if x not in weapon_list]
            weapon_id_list = [get_item_id_by_name(x) for x in weapon_list]
            print(f"\n{Fore.MAGENTA}[Weapon Parsing] Weapon list: {weapon_list}")
            print(f"{Fore.MAGENTA}[Weapon Parsing] Weapon ID list: {weapon_id_list}")
            if len(weapon_id_list) != 7:
                raise RuntimeError("Weapon banner must have 7 weapons")
            orange_id_list = weapon_id_list[:2]
            purple_id_list = weapon_id_list[2:]
            print(f"{Fore.MAGENTA}[Weapon Parsing] Orange ID: {orange_id_list}")
            print(f"{Fore.MAGENTA}[Weapon Parsing] Purple ID: {purple_id_list}\n")
        else:
            raise RuntimeError("Unknown banner type")
    elif "本祈愿属于「集录祈愿」" in content_text:
        uigf_pool_type = 500
        content_text_no_space = content_text.replace(" ", "")
        orange_characters_re_list = re.search(r"5星角色：(?P<r>.*?)5星武器：", content_text_no_space).group("r").split("/")
        print(f"{Fore.CYAN}[Gacha Parsing] Orange characters re list: {orange_characters_re_list}")
        purple_characters_re_list = re.search(r"4星角色：(?P<r>.*?)(?=4星武器：)", content_text_no_space).group("r").split("/")
        print(f"{Fore.CYAN}[Gacha Parsing] Purple characters re list: {purple_characters_re_list}")
        orange_weapons_re_list = re.search(r"5星武器：(?P<r>.*?)4星角色：", content_text_no_space).group("r").split("/")
        print(f"{Fore.CYAN}[Gacha Parsing] Orange weapons re list: {orange_weapons_re_list}")
        purple_weapons_re_list = re.search(r"4星武器：(?P<r>.*?)(?=※)", content_text_no_space).group("r").split("/")
        print(f"{Fore.CYAN}[Gacha Parsing] Purple weapons re list: {purple_weapons_re_list}")
        orange_list = []
        [orange_list.append(x) for x in orange_characters_re_list if x not in orange_list]
        [orange_list.append(x) for x in orange_weapons_re_list if x not in orange_list]
        purple_list = []
        [purple_list.append(x) for x in purple_characters_re_list if x not in purple_list]
        [purple_list.append(x) for x in purple_weapons_re_list if x not in purple_list]

        orange_id_list = [get_item_id_by_name(x) for x in orange_list]
        purple_id_list = [get_item_id_by_name(x) for x in purple_list]
        print(f"{Fore.CYAN}[Gacha Parsing] Orange list: {orange_list}")
        print(f"{Fore.CYAN}[Gacha Parsing] Purple list: {purple_list}")
        print(f"{Fore.CYAN}[Gacha Parsing] Orange ID list: {orange_id_list}")
        print(f"{Fore.CYAN}[Gacha Parsing] Purple ID list: {purple_id_list}")
        print(f"{Fore.CYAN}[Gacha Parsing] Total count of Orange: {len(orange_id_list)}")
        print(f"{Fore.CYAN}[Gacha Parsing] Total count of Purple: {len(purple_id_list)}\n")
    else:
        print(f"{Fore.LIGHTYELLOW_EX}[Content] Not a banner announcement: {chs_ann['subtitle']}\n")
        return None

    if uigf_pool_type != 0:
        if uigf_pool_type != 500:
            time_pattern = (r"(?:〓祈愿介绍〓祈愿时间概率提升(?:角色|武器)（5星）概率提升(?:角色|武器)（4星）"
                            r"(<t class=\"(?:(t_lc)|(t_gl))\">)?)"
                            r"(?P<start>((\d\.\d|「月之[一二三四五六七八九]」)版本更新后)|(20\d{2}/\d{2}/\d{2} \d{2}:\d{2}(:\d{2})?))"
                            r"(?:(</t>)?( )?~( )?<t class=\"(?:(t_lc)|(t_gl))\">)"
                            r"(?P<end>20\d{2}/\d{2}/\d{2} \d{2}:\d{2}(:\d{2})?)")
        else:
            time_pattern = (r"(?:〓祈愿介绍〓祈愿时间可定轨5星角色可定轨5星武器"
                            r"(<t class=\"(?:(t_lc)|(t_gl))\">)?)"
                            r"(?P<start>((\d\.\d|「月之[一二三四五六七八九]」)版本更新后)|(20\d{2}/\d{2}/\d{2} \d{2}:\d{2}(:\d{2})?))"
                            r"(?:(</t>)?( )?~( )?<t class=\"(?:(t_lc)|(t_gl))\">)"
                            r"(?P<end>20\d{2}/\d{2}/\d{2} \d{2}:\d{2}(:\d{2})?)")
        try:
            content_text = content_text.replace(' contenteditable="false"', "")
            time_result = re.search(time_pattern, content_text)
            start_time = time_result.group("start")
            end_time = time_result.group("end")
            print(f"{Fore.LIGHTRED_EX}[Time Parsing] Found banner time: {start_time} ~ {end_time}")
        except AttributeError:
            raise ValueError(f"Unknown time format\nAnnouncement Content: {content_text}\nPattern: {time_pattern}")
        if "更新后" in start_time:
            order = 1
            if DEBUG:
                print(f"{Fore.LIGHTRED_EX}[Time Parsing] Start time is relative, need to find accurate time in update log")
            version_match = re.search(r"^(\d\.\d|「月之[一二三四五六七八九]」)", start_time)
            if version_match:
                version_text = version_match.group(0)
                if "月之" in version_text:
                    version = convert_chinese_version(version_text)
                else:
                    version = version_text
            else:
                raise ValueError(f"Unknown version format in start_time: {start_time}")

            try:
                patch_notes = [b for b in all_announcements if
                              (b["subtitle"] == version + "版本更新说明") or
                              (any(chinese + "版本更新说明" in b["subtitle"] for chinese in CHINESE_VERSION_MAP.keys()))]
                if patch_notes:
                    patch_note = BeautifulSoup(patch_notes[0]["content"], "html.parser").text
                    patch_time_pattern = (r"(?:〓更新时间〓<t class=\"t_(gl|lc)\"( contenteditable=\"false\")?>)"
                                          r"(?P<start>20\d{2}/\d{2}/\d{2} \d{2}:\d{2}(:\d{2})?)"
                                          r"(?:</t>开始)")
                else:
                    raise IndexError("No patch notes found")
            except IndexError:
                try:
                    patch_notes = [b for b in all_announcements if
                                  (b["subtitle"] == version + "版本更新维护预告") or
                                  (any(chinese + "版本更新维护预告" in b["subtitle"] for chinese in CHINESE_VERSION_MAP.keys()))]
                    if patch_notes:
                        patch_note = BeautifulSoup(patch_notes[0]["content"], "html.parser").text
                        print(f"\n{Fore.LIGHTBLUE_EX}[Patch Note] Patch note: {patch_note}")
                        patch_time_pattern = (r"(?:预计将于<t class=\"t_(gl|lc)\"( contenteditable=\"false\")?>)"
                                              r"(?P<start>20\d{2}/\d{2}/\d{2} \d{2}:\d{2}(:\d{2})?)"
                                              r"(?:</t>进行版本更新维护)")
                    else:
                        raise IndexError("No maintenance announcement found")
                except IndexError:
                    if DEBUG:
                        for b in all_announcements:
                            print(f"{Fore.RED}[Debug] {b['subtitle']}")
                            print(f"{Fore.RED}[Debug] {b['content']}")
                    print(f"{Fore.LIGHTBLUE_EX}[Patch Note] No update log found; game is most likely under maintenance")
                    exit(500)
            try:
                start_time = re.search(patch_time_pattern, patch_note).group("start")
            except AttributeError:
                raise ValueError(f"Unknown time format\nPatch Note: {patch_note}\nPattern: {patch_time_pattern}")
            print(f"{Fore.LIGHTBLUE_EX}[Patch Note] Found patch time: {start_time}")
        else:
            version = "99.99"
            order = 2
            for b in all_announcements:
                if "版本更新说明" in b["subtitle"]:
                    version_match = re.search(r"^(\d+\.\d+|「月之[一二三四五六七八九]」)", b["subtitle"])
                    if version_match:
                        version_text = version_match.group(0)
                        if "月之" in version_text:
                            version = convert_chinese_version(version_text)
                        else:
                            version = version_text
                    break
            if version == "99.99":
                raise ValueError("No update log found")
    else:
        return None

    banner_meta = BannerMeta(
        lang="zh-cn",
        ann_id=chs_ann["ann_id"],
        version=version,
        order=order,
        name=banner_name,
        uigf_banner_type=uigf_pool_type,
        banner_image_url=banner_image_url,
        banner_image_url_backup=banner_image_url,
        start_time=start_time,
        end_time=end_time,
        up_orange_list=orange_id_list,
        up_purple_list=purple_id_list
    )
    print(f"\n{Fore.LIGHTGREEN_EX}[BannerMeta] {banner_meta.model_dump_json()}")
    banner_meta_list.append(banner_meta)

    target_language = ["en-us", "zh-tw", "ja", "ko", "es", "fr",
                       "ru", "th", "vi", "de", "id", "pt", "tr", "it"]
    for lang in target_language:
        this_meta = banner_meta.model_copy()
        this_meta.lang = lang
        url = "https://sg-hk4e-api-static.hoyoverse.com/common/hk4e_global/announcement/api/getAnnContent?"
        params = {
            "game": "hk4e",
            "game_biz": "hk4e_global",
            "region": "os_asia",
            "bundle_id": "hk4e_global",
            "channel_id": "1",
            "level": "55",
            "platform": "pc",
            "lang": lang,
        }
        for k, v in params.items():
            url += f"{k}={v}&"
        url += "uid=100000000"
        this_lang_ann = requests.get(url).json().get("data").get("list")
        matched_ann = [ann for ann in this_lang_ann if ann["ann_id"] == chs_ann["ann_id"]]
        banner_name = get_banner_name_by_subtitle(matched_ann[0]["subtitle"])
        this_meta.name = banner_name
        banner_image = matched_ann[0].get("banner", "")
        this_meta.banner_image_url = banner_image
        print(f"{Fore.LIGHTGREEN_EX}[BannerMeta] {this_meta.model_dump_json()}")
        banner_meta_list.append(this_meta)

    return banner_meta_list


def archive_announcement(ann: dict):
    import os, requests
    ann_id = ann["ann_id"]
    base_dir = "ann_archive"
    ann_dir = os.path.join(base_dir, str(ann_id))
    os.makedirs(ann_dir, exist_ok=True)
    # Save zh-cn content
    with open(os.path.join(ann_dir, "zh-cn.txt"), "w", encoding="utf-8") as f:
        f.write(ann["content"])
    target_languages = ["en-us", "zh-tw", "ja", "ko", "es", "fr", "ru", "th", "vi", "de", "id", "pt", "tr", "it"]
    for lang in target_languages:
        url = "https://sg-hk4e-api-static.hoyoverse.com/common/hk4e_global/announcement/api/getAnnContent?"
        params = {
            "game": "hk4e",
            "game_biz": "hk4e_global",
            "region": "os_asia",
            "bundle_id": "hk4e_global",
            "channel_id": "1",
            "level": "55",
            "platform": "pc",
            "lang": lang,
        }
        for k, v in params.items():
            url += f"{k}={v}&"
        url += "uid=100000000"
        try:
            ann_list = requests.get(url).json().get("data", {}).get("list", [])
            matched = [a for a in ann_list if a["ann_id"] == ann_id]
            if matched:
                with open(os.path.join(ann_dir, f"{lang}.txt"), "w", encoding="utf-8") as f:
                    f.write(matched[0]["content"])
        except Exception:
            pass


def refresh_all_banner_data():
    return_result = {}
    url = "https://sg-hk4e-api-static.hoyoverse.com/common/hk4e_global/announcement/api/getAnnContent?"
    params = {
        "game": "hk4e",
        "game_biz": "hk4e_global",
        "region": "os_asia",
        "bundle_id": "hk4e_global",
        "channel_id": "1",
        "level": "55",
        "platform": "pc",
        "lang": "zh-cn",
    }
    for k, v in params.items():
        url += f"{k}={v}&"
    url += "uid=100000000"
    print(f"{Fore.YELLOW}[HTTP] zh-cn URL: {url}\n")
    banner_data = requests.get(url).json().get("data").get("list")
    for ann in banner_data:
        # Archive each announcement's raw content
        archive_announcement(ann)
        this_banner_data = announcement_to_banner_meta(ann, banner_data)
        if this_banner_data is None:
            continue
        else:
            # Append banner announcement id to banner_ann_list.txt
            banner_list_file = os.path.join("ann_archive", "banner_ann_list.txt")
            with open(banner_list_file, "a", encoding="utf-8") as f:
                f.write(str(ann["ann_id"]) + "\n")
            this_banner_dict = {}
            this_banner_ann_id = this_banner_data[0].ann_id

            this_banner_dict["UpOrangeList"] = this_banner_data[0].up_orange_list
            this_banner_dict["UpPurpleList"] = this_banner_data[0].up_purple_list
            this_banner_dict["UIGF_pool_type"] = this_banner_data[0].uigf_banner_type
            this_banner_dict["start_time"] = this_banner_data[0].start_time
            this_banner_dict["end_time"] = this_banner_data[0].end_time
            this_banner_dict["version_number"] = this_banner_data[0].version
            this_banner_dict["order_number"] = this_banner_data[0].order
            for lang_banner in this_banner_data:
                this_banner_dict[lang_banner.lang] = {
                    "banner_name": lang_banner.name,
                    "banner_image": lang_banner.banner_image_url
                }
            return_result[this_banner_ann_id] = this_banner_dict
    with open("banner-data.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(return_result, indent=2, ensure_ascii=False))
    print(f"{Fore.LIGHTGREEN_EX}[Finish] Done\n")


if __name__ == "__main__":
    print(f"{Back.WHITE}{Fore.BLACK}======== Starting Banner Data Collection ========{Style.RESET_ALL}\n")
    refresh_all_banner_data()
    create_banner()
