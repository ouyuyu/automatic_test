"""
需要解决的问题
- 知识库测试的时候怎么知道它是不是走到小多轮里边

- 误触到小多轮当中时候，要走出多轮继续测试(用setUp和tearDown)
    # 打电话有什么事吗 -> 【你们找我有什么事】
    # 您好，您近期有在我店看了一汽大众${carname}车型的车，想花个两分钟，邀请您对于我们的服务体验做一个满意度回访，请问您现在方便吗？  ztqzhf02(这个是主节点)

- 优化成面向对象，class Source()
- 配合链式调用
- 设置函数，用来配置初始条件，*测试语句，收尾条件
"""
# import xlwings as xw
import requests,json
from urllib import parse
# import re

# source = 'phone_waihu_dwzqclhf'
# qa = '你是不是机器人'
def qa(source,q):
    if q == "收到":
        q = "是的"
    
    url = f'http://172.20.208.127:40080/center/?question={parse.quote(q)}&source={source}&user_id=8lodfmmu9llq798rnazsaff5fesseq40'
    resp = requests.get(url)
    result = resp.content.decode('utf8')
#     print(result)
    result_content = json.loads(result)['answer'][0]['txt']
    if result_content == []:
        answer = "这个问题无法解答"
        ismute = False
        topic_name = 'Error'
        ismulti = False
        return None
    else:
        content = result_content[0]['content']
        answer_dict = json.loads(content)
        return json.dumps(answer_dict,ensure_ascii=False)
        answer = answer_dict['answer']
        topic_name = answer_dict["matched_topic_name"]
        ismulti = answer_dict['is_multi_topic']
        ismute = json.loads(answer_dict["display_answer"])["action"] == "mute_query" if answer_dict["display_answer"]!="" else False
        return answer,ismute,topic_name,ismulti

def qaa(source,q):
    a,b,c,d = qa(source,q)
#     print(a,b,c)
    if b == True: #默认不说话往下走的情况
#         print(a,'\n【默认不说话】')
#         a,b,c,d = qa(source,"好的")
        return a
#     elif "再见" in a: #结束语的情况
#         print(f'【结束语:{c}】'+a,'\n')
#         a,b,c,d = qa(source,"开场白")
#         return a
    elif not "根节点" in c: #标准句的情况
        return f'【{c}】{a}'
    else:  #其他 (主节点、回答不上)
        return a

if __name__ == '__main__':
    source = 'phone_waihu_dljyhs'
    print(qa(source,'开场白'))
    
    
    
#     while True:
#         #-------前置条件
#         qaa(source,"开场白")
# #         qaa(source,"北京")
# #         qaa(source,"不用")
# #         qaa(source,"好的")
#         print(qaa(source,"北京"))
#         
#         #-------执行测试语句
#         wd = input("q:")
#         print(qaa(source,wd)) #结果
#         pass #判断规则
#         print("\n-----------------")#测试完成点
#         
#         #-------后置条件
#         print(qaa(source,"4.1 BIM培训结束语"),'\n')
# #         qaa(source,"Jie Shu Yu shibai")



#     bk=xw.Book(r'C:\Users\viruser.v-desktop\Desktop\知识库测试集.xls')
#     sht=bk.sheets[0]
#     wds_fail=[]
#     a_buttum=sht.range('A' + str(sht.cells.last_cell.row)).end('up').row
#     for i in range(1,a_buttum):
#         wd =str(sht.range(f'A{i}').value)
#         answer,ismute,topic_name,ismulti = qa(source,wd)
#         if "这个问题无法解答" in answer:
#             wds_fail.append(wd)
# #         elif ismulti == True:
# #             qa(source,"end_zaimang")
#         else:
#             print(f'{wd} -> 【{topic_name}】\n{answer}\n')
#     print(f"\n共检测出{wds_fail.__len__()}个问句无法回答")
#     print(wds_fail)

#     qa(source,"开场白")
#     qa(source,"帮我办一个吧")
#     qa(source,"好的")
#     qa(source,"不想听")
#     print(qa(source,"不要在讲了。"))