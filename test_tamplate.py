# 填写关键信息
SOURCE = 'phone_waihu_pkzsbcsymb'    #被测试模板的source
FILENAME = '2345.csv'                 #测试用例文件名字，不建议修改

# 配置信息 - 一般情况
START_Q = "开场白"
"""
模板的模板场景，即开场白节点触发标准句，用作路径生效，如果出现输入路径但是测试场景不匹配的情况下进行修改。
一般情况下默认值是开场白，适当情况下可以改成"kaichangbai"或者"Kai Chang Bai"。
"""

FIRST_NODE = "开场白"
"""
第一个节点的节点名称，用作路径生效，如果出现输入路径但是测试场景不匹配的情况下进行修改。
一般情况下默认值是开场白。
"""

import requests,json
from urllib import parse
import pandas
import re
import traceback
try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda x:x


def qa(source,q,autoBreak=0):
    '''
    简单的QA函数，输入问句，直接返回答案
    如果是异常情况，则返回KeyError
    正常情况下返回:
    content词典
    
    '''
    if q == "收到":
        q = "是的"
    
    url = f'http://vopoc.ths123.com/brokerageController/center/?question={parse.quote(q)}&source={source}&user_id=8lodfmmu9llq798rnazsaff5fesseq40'
    resp = requests.get(url)
    result = resp.content.decode('utf8')
    try:
        result_content = json.loads(result)['answer'][0]['txt']
        session_status = json.loads(result)['answer'][0]['session_status']
    except KeyError:
        print('【异常警告】:result=',json.loads(result),'\tq=',q)
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
        return None,None
    else:
        content = result_content[0]['content']
        session_status = json.loads(session_status)#包含节点路径，填槽信息等内容
        answer_dict = json.loads(content)# 包含答案、答案类型等信息
        #在answer_dict中插入意向信息
        answer_dict['intent'] = json.loads(result)['answer'][0]["protocol"][0]["intent"] if len(json.loads(result)['answer'][0]["protocol"]) != 0 else {}
        return answer_dict,session_status
#         try:#待解决:模板测试有问题,phone_waihu_hccybclhf当中遇到默认不说话返回的answer_path为空列表
#             answer_path = json.loads(session_status)['answer_path'][0]#包含节点路径，填槽信息等内容
#         except:
#             '''
#                 以下情况会触发警报
#                 1.遇到接口节点，对话页无法获取信息一直打断失败
#                 2.本身就无法回答的打断失败
#             '''
#             answer_path = {}
#             print(session_status)
#         answer_dict = json.loads(content)# 包含答案、答案类型等信息
#         return answer_dict,answer_path


class Source(object):
    def __init__(self,source,start_q="开场白",end_q="结束语",testmode=False):
        self.source = source
        self.start_q = start_q
        self.end_q = end_q
    
    def callback_multi(self,question):
        '''
        对qa的规则修饰:
        1.如果问句是开场白，一定要让返回的答案是【开场白】才行
        '''
        #输出模板默认数据
        callmulti_dict = {
            "nodename":"-",
            "topic_name":"-",
            "answer":"-",
            "isInterrupt":"-",
            "remark":"-",
            "intent":"-",
            "filled_slot":"-"
            }

        try:
            #如果是开场白的情况下，要让返回的答案一定是开场白为止
            if question == self.start_q:
                answer_dict,session_status = qa(self.source,question)
                while session_status["answer_path"][0]["node_name"] != FIRST_NODE:
                   answer_dict,session_status = qa(self.source,question)
            else:
                answer_dict,session_status = qa(self.source,question)
            #填入答案
            callmulti_dict["answer"] = answer_dict['answer']
            #触发的标准句trigger,不一定要填入
            topic_name = answer_dict["matched_topic_name"]
        except KeyError:
#             traceback.print_exc()
            print(KeyError,question)
            return callmulti_dict
        if answer_dict is None:
            callmulti_dict["answer"] = "这个问题无法解答"
            return callmulti_dict
        
        #答案
        answer = answer_dict['answer']
        #触发的标准句trigger
        topic_name = answer_dict["matched_topic_name"]
        
        if answer_dict["display_answer"] != "": #如果有交互动作
            #默认不说话往下走的情况
            if json.loads(answer_dict["display_answer"])["action"] == "mute_query": 
                callmulti_dict["nodename"] = session_status["answer_path"][0]["node_name"]
            
            #结束语的情况
            elif json.loads(answer_dict["display_answer"])["action"] == "hangup": 
                #如果是多轮结束语
                if answer_dict["is_multi_topic"]:
                    callmulti_dict["nodename"] = session_status["answer_path"][0]["node_name"]
                else:
                    callmulti_dict["topic_name"] = topic_name
            
            #重播的情况
            elif json.loads(answer_dict["display_answer"])["action"] == "replay": 
                callmulti_dict["topic_name"] = topic_name
            #打断不填槽的情况
            elif json.loads(answer_dict["display_answer"])["action"] == "interrupt_not_slot":
                callmulti_dict["nodename"] = session_status["answer_path"][0]["node_name"]
            
            else:
                print("未知交互动作："+answer_dict["display_answer"])
                callmulti_dict["nodename"] = session_status["answer_path"][0]["node_name"]
                callmulti_dict["topic_name"] = topic_name
                callmulti_dict["remark"] = session_status["answer_path"][0]
        
        #如果是打断话术
        elif answer_dict["dialog_state"] == "2":
            callmulti_dict["isInterrupt"] = "打断失败"
        
        elif not "根节点" in topic_name: 

            #小多轮的情况
            if answer_dict['is_multi_topic']:
                callmulti_dict["topic_name"] = topic_name
                callmulti_dict["nodename"] = session_status["answer_path"][0]["node_name"]
            #标准句的情况
            else:
                callmulti_dict["topic_name"] = topic_name
        
        else:  #其他 (主节点默认话术)
            callmulti_dict["nodename"] = session_status["answer_path"][0]["node_name"]
        
        #获取填槽信息
        if len(session_status["filled_slot"])>0:
            session_status["filled_slot"].sort(key=lambda x:x["pass_round"])
            filled_slot = session_status["filled_slot"][0]
            word_type = filled_slot["word_type"]
            if "input_question" in word_type:
                word_type = "用户说话"
            word_value = filled_slot["value"]
            callmulti_dict["filled_slot"] = f"{word_type}"
        #获取意向信息
        if answer_dict['intent'] != {}:
            callmulti_dict['intent'] = answer_dict['intent']['value']
        return callmulti_dict
    
    
    def callback_list_forscript(self,path:str,new_question:str):
        
        # setUp
        try:
            qlist = path.split('>')
        except AttributeError:
            qlist = []
        try:
            for item in qlist:
                section = self.callback_multi(item)["answer"]
            # test
            test_result = self.callback_multi(new_question)
        
        except Exception as e:
            print(2,e)
            # traceback.print_exc()
        #结果正常时候
        finally:
            return section,test_result
    
    def __call__(self,question):
        return self.callback_multi(question)

def main1(source,start_q,test_filename):
    a = Source(source, start_q)

    try:
        df = pandas.read_csv(test_filename, encoding='utf8')
    except UnicodeDecodeError:
        df = pandas.read_csv(test_filename, encoding='GBK')
    data = df.iterrows()
    new_df = pandas.DataFrame(columns=["测试节点", "测试路径", "测试场景", "测试问句", "多轮节点", "匹配到的标准句", "回答", "填槽信息", "意向", "打断失败"])
    row_count = df.shape[0]
    for item in tqdm(data):
        index = item[0]
        node = item[1][0]
        path = item[1][1]
        question = item[1][2]
        print("\r", "{:.1%}".format((index + 1) / row_count), end="")
        try:
            section, test_result = a.callback_list_forscript(path, question)
            nodename, topic, answer, isInter, filled_slot, intent = test_result["nodename"], test_result["topic_name"], \
                                                                    test_result["answer"], test_result["isInterrupt"], \
                                                                    test_result["filled_slot"], test_result["intent"]
        except Exception as e:
            print(3, question, e)
            section, nodename, topic, answer, isInter, filled_slot, intent = "NaN", "NaN", "NaN", "NaN", "NaN", "NaN", "NaN"
        new_df.loc[index] = [node, path, section, question, nodename, topic, answer, filled_slot, intent, isInter]
    print("\n测试完成")
    new_df.to_csv('多轮测试结果.csv', encoding='utf8', index=False, chunksize=None)

def main2(source,start_q,test_filename):
    a = Source(source, start_q)
    try:
        df = pandas.read_csv(test_filename, encoding='utf8')
    except UnicodeDecodeError:
        df = pandas.read_csv(test_filename, encoding='GBK')
    data = df.iterrows()
    new_df = pandas.DataFrame(columns=["测试节点", "测试路径", "测试场景", "测试问句", "多轮节点", "匹配到的标准句", "回答", "填槽信息", "意向", "打断失败"])
    row_count = df.shape[0]
    
if __name__ == '__main__':
    main1(SOURCE,START_Q,FILENAME)