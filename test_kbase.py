# 填写关键信息
SOURCE = 'phone_waihu_xxjdsqyyhf'    #被测试模板的source
FILENAME = '123.csv'                     #测试集文件，需要是csv文件



# import xlwings as xw
import requests,json
from urllib import parse
import pandas


def qa(source,q,autoBreak=0):
    if q == "收到":
        q = "是的"
    
    url = f'http://vopoc.ths123.com//brokerageController/center/?question={parse.quote(q)}&source={source}&user_id=8lodfmmu9llq798rnazsaff5fesseq40'
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
        answer_path = json.loads(session_status)
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
    source = SOURCE
    a= Source(source)
    
#     while True:
#         print(a.callback_list("开场白-方便"))
#         print('\n'+'--------Next---------')
    
    try:
        df = pandas.read_csv(FILENAME,encoding='GBK')
    except UnicodeDecodeError:
        df = pandas.read_csv(FILENAME,encoding='utf8')
    data = df.iterrows()
    new_df = pandas.DataFrame(columns=["测试问句","匹配到的标准句","标准句","是否正确"])
    row_count = df.shape[0]
    wrong_standar = set()
    for item in data:
        index = item[0]
        question = item[1][0]
        standar = item[1][1]
        print("\r","{:.1%}".format((index+1)/row_count),end="")
        try:
            #询问问句
            answer_dict,answer_path = a(question)
            
            #方案一:遇到是小多轮的情况，就重复说"好的"，直到返回的是结束语
            matched_topic = answer_dict['matched_topic_name']
            if matched_topic!=standar:
                wrong_standar.add(standar)
            if answer_dict["is_multi_topic"]:
                while not "hangup" in answer_dict["display_answer"]:
                    answer_dict,answer_path = a("好的")
            
            
            #方案二:小多轮后面跟着场景信息的节点会陷入死循环，目前无法解决，循环次数超过15次会break，输出建议手动测试
#             while answer_path["session_round"] !=1 and answer_dict["is_multi_topic"]: #当触发的是小多轮后面的主节点
# #                 print(666,question,answer_path["session_round"],answer_dict['matched_topic_name'])
#                 if answer_path["session_round"] >14:
#                     break
#                 answer_dict,answer_path = a(question)
#             matched_topic = answer_dict['matched_topic_name']
            
            
        except KeyError as e:
#             print(question,"￥无法回答￥","")
            matched_topic = "NaN"
            wrong_standar.add(standar)
        except Exception as e:
            print(3,e)
            matched_topic = "NaN"
            wrong_standar.add(standar)
        
        new_df.loc[index] = [question,matched_topic,standar,1 if matched_topic==standar else 0]  
    
    print(f"知识库数量\t正确数\t正确率\n{row_count}\t{new_df.是否正确.sum()}\t{new_df.是否正确.sum()/row_count:.2%}")
    if len(wrong_standar) > 0:
        print("\n错误标准句如下:")
        for w in wrong_standar:
            print(w)
    new_df.to_csv('知识库测试结果.csv',encoding='utf8',index=False)
