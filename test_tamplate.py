# 必填项
SOURCE = 'phone_waihu_gzdxspclcsy'    #被测试模板的source
TESTMODE = 4                        #1.批量测试单问题用例 2.对话页模式单节点测试 3.对话页模式 4.批量测试多轮用例
FIRST_NODE = "1开场白"           #第一个节点的节点名称,必须要和模板填写一致。但是如果开场白是获取信息的节点，则填写跳转到的节点名称
START_Q = "开场白"

# 配置信息:批量测试
FILENAME = '2345.csv'                 #测试用例文件名字，不建议修改
OUTPUTNAME = '多轮测试结果2.csv'      #测试报告文件名字，必须以csv结尾

# 配置信息:轮询测试
PATH = '开场白>是的'                     # 测试路径
AUTOPASS = 1                       #自动进入下一轮：1表示会自动进行，0表示不会

# 配置信息:流程测试
FILENAME_2 = '1234.csv'
OUTPUTNAME_2 = '多轮测试结果2.csv'

import requests,json
from urllib import parse
import pandas
from numpy import nan
import re
import traceback
try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda x:x
from colorize import printWarn,printInfo,printError,printHighlight


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
        protocol = json.loads(result)['answer'][0]["protocol"]
        if len(protocol) != 0:
            intentlist = [p["intent"]['value'] for p in protocol if "intent" in p and 'value' in p['intent']]
            intentlist = [i for i in intentlist if i != ""]
            intent = {"value":",".join(intentlist)}
        else:
            intent = {}
        answer_dict['intent'] = intent
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
    
    def callback_multi(self,question) -> dict:
        '''
        本质上还是一次提问,但是对qa的规则进行修饰,提取关键字段:
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
            "filled_slot":"-",
            "isHangup":False
            }


        try:
            # 如果是开场白的情况下，要让返回的答案一定是开场白为止
            if question == self.start_q:
                answer_dict,session_status = qa(self.source,question)
                while session_status["answer_path"][0]["node_name"] != FIRST_NODE:
                   answer_dict,session_status = qa(self.source,question)
            # 否则正常提问,返回answer_dict,session_status
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
        # 如果返回的答案是None,那就是无法解答，非打断失败
        if answer_dict is None:
            callmulti_dict["answer"] = "这个问题无法解答"
            return callmulti_dict

        #触发的标准句trigger
        topic_name = answer_dict["matched_topic_name"]
        # 如果有交互动作
        if answer_dict["display_answer"] != "":
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
                callmulti_dict["isHangup"] = True
            
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
        #如果是打断失败话术
        elif answer_dict["dialog_state"] == "2":
            callmulti_dict["isInterrupt"] = "打断失败"
        #如果是小多轮或者是单轮
        elif not "根节点" in topic_name: 

            #小多轮的情况
            if answer_dict['is_multi_topic']:
                callmulti_dict["topic_name"] = topic_name
                callmulti_dict["nodename"] = session_status["answer_path"][0]["node_name"]
            #标准句的情况
            else:
                callmulti_dict["topic_name"] = topic_name
        # 其他情况 (主节点默认话术)
        else:
            callmulti_dict["nodename"] = session_status["answer_path"][0]["node_name"]
        
        #获取填槽信息
        # TODO:词槽信息获取不对
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
            intent = answer_dict['intent']['value']
            if intent != "":
                callmulti_dict['intent'] = answer_dict['intent']['value']
        return callmulti_dict

    def callback_list(self, path: str):
        # setUp
        try:
            qlist = path.split('>')
        except AttributeError:
            qlist = []
        try:
            for item in qlist:
                section = self.callback_multi(item)["answer"]
        except Exception as e:
            print(2, e)
            traceback.print_exc()
        finally:
            return section
    def callback_list_forscript(self,path:str,new_question:str):
        section = self.callback_list(path)
        try:
            # test
            test_result = self.callback_multi(new_question)
        except Exception as e:
            print(3,e)
            # traceback.print_exc()
        #结果正常时候
        finally:
            return section,test_result
    def display_multiinfo(self,query):
        answer_dict = self.callback_multi(query)
        text = "\n机器人说:" + answer_dict['answer']
        if answer_dict['isInterrupt'] == "-":
            print(text)
        else:
            printError(text)
        if answer_dict['nodename'] != "-":
            printInfo("多轮节点:" + answer_dict['nodename'])
        if answer_dict['filled_slot'] != "-":
            printInfo("填槽信息:" + answer_dict['filled_slot'])
        if answer_dict['topic_name'] != "-":
            printInfo("触达知识库:" + answer_dict['topic_name'])
        if answer_dict['intent'] != "-":
            printHighlight("输出意向:" + answer_dict['intent'])
        return answer_dict
    def __call__(self,question):
        return self.callback_multi(question)

def main1(source,start_q,test_filename):
    a = Source(source, start_q)

    try:
        df = pandas.read_csv(test_filename, encoding='utf8')
    except UnicodeDecodeError:
        df = pandas.read_csv(test_filename, encoding='GBK')
    data = df.iterrows()
    new_df = pandas.DataFrame(columns=["测试节点", "测试路径", "测试场景", "测试问句", "多轮节点", "匹配到的标准句", "回答", "填槽信息", "意向", "打断失败","是否正确（错标0，对标1，用例有问题标2）","问题类型（词库问题、槽位顺序、新知识、等等，按实际写）","优化方案","备注"])
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
            print(4, question, e)
            section, nodename, topic, answer, isInter, filled_slot, intent = "NaN", "NaN", "NaN", "NaN", "NaN", "NaN", "NaN"
        new_df.loc[index] = [node, path, section, question, nodename, topic, answer, filled_slot, intent, isInter, nan, nan, nan, nan]
    print("\n测试完成")
    new_df = new_df.sort_values("测试节点")
    new_df.to_csv(OUTPUTNAME, encoding='utf8', index=False, chunksize=None)


def main2(source):
    a = Source(source, START_Q)
    while True:
        print("测试场景:", a.callback_list(PATH), "\n")
        query = input("你说:")
        a.display_multiinfo(query)
        if not AUTOPASS:
            input()
        print('\n--------Next---------\n')
def main3(source):
    a = Source(source, START_Q)
    while True:
        section = a.callback_multi(START_Q)
        printInfo("开场白")
        print("机器人说:"+section["answer"])
        while not section["isHangup"]:
            query = input("\n你说:")
            section = a.display_multiinfo(query)
        printWarn("结束语挂机")
        print("="*5,"输入回车进入下一轮","="*5)
        input()
def main4(source):
    a = Source(source, START_Q)
    try:
        df = pandas.read_csv(FILENAME_2, encoding='utf8')
    except UnicodeDecodeError:
        df = pandas.read_csv(FILENAME_2, encoding='GBK')
    data = df.iterrows()
    new_df = pandas.DataFrame(columns=["场景序号", "测试问句", "回答", "多轮节点", "匹配到的标准句", "填槽信息", "意向", "打断失败","意向路径"])
    row_count = df.shape[0]
    intentpath = []
    for item in tqdm(data):
        index = item[0]
        group = item[1][0]
        question = item[1][1]
        print("\r", "{:.1%}...正在测试第 {} 组".format((index + 1) / row_count,group), end="")
        try:
            test_result = a.callback_multi(question)
            nodename, topic, answer, isInter, filled_slot, intent = test_result["nodename"], test_result["topic_name"], \
                                                                    test_result["answer"], test_result["isInterrupt"], \
                                                                    test_result["filled_slot"], test_result["intent"]
            if intent != "-":
                intentpath.append(intent)
            filled_slot = filled_slot.split(".")[-1]
        except Exception as e:
            print(4, question, e)
            nodename, topic, answer, isInter, filled_slot, intent = "NaN", "NaN", "NaN", "NaN", "NaN", "NaN","NaN"
        # 意向路径
        if index == row_count-1 or df.loc[index][0] != df.loc[index+1][0]:
            intentpath_str = "-".join(intentpath)
            intentpath = []
        else:
            intentpath_str = "-"
        new_df.loc[index] = [group, question, answer, nodename, topic,  filled_slot, intent, isInter,intentpath_str]
    print("\n测试完成")
    new_df.to_csv(OUTPUTNAME_2, encoding='utf8', index=False, chunksize=None,)
if __name__ == '__main__':
    if TESTMODE == 1:
        main1(SOURCE,START_Q,FILENAME)
    elif TESTMODE == 2:
        main2(SOURCE)
    elif TESTMODE == 3:
        main3(SOURCE)
    elif TESTMODE == 4:
        main4(SOURCE)