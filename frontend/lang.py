#coding: utf-8

import os
import sys
import json
import re
import time
import random
import json
from hashlib import md5

# try:
#     from googletrans import Translator
# except ImportError:
#     print("未安装 googletrans==4.0.0-rc1，正在安装...")
#     os.system('pip install googletrans==4.0.0-rc1 -i http://pypi.tuna.tsinghua.edu.cn/simple')
#     from googletrans import Translator

try:
    import requests
except ImportError:
    print("未安装 requests，正在安装...")
    os.system('pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple')
    import requests



# 解决 Windows 下编码问题，强制使用 utf-8 编码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# 百度翻译
class baidu_translate:
    endpoint = 'http://api.fanyi.baidu.com'
    path = '/api/trans/vip/translate'
    url = endpoint + path
    appid = '20180721000187461'
    appkey = 'HaI_R03u6RyDBizKw09G'
    from_lang = 'zh'

    def make_md5(self,s, encoding='utf-8'):
        '''
            @name 生成md5
            @param s 字符串
            @param encoding 编码
            @return string
        '''
        return md5(s.encode(encoding)).hexdigest()
    

    def translate(self, query, to_lang='en'):
        '''
            @name 调用百度翻译API
            @param query 原文
            @param to_lang 目标语言
            @return dict
        '''
        salt = random.randint(32768, 65536)
        sign = self.make_md5(self.appid + query + str(salt) + self.appkey)

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        payload = {'appid': self.appid, 'q': query, 'from': self.from_lang, 'to': to_lang, 'salt': salt, 'sign': sign}

        r = requests.post(self.url, params=payload, headers=headers)
        result = r.json()
        return result
    

    # def google(self,text,dest,src):
    #     '''
    #         @name 调用googletrans API
    #         @param text 原文
    #         @param dest 目标语言
    #         @param src 源语言
    #         @return string
    #     '''
    #     print('原文:',text,'目标语言:',dest)
    #     translater = Translator()
    #     result = translater.translate(text, dest, src)
    #     return result.text  



class Lang:
    extension = [".html",".go",".tpl"]
    server_path = "./src/bt-i18n"
    exec_path = server_path
    production_path = "./src/bt-i18n/transResult"   # 翻译后产物的存放地址


    
    
    def read_file(self,filename):
        '''
            @name 读取文件
            @param filename 文件名
            @return any
        '''
        with open(filename, "r",encoding="utf-8") as file:
            fbody = file.read()
            return fbody
    
    def write_file(self,filename, body):
        '''
            @name 写入文件
            @param filename 文件名
            @param body 内容
        '''
        with open(filename, "w",encoding="utf-8") as file:
            file.write(body)
    
    def get_lang(self, body):
        '''
            @name 解析文件中要翻译的文本
            @param body 文件内容
            @return list
        '''

        lang_list = []
        for line in body.split("\n"):
            if "public.lang(" in line or "public.Lang(" in line:
                lang = re.findall(r"public\.lang\([\'\"](.+?)[\'\"]", line,re.I)
                if lang:
                    lang_list.extend(lang)
            elif "public.LangCtx(" in line:
                lang = re.findall(r"public\.LangCtx\(ctx, [\'\"](.+?)[\'\"]", line,re.I)
                if lang:
                    lang_list.extend(lang)
            elif "{{LangCtx .ctx " in line:
                lang = re.findall(r"{{LangCtx .ctx [\"](.+?)[\"]", line,re.I)
                if lang:
                    lang_list.extend(lang)
            elif "{{Lang " in line:
                lang = re.findall(r"{{Lang [\"](.+?)[\"]", line,re.I)
                if lang:
                    lang_list.extend(lang)
            elif "# LANG {" in line:
                lang = re.findall(r"# LANG\s+\{(.+?)\}", line,re.I)
                if lang:
                    lang_list.extend(lang)
            
            # 处理元数据中的翻译
            elif "Lang{" in line and "}" in line:
                lang = re.findall(r"Lang\{(.+?)\}", line,re.I)
                if lang:
                    lang_list.extend(lang)

        return lang_list
    
    def get_all_lang_dict(self,to_lang='en'):
        '''
            @name 取已经翻译过的结果集
            @param to_lang 目标语言
            @return dict
        '''

        filename = os.path.join(self.server_path,'all',to_lang + '.json')
        if not os.path.exists(filename):
            return {}
        body = self.read_file(filename)
        try:
            return json.loads(body)
        except:
            return {}
        
    def save_all_lang_dict(self,langs,to_lang='en'):
        '''
            @name 保存翻译结果集
            @param langs dict
            @param to_lang 目标语言
        '''
        save_path = os.path.join(self.exec_path,'all')
        filename = os.path.join(save_path,to_lang + '.json')
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        
        self.write_file(filename,json.dumps(langs,indent=4,ensure_ascii=False))

    
    def translate(self, langs,to_lang='en',name='server',to_lang_google='en',from_type = 'google'):
        '''
            @name 翻译
            @param langs list
            @param to_lang 目标语言
            @param name 保存文件名
        '''
        baidu = baidu_translate()
        to_lang_dict = {}
        all_lang_dict = self.get_all_lang_dict(to_lang)
        for lang in langs:
            md5 = lang
            if to_lang == 'zh':
                to_lang_dict[md5] = lang
                continue

            # 先从已经翻译过的结果集中取
            if md5 in all_lang_dict:
                to_lang_dict[md5] = all_lang_dict[md5]['dst']
                continue

            # 调用googletrans API
            trans_result = {}
            if from_type == 'google':
                try:
                    trans_result['dst'] = baidu.google(lang,to_lang_google,'zh-cn')
                except Exception as e:
                    print('Error:',e)
                    if str(e).find('EOF occurred in violation of protocol') != -1 or str(e).find('The read operation timed out') != -1:
                        print('翻译失败，正在重试...')
                        time.sleep(1)
                        try:
                            trans_result['dst'] = baidu.google(lang,to_lang_google,'zh-cn')
                        except Exception as e:
                            print('Error:',e)

                    continue
            else:
                try:
                    result = baidu.translate(lang,to_lang)
                    print('result:',result)
                    trans_result['dst'] = result['trans_result'][0]['dst']
                except Exception as e:
                    print('Error:',e)
                    if str(e).find('EOF occurred in violation of protocol') != -1 or str(e).find('The read operation timed out') != -1:
                        print('翻译失败，正在重试...')
                        time.sleep(1)
                        try:
                            result = baidu.translate(lang,to_lang)
                            print('result:',result)
                            trans_result['dst'] = result['trans_result'][0]['dst']
                        except Exception as e:
                            print('Error:',e)
                    continue
                    


            res = {
                'src': lang,
                'dst': trans_result['dst']
            }

            to_lang_dict[md5] = trans_result['dst']
            all_lang_dict[md5] = res

            if from_type == 'google':
                time.sleep(0.1)

        # 保存翻译结果集
        self.save_all_lang_dict(all_lang_dict,to_lang)

        # 保存翻译结果到语言文件
        save_path = os.path.join(self.production_path,'lang')
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        filename = os.path.join(save_path,to_lang+'.json')

        self.write_file(filename,json.dumps(to_lang_dict,indent=4,ensure_ascii=False))

        
    def get_settings(self):
        '''
            @name 获取配置文件
            @return list
        '''
        default = [{
            "name": "en",
            "google": "en",
            "title": "English",
            "cn": "英语"
        }]
        filename = os.path.join(self.server_path,'settings.json')
        if not os.path.exists(filename):
            return default
        body = self.read_file(filename)
        try:
            return json.loads(body)
        except:
            return default

    def get_src_lang(self):
        filename = self.server_path + "/zh.panel_source.json"
        body = self.read_file(filename)
        # body = body.replace("export default ","")
        s = json.loads(body)
        return s.keys()

    
    def start(self):
        '''
            @name 开始翻译
        '''
        # 获取配置文件中的语言
        config_langs = self.get_settings()


        # 解析文件中需要翻译的文本
        langs = self.get_src_lang()


        for lang in config_langs:
            # 翻译
            print('正在翻译:',lang['cn'],'=>',lang['name'],'=>',lang['title'],'...')
            self.translate(langs,lang['name'],'server',lang['google'],'baidu')

if __name__ == "__main__":
    # 设置代理
    # os.environ["http_proxy"] = "http://192.168.1.211:10809"
    # os.environ["https_proxy"] = "http://192.168.1.211:10809"
        
    lang = Lang()
    lang.start()
        
    