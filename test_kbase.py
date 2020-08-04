"""
需要解决的问题

- 导致异常的原因，触发标准句可能是否定意图
- 多轮当中显示进入哪个子节点

"""
# import xlwings as xw
import requests,json
from urllib import parse
import numpy,pandas
import re
# import re

# source = 'phone_waihu_dwzqclhf'
# qa = '你是不是机器人'
def qa(source,q,autoBreak=0):
    if q == "收到":
        q = "是的"
    
    url = f'http://vopoc.ths123.com/brokerageController/center/?question={parse.quote(q)}&source={source}&user_id=8lodfmmu9llq798rnazsaff5fesseq40'
    resp = requests.get(url)
    result = resp.content.decode('utf8')
#     print(result)
    try:
        result_content = json.loads(result)['answer'][0]['txt']
        session_status = json.loads(result)['answer'][0]['session_status']
    except KeyError:
#         print('【异常警告】:result=',json.loads(result),'\tq=',q)
        if autoBreak:
            exit()
        else:
            raise KeyError
    except Exception as e:
        print(1,e)
        if autoBreak:
            exit()
        else:
            raise KeyError
    if result_content == []:
#         answer = "这个问题无法解答"
#         ismute = False
#         topic_name = 'Error'
#         ismulti = False
        return None,None
    else:
        content = result_content[0]['content']
        answer_path = json.loads(session_status)['answer_path']
        answer_dict = json.loads(content)
        return answer_dict,answer_path


class Source(object):
    def __init__(self,source,start_q="开场白",end_q="结束语",testmode=False):
        self.source = source
        self.start_q = start_q
        self.end_q = end_q
    
    def __call__(self,question):
        return qa(self.source,question)

if __name__ == '__main__':
    source = 'phone_waihu_zzmfkd'
    a= Source(source,end_q='送多少兆的宽带')
    
#     while True:
#         print(a.callback_list("开场白-方便"))
#         print('\n'+'--------Next---------')
    
    df = pandas.read_csv('123.csv',encoding='GBK')
    data = df.iterrows()
    new_df = pandas.DataFrame(columns=["测试问句","匹配到的标准句","是否正确"])
    for item in data:
        index = item[0]
        question = item[1][0]
        standar = item[1][1]
        try:
            #询问问句
            answer_dict,answer_path = a(question)
            matched_topic = answer_dict['matched_topic_name']
#             print(question,matched_topic,f"【{answer_dict['display_answer']}】")
            
        except KeyError as e:
#             print(question,"￥无法回答￥","")
            matched_topic = "NaN"
        except Exception as e:
            print(3,e)
            matched_topic = "NaN"
        
        new_df.loc[index] = [question,matched_topic,False]       
    new_df.to_csv('知识库测试结果.csv',encoding='utf8',index=False)