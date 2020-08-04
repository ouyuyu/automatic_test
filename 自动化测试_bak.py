"""
需要解决的问题
知识库测试的时候怎么知道它是不是走到小多轮里边
辨别新知识

"""
import xlwings as xw
import requests,json
from urllib import parse
import re

# source = 'phone_waihu_dwzqclhf'
# qa = '你是不是机器人'
def qa(source,q):
    if q == "收到":
        q = "是的"
    
    url = f'http://172.20.208.127:40080/center/?question={parse.quote(q)}&source={source}&user_id=8lodfmmu9llq798rnazsaff5fesseq40'
    resp = requests.get(url)
    result = resp.content.decode('utf8')
    result_content = json.loads(result)['answer'][0]['txt']
    if result_content == []:
        answer = "这个问题无法解答"
        return answer
    else:
        content = result_content[0]['content']
        answer = json.loads(content)['answer']
        topic_name = json.loads(content)["matched_topic_name"]
        if "根节点" in topic_name:
            return answer
        elif "开场白" in topic_name:
            return answer
        elif "end" in topic_name or "结束语" in topic_name:
            return answer
        else:
            return answer,topic_name
def qaa(source,q):
    a = qa(source,q)
    if a == "\\" or a == "/":
        print('/')
        a = qa(source,"好的")
    elif "再见" in a:
        print(a,'\n')
        a = qa(source,"开场白")
#     elif not "吗？" in a or "吗?" in a:
#         a = qa(source,"好的")
    return a
if __name__ == '__main__':
    source = 'phone_waihu_zxzqfxq'
    
#     while True:
#         wd = input("q:")
#         print(qaa(source,wd))


    print(123)
    bk=xw.Book(r'C:\Users\viruser.v-desktop\Desktop\知识库测试集.xls')
    sht=bk.sheets[0]
    wds_fail=[]
    print(123)
    a_buttum=sht.range('A' + str(sht.cells.last_cell.row)).end('up').row
    for i in range(1,a_buttum):
        wd =str(sht.range(f'A{i}').value)
        answer = qa(source,wd)
        if "这个问题无法解答" in answer:
            wds_fail.append(wd)
        else:
            print(f'{wd} -> 【{answer[1]}】\n{answer[0]}\n')
    print(f"\n共检测出{wds_fail.__len__()}个问句无法回答")
    print(wds_fail)

#     qa(source,"开场白")
#     qa(source,"方便")
#     qa(source,"好的")
#     qa(source,"不想听")
#     print(qa(source,"不要在讲了。"))