"""
需要解决的问题

- 导致异常的原因，触发标准句可能是否定意图

"""
# import xlwings as xw
import requests,json
from urllib import parse
import numpy,pandas
import re


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
        1.默认不说话往下走，自动回复【好的】
        2.如果问句是开场白，一定要让返回的答案是【开场白】才行
        '''
        try:
            answer_dict,answer_path = qa(self.source,question)
            #如果是开场白的情况下，要让返回的答案一定是开场白为止
            if question == self.start_q:
#                 while answer_path["node_name"] != self.start_q: #如果节点名称是1.1 开场白,那将进入死循环
                while not "开场白" in answer_path["node_name"]:
                   answer_dict,answer_path = qa(self.source,question)
                   
        except KeyError:
            raise KeyError
        if answer_dict is None:
            return "这个问题无法解答"
        
        #答案
        answer = answer_dict['answer']
        #触发的标准句trigger
        topic_name = answer_dict["matched_topic_name"]
        
        
        if answer_dict["display_answer"] != "": #如果有交互动作
            #默认不说话往下走的情况
            if json.loads(answer_dict["display_answer"])["action"] == "mute_query": 
                answer = answer+'*默认不说话*\n'+self.callback_multi('好的')
                return answer
            
            #结束语的情况
            elif json.loads(answer_dict["display_answer"])["action"] == "hangup": 
                return f'【结束语:{topic_name}】'+answer
            
            #重播的情况
            elif json.loads(answer_dict["display_answer"])["action"] == "replay": 
                return f'【{topic_name}】'+answer
            #打断不填槽的情况
            elif json.loads(answer_dict["display_answer"])["action"] == "interrupt_not_slot":
                return f'【{topic_name}】'+answer
            else:
                print("未知交互动作："+answer_dict["display_answer"])
                return f'{answer_path["node_name"]}||'+answer
        #打断话术
        elif answer_dict["dialog_state"] == "2":
            return '[打断失败话术]'+answer
        
        elif not "根节点" in topic_name: 

            #小多轮的情况
            if answer_dict['is_multi_topic']:
                return f'{answer}[{topic_name}]'
            #标准句的情况
            else:
                return f'【{topic_name}】{answer}'
        
        else:  #其他 (主节点默认话术)
            return f'{answer_path["node_name"]}||'+answer
    
    
    def callback_list_forscript(self,path:str,new_question:str):
        
        # setUp
        try:
            qlist = path.split('>')
        except AttributeError:
            qlist = []
        try:
            for item in qlist:
                section = self.callback_multi(item)
            
            # test
            answer = self.callback_multi(new_question)
        
        #发生KeyError错误时
        except KeyError:
            qa(self.source,self.end_q) #tearDown
            return section,"KeyError",'-','-'
        
        except Exception as e:
            print(2,e)
            qa(self.source,self.end_q) #tearDown
            return section,"OtherError",'-','-'
        
        #结果正常时候
        else:
            
            if '[打断失败话术]' in answer:
                return section,answer,'打断失败','-'
            elif all(['【' in answer,not '小多轮' in answer,not '结束语' in answer]):
                topic = re.findall(r'【(.*)】',answer)[0]
                return section,answer,'-',topic
            else:
                return section,answer,'-','-'
    
    def __call__(self,question):
        return self.callback_multi(question)

if __name__ == '__main__':
    source = 'phone_waihu_hcrzrqclhf'
    a= Source(source,end_q="开场白")

    
    df = pandas.read_csv('2345.csv',encoding='GBK')
    data = df.iterrows()
    new_df = pandas.DataFrame(columns=["测试节点","测试路径","测试场景","测试问句","回答","打断失败","匹配到的标准句"])
    row_count = df.shape[0]
    for item in data:
        index = item[0]
        node = item[1][0]
        path = item[1][1]
        question = item[1][2]
        print("\r","{:.1%}".format((index+1)/row_count),end="")
        section,answer,isInter,topic = a.callback_list_forscript(path,question)
        new_df.loc[index] = [node,path,section,question,answer,isInter,topic]
    print("\n测试完成")        
    new_df.to_csv('多轮测试结果.csv',encoding='utf8',index=False,chunksize=None)