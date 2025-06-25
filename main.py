# -*- coding:utf-8 -*-
import os
import random
import sys
import time
import requests
from bs4 import BeautifulSoup
import re
from tqdm import tqdm
from datetime import datetime
from utils import filter_title_str
import json
import logging
import traceback
import platform
import pathlib

from markdownify import MarkdownConverter


# 读取配置文件
def load_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        print("未找到config.json文件，尝试读取旧版zhihuUrls.json文件")
        try:
            with open('zhihuUrls.json', 'r', encoding='utf-8') as f:
                urls = json.load(f)
                return {"zhihuUrls": urls, "outputPath": "", "os": ""}
        except FileNotFoundError:
            print("未找到配置文件，请创建config.json文件并配置收藏夹信息")
            return {"zhihuUrls": [], "outputPath": "", "os": ""}

# 获取当前操作系统类型
def get_current_os():
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    else:
        return "unknown"

# 解析路径，根据操作系统类型处理
def parse_output_path(path_str, os_type):
    if not path_str:
        return None
    
    # 如果没有指定os，则自动检测
    if not os_type:
        os_type = get_current_os()
    
    try:
        if os_type.lower() == "windows":
            # Windows路径处理
            # 支持 D:\path\to\folder 或 D:/path/to/folder 格式
            path_str = path_str.replace('/', '\\')
            return pathlib.Path(path_str).resolve()
        elif os_type.lower() in ["linux", "freebsd", "openbsd", "netbsd", "solaris", "aix"]:
            # Unix-like系统路径处理
            # 支持 /usr/local/lib 格式
            if path_str.startswith('~'):
                path_str = os.path.expanduser(path_str)
            return pathlib.Path(path_str).resolve()
        elif os_type.lower() in ["macos", "darwin"]:
            # macOS路径处理
            # 支持 /Users/username/Documents 或 ~/Documents 格式
            if path_str.startswith('~'):
                path_str = os.path.expanduser(path_str)
            return pathlib.Path(path_str).resolve()
        elif os_type.lower() in ["cygwin", "msys"]:
            # Cygwin/MSYS环境路径处理
            # 支持 /cygdrive/c/path 或 /c/path 格式
            if path_str.startswith('/cygdrive/'):
                # Cygwin格式: /cygdrive/c/path -> C:\path
                drive_path = path_str[10:]  # 移除 /cygdrive/
                if len(drive_path) >= 2 and drive_path[1] == '/':
                    path_str = drive_path[0].upper() + ':' + drive_path[1:].replace('/', '\\')
            elif path_str.startswith('/') and len(path_str) >= 3 and path_str[2] == '/':
                # MSYS格式: /c/path -> C:\path
                path_str = path_str[1].upper() + ':' + path_str[2:].replace('/', '\\')
            return pathlib.Path(path_str).resolve()
        else:
            # 其他系统，尝试通用处理
            logging.warning(f"未知操作系统类型: {os_type}，尝试通用路径处理")
            if path_str.startswith('~'):
                path_str = os.path.expanduser(path_str)
            return pathlib.Path(path_str).resolve()
    except Exception as e:
        logging.error(f"路径解析失败: {path_str}, 错误: {str(e)}")
        return None

# 读取cookies
def load_cookies():
    try:
        with open('cookies.json', 'r', encoding='utf-8') as f:
            cookies_list = json.load(f)
        cookies_dict = {}
        for cookie in cookies_list:
            cookies_dict[cookie['name']] = cookie['value']
        return cookies_dict
    except FileNotFoundError:
        print("未找到cookies.json文件，将使用无登录模式访问（部分内容可能无法获取）")
        return {}

# 全局变量存储当前处理的收藏夹名称
current_collection_name = ""

# 全局日志数据存储
processing_log = []

# 全局配置和路径管理
config = {}
base_output_path = None

# 设置调试日志
def setup_debug_logging():
    # 初始化时使用默认路径，稍后会在main中重新配置
    logs_dir = os.path.join(os.path.dirname(__file__), 'downloads', 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_log_file = os.path.join(logs_dir, f"debug_{timestamp}.log")
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(debug_log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return debug_log_file

# 重新配置日志路径
def reconfigure_logging():
    logs_dir = get_logs_path()
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_log_file = os.path.join(logs_dir, f"debug_{timestamp}.log")
    
    # 清除已有的handler
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # 重新配置
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(debug_log_file, encoding='utf-8'),
            logging.StreamHandler()
        ],
        force=True
    )
    return debug_log_file

# 获取输出路径的函数
def get_output_path(collection_name):
    """
    根据配置获取输出路径
    如果配置了outputPath，使用自定义路径
    否则使用默认的downloads路径
    """
    global base_output_path
    
    if base_output_path:
        # 使用自定义输出路径
        return os.path.join(str(base_output_path), collection_name)
    else:
        # 使用默认路径
        return os.path.join(os.path.dirname(__file__), 'downloads', collection_name)

def get_logs_path():
    """
    获取日志路径
    """
    global base_output_path
    
    if base_output_path:
        # 使用自定义输出路径
        return os.path.join(str(base_output_path), 'logs')
    else:
        # 使用默认路径
        return os.path.join(os.path.dirname(__file__), 'downloads', 'logs')

debug_log_file = setup_debug_logging()

cookies = load_cookies()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
    "Connection": "keep-alive",
    "Accept": "text/html,application/json,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.8"
}

class ObsidianStyleConverter(MarkdownConverter):
    """
    Create a custom MarkdownConverter that adds two newlines after an image
    """

    def chomp(self, text):
        """
        If the text in an inline tag like b, a, or em contains a leading or trailing
        space, strip the string and return a space as suffix of prefix, if needed.
        This function is used to prevent conversions like
            <b> foo</b> => ** foo**
        """
        prefix = ' ' if text and text[0] == ' ' else ''
        suffix = ' ' if text and text[-1] == ' ' else ''
        text = text.strip()
        return (prefix, suffix, text)

    def convert_img(self, *args, **kwargs):
        logging.debug(f"convert_img called with args: {args}, kwargs={kwargs}")
        try:
            # 提取参数，适配不同的调用方式
            if len(args) >= 2:
                el, text = args[0], args[1]
            else:
                el = kwargs.get('el')
                text = kwargs.get('text', '')
            
            alt = el.attrs.get('alt', None) or ''
            src = el.attrs.get('src', None) or ''

            # 使用全局变量获取当前收藏夹名称
            global current_collection_name
            downloadDir = get_output_path(current_collection_name)
            if not os.path.exists(downloadDir):
                os.makedirs(downloadDir)
            assetsDir = os.path.join(downloadDir,'assets')
            if not os.path.exists(assetsDir):
                os.makedirs(assetsDir)

            img_content = requests.get(url=src, headers=headers, cookies=cookies).content
            img_content_name = src.split('?')[0].split('/')[-1]

            imgPath = os.path.join(assetsDir,img_content_name)
            with open(imgPath, 'wb') as fp:
                fp.write(img_content)

            result = '![[%s]]\n(%s)\n\n' % (img_content_name, alt)
            logging.debug(f"convert_img returning: {result}")
            return result
        except Exception as e:
            logging.error(f"convert_img error: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            raise

    def convert_a(self, *args, **kwargs):
        logging.debug(f"convert_a called with args: {args}, kwargs={kwargs}")
        try:
            # 提取参数，适配不同的调用方式
            if len(args) >= 2:
                el, text = args[0], args[1]
                convert_as_inline = args[2] if len(args) > 2 else None
            else:
                el = kwargs.get('el')
                text = kwargs.get('text', '')
                convert_as_inline = kwargs.get('convert_as_inline')
            
            prefix, suffix, text = self.chomp(text)
            if not text:
                return ''
            href = el.get('href')
            # title = el.get('title')

            if el.get('aria-labelledby') and el.get('aria-labelledby').find('ref') > -1:
                text = text.replace('[', '[^')
                result = '%s' % text
                logging.debug(f"convert_a returning (aria-labelledby): {result}")
                return result
            if (el.attrs and 'data-reference-link' in el.attrs) or ('class' in el.attrs and ('ReferenceList-backLink' in el.attrs['class'])):
                text = '[^{}]: '.format(href[5])
                result = '%s' % text
                logging.debug(f"convert_a returning (reference-link): {result}")
                return result

            # 调用父类方法，适配不同的参数组合
            try:
                if convert_as_inline is not None:
                    result = super(ObsidianStyleConverter, self).convert_a(el, text, convert_as_inline, **kwargs)
                else:
                    result = super(ObsidianStyleConverter, self).convert_a(el, text, **kwargs)
            except TypeError:
                # 如果参数不匹配，尝试不同的调用方式
                try:
                    result = super(ObsidianStyleConverter, self).convert_a(*args, **kwargs)
                except TypeError:
                    result = super(ObsidianStyleConverter, self).convert_a(el, text)
            
            logging.debug(f"convert_a returning (super): {result}")
            return result
        except Exception as e:
            logging.error(f"convert_a error: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            raise

    def convert_li(self, *args, **kwargs):
        logging.debug(f"convert_li called with args: {args}, kwargs={kwargs}")
        try:
            # 提取参数，适配不同的调用方式
            if len(args) >= 2:
                el, text = args[0], args[1]
                convert_as_inline = args[2] if len(args) > 2 else None
            else:
                el = kwargs.get('el')
                text = kwargs.get('text', '')
                convert_as_inline = kwargs.get('convert_as_inline')
            
            if el and el.find('a', {'aria-label': 'back'}) is not None:
                result = '%s\n' % ((text or '').strip())
                logging.debug(f"convert_li returning (aria-label back): {result}")
                return result

            # 调用父类方法，适配不同的参数组合
            try:
                if convert_as_inline is not None:
                    result = super(ObsidianStyleConverter, self).convert_li(el, text, convert_as_inline, **kwargs)
                else:
                    result = super(ObsidianStyleConverter, self).convert_li(el, text, **kwargs)
            except TypeError:
                # 如果参数不匹配，尝试不同的调用方式
                try:
                    result = super(ObsidianStyleConverter, self).convert_li(*args, **kwargs)
                except TypeError:
                    result = super(ObsidianStyleConverter, self).convert_li(el, text)
            
            logging.debug(f"convert_li returning (super): {result}")
            return result
        except Exception as e:
            logging.error(f"convert_li error: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            raise

def markdownify(html, **options):
    return ObsidianStyleConverter(**options).convert(html)


# 获取收藏夹的回答总数
def get_article_nums_of_collection(collection_id):
    """
    :param starturl: 收藏夹连接
    :return: 收藏夹的页数
    """
    try:
        collection_url = "https://www.zhihu.com/api/v4/collections/{}/items".format(collection_id)
        html = requests.get(collection_url, headers=headers, cookies=cookies)
        html.raise_for_status()

        # 页面总数
        return html.json()['paging'].get('totals')
    except:
        return None


# 解析出每个回答的具体链接
def get_article_urls_in_collection(collection_id):
    collection_id =collection_id.replace('\n','')

    offset = 0
    limit = 20

    article_nums = get_article_nums_of_collection(collection_id)

    url_list = []
    title_list = []
    while offset < article_nums:
        collection_url = "https://www.zhihu.com/api/v4/collections/{}/items?offset={}&limit={}".format(collection_id,
                                                                                                       offset, limit)
        try:
            html = requests.get(collection_url, headers=headers, cookies=cookies)
            content = html.json()
        except:
            return None

        for el in content['data']:
            url_list.append(el['content']['url'])
            try:
                if el['content']['type'] == 'answer':
                    title_list.append(el['content']['question']['title'])
                else:
                    title_list.append(el['content']['title'])
            except:
                print('********')
                print('TBD 非回答, 非专栏, 想法类收藏暂时无法处理')
                for k, v in el['content'].items():
                    if k in ['type', 'url']:
                        print(k, v)
                print('********')
                url_list.pop()

        offset += limit

    return url_list, title_list


# 获得单条答案的数据
def get_single_answer_content(answer_url):
    # all_content = {}
    # question_id, answer_id = re.findall('https://www.zhihu.com/question/(\d+)/answer/(\d+)', answer_url)[0]

    html_content = requests.get(answer_url, headers=headers, cookies=cookies)
    soup = BeautifulSoup(html_content.text, "lxml")
    try:
        answer_content = soup.find('div', class_="AnswerCard").find("div", class_="RichContent-inner")
    except:
        print(answer_url, 'failed')
        return -1
    # 去除不必要的style标签
    for el in answer_content.find_all('style'):
        el.extract()

    for el in answer_content.select('img[src*="data:image/svg+xml"]'):
        el.extract()
    
    for el in answer_content.find_all('a'): # 处理回答中的卡片链接
        aclass = el.get('class')
        if isinstance(aclass, list):
            if aclass[0] == 'LinkCard':
                linkcard_name = el.get('data-text')
                el.string = linkcard_name if linkcard_name is not None else el.get('href')
        else:
            pass
        try:
            if el.get('href').startswith('mailto'): # 特殊bug, 正文的aaa@bbb.ccc会被识别为邮箱, 嵌入<a href='mailto:xxx'>中, markdown转换时会报错
                el.name = 'p'
        except:
            print(answer_url, el) # 一些广告卡片, 不需要处理
        
    # 添加html外层标签
    answer_content = html_template(answer_content)

    return answer_content


# 获取单条专栏文章的内容
def get_single_post_content(paper_url):
    html_content = requests.get(paper_url, headers=headers, cookies=cookies)
    soup = BeautifulSoup(html_content.text, "lxml")
    post_content = soup.find("div", class_="Post-RichText")
    # 去除不必要的style标签
    if post_content:
        for el in post_content.find_all('style'):
            el.extract()

        for el in post_content.select('img[src*="data:image/svg+xml"]'):
            el.extract()
        
        for el in post_content.find_all('a'): # 处理专栏文章中的卡片链接
            aclass = el.get('class')
            if isinstance(aclass, list):
                if aclass[0] == 'LinkCard':
                    linkcard_name = el.get('data-text')
                    el.string = linkcard_name if linkcard_name is not None else el.get('href')
            else:
                pass
            try:
                if el.get('href').startswith('mailto'): # 特殊bug, 正文的aaa@bbb.ccc会被识别为邮箱, 嵌入<a href='mailto:xxx'>中, markdown转换时会报错
                    el.name = 'p'
            except:
                print(paper_url, el)
    else:
        post_content = "该文章链接被404, 无法直接访问"

    # 添加html外层标签
    post_content = html_template(post_content)

    return post_content


def html_template(data):
    # api content
    html = '''
        <html>
        <head>
        </head>
        <body>
        %s
        </body>
        </html>
        ''' % data
    return html


def is_article_already_downloaded(file_path, target_url):
    """
    检查文件是否已存在且包含相同的URL
    :param file_path: 要检查的markdown文件路径
    :param target_url: 目标URL
    :return: True如果文件存在且URL匹配，False否则
    """
    if not os.path.exists(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            # 检查第一行是否为引用块且包含目标URL
            if first_line.startswith('> ') and target_url in first_line:
                return True
    except:
        pass
    
    return False


def get_unique_filename(base_dir, title, url):
    """
    获取唯一的文件名，如果标题重复则添加URL的ID部分
    :param base_dir: 基础目录
    :param title: 文章标题
    :param url: 文章URL
    :return: 唯一的文件路径
    """
    base_filename = filter_title_str(title)
    file_path = os.path.join(base_dir, base_filename + ".md")
    
    # 如果文件不存在，直接返回
    if not os.path.exists(file_path):
        return file_path
    
    # 如果文件存在且URL匹配，返回该路径（用于跳过）
    if is_article_already_downloaded(file_path, url):
        return file_path
    
    # 如果文件存在但URL不匹配，添加URL ID后缀
    url_id = url.split('/')[-1]
    unique_filename = f"{base_filename}_{url_id}"
    return os.path.join(base_dir, unique_filename + ".md")


def save_processing_log():
    """
    保存处理日志到logs目录
    """
    logs_dir = get_logs_path()
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{timestamp}.json"
    log_path = os.path.join(logs_dir, log_filename)
    
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(processing_log, f, ensure_ascii=False, indent=2)
    
    print(f"处理日志已保存到: {log_path}")



def process_single_collection(collection_name, collection_url):
    """处理单个收藏夹"""
    global current_collection_name, processing_log
    current_collection_name = collection_name
    
    collection_id = collection_url.split('?')[0].split('/')[-1]
    urls, titles = get_article_urls_in_collection(collection_id)
    
    # 初始化此收藏夹的日志记录
    collection_log = {
        "name": collection_name,
        "url": collection_url,
        "list": []
    }
    
    if not urls:
        print(f"收藏夹 '{collection_name}' 获取失败或为空")
        processing_log.append(collection_log)
        return
    
    assert len(urls) == len(titles), '地址标题列表长度不一致'
    
    print(f"收藏夹 '{collection_name}' 共获取 {len(urls)} 篇可导出回答或专栏")
    
    downloadDir = get_output_path(collection_name)
    if not os.path.exists(downloadDir):
        os.makedirs(downloadDir)
    
    for i in tqdm(range(len(urls)), desc=f"处理 {collection_name}"):
        content = None
        url = urls[i]
        title = titles[i]
        
        # 获取唯一的文件路径
        file_path = get_unique_filename(downloadDir, title, url)
        
        # 初始化文章日志记录
        article_log = {
            "name": title,
            "url": url,
            "status": ""
        }
        
        # 检查文件是否已存在且包含相同URL
        if is_article_already_downloaded(file_path, url):
            article_log["status"] = "文章已存在,跳过下载"
            collection_log["list"].append(article_log)
            continue
        
        try:
            if url.find('zhuanlan') != -1:
                content = get_single_post_content(url)
            else:
                content = get_single_answer_content(url)
            
            if content == -1:
                article_log["status"] = f"文章下载失败, 原因:获取内容失败"
                collection_log["list"].append(article_log)
                print(url, 'get content failed.')
                continue
            
            md = markdownify(content, heading_style="ATX")
            md = '> %s\n' % url + md
            
            with open(file_path, "w", encoding='utf-8') as md_file:
                md_file.write(md)
            
            article_log["status"] = "文章不存在,正常下载"
            collection_log["list"].append(article_log)
            time.sleep(random.randint(1, 5))
            
        except Exception as e:
            article_log["status"] = f"文章下载失败, 原因:{str(e)}"
            collection_log["list"].append(article_log)
            print(content)
            print(e)
            print(url, 'error')
    
    # 将收藏夹日志添加到全局日志
    processing_log.append(collection_log)
    print(f"收藏夹 '{collection_name}' 下载完毕")


if __name__ == '__main__':
    # 加载配置
    global config, base_output_path
    config = load_config()
    
    # 解析输出路径
    if config.get('outputPath'):
        base_output_path = parse_output_path(config['outputPath'], config.get('os', ''))
        if base_output_path:
            print(f"使用自定义输出路径: {base_output_path}")
            # 重新配置日志路径
            reconfigure_logging()
        else:
            print("输出路径解析失败，使用默认路径")
            base_output_path = None
    else:
        print("使用默认输出路径: downloads/")
    
    zhihu_collections = config.get('zhihuUrls', [])
    
    if not zhihu_collections:
        print("没有找到要处理的收藏夹配置")
        sys.exit(1)
    
    print(f"共找到 {len(zhihu_collections)} 个收藏夹待处理")
    
    for collection in zhihu_collections:
        collection_name = collection.get('name', '未命名收藏夹')
        collection_url = collection.get('url', '')
        
        if not collection_url:
            print(f"收藏夹 '{collection_name}' 缺少URL，跳过")
            continue
        
        print(f"\n开始处理收藏夹: {collection_name}")
        process_single_collection(collection_name, collection_url)
    
    print("\n所有收藏夹处理完毕!")
    
    # 保存处理日志
    save_processing_log()

# def testMarkdownifySingleAnswer():
#     url = "https://www.zhihu.com/question/506166712/answer/2271842801"
#     content = get_single_answer_content(url)
#     md = markdownify(content, heading_style="ATX")
#     id = url.split('/')[-1]
#
#     downloadDir = os.path.join(os.path.dirname(__file__), 'downloads', '剪藏')
#     if not os.path.exists(downloadDir):
#         os.makedirs(downloadDir)
#     with open(os.path.join(downloadDir, id + ".md"), "w", encoding='utf-8') as md_file:
#         md_file.write(md)
#     print("{} 转换成功".format(id))
#
# def testMarkdownifySinglePost():
#     url = 'https://zhuanlan.zhihu.com/p/386395767'
#     content = get_single_post_content(url)
#     md = markdownify(content, heading_style="ATX")
#     id = url.split('/')[-1]
#     with open("./" + id + ".md", "w", encoding='utf-8') as md_file:
#         md_file.write(md)
#     print("{} 转换成功".format(id))
#
#
# # if __name__ == '__main__':
# #     testMarkdownifySingleAnswer()
#