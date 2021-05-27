# 填写关键信息
SOURCE = 'phone_waihu_hdhseyd'    #被测试模板的source
PATH = '开场白'                      #测试路径，问题与问题之间用>隔开

START_Q = "开场白"                        #模板的模板场景，一般情况下默认值是开场白，适当情况下可以改成"kaichangbai"或者"Kai Chang Bai"

# import xlwings as xw
import requests,json
from urllib import parse
import numpy,pandas
import time



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
        
        try:#待解决:模板测试有问题,phone_waihu_hccybclhf当中遇到默认不说话返回的answer_path为空列表
            answer_path = json.loads(session_status)['answer_path'][0]#包含节点路径，填槽信息等内容
        except:
            '''
                以下情况会触发警报
                1.遇到接口节点，对话页无法获取信息一直打断失败
                2.本身就无法回答的打断失败
            '''
            answer_path = {}
            print(session_status)
        answer_dict = json.loads(content)# 包含答案、答案类型等信息
        return answer_dict,answer_path


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
            answer_dict,answer_path = qa(self.source,question)
            #如果是开场白的情况下，要让返回的答案一定是开场白为止
            if question == self.start_q:
                while not "开场白" in answer_path["node_name"]:
                   answer_dict,answer_path = qa(self.source,question)
            #填入答案
            callmulti_dict["answer"] = answer_dict['answer']
            #触发的标准句trigger,不一定要填入
            topic_name = answer_dict["matched_topic_name"]
        except KeyError:
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
                callmulti_dict["nodename"] = answer_path["node_name"]
            
            #结束语的情况
            elif json.loads(answer_dict["display_answer"])["action"] == "hangup": 
                #如果是多轮结束语
                if answer_dict["is_multi_topic"]:
                    callmulti_dict["nodename"] = answer_path["node_name"]
                else:
                    callmulti_dict["topic_name"] = topic_name
            
            #重播的情况
            elif json.loads(answer_dict["display_answer"])["action"] == "replay": 
                callmulti_dict["topic_name"] = topic_name
            #打断不填槽的情况
            elif json.loads(answer_dict["display_answer"])["action"] == "interrupt_not_slot":
                callmulti_dict["nodename"] = answer_path["node_name"]
            
            else:
                print("未知交互动作："+answer_dict["display_answer"])
                callmulti_dict["nodename"] = answer_path["node_name"]
                callmulti_dict["topic_name"] = topic_name
                callmulti_dict["remark"] = answer_path
        
        #如果是打断话术
        elif answer_dict["dialog_state"] == "2":
            callmulti_dict["isInterrupt"] = "打断失败"
        
        elif not "根节点" in topic_name: 

            #小多轮的情况
            if answer_dict['is_multi_topic']:
                callmulti_dict["topic_name"] = topic_name
                callmulti_dict["nodename"] = answer_path["node_name"]
            #标准句的情况
            else:
                callmulti_dict["topic_name"] = topic_name
        
        else:  #其他 (主节点默认话术)
            callmulti_dict["nodename"] = answer_path["node_name"]
        return callmulti_dict
    
    
    def callback_list(self,path:str):
        
        # setUp
        try:
            qlist = path.split('>')
        except AttributeError:
            qlist = []
        try:
            for item in qlist:
                section = self.callback_multi(item)["answer"]
        
        except Exception as e:
            print(2,e)
        #结果正常时候
        finally:
            return section
    
    def __call__(self,question):
        return self.callback_multi(question)

if __name__ == '__main__':
    source = SOURCE
    a= Source(source,start_q=START_Q)
    
    while True:
        print("测试场景:",a.callback_list(PATH),"\n")
        query = input("你说:")
        print("\n机器人说:",a.callback_list(query))
#         input()
        print('\n--------Next---------\n')


