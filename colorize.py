from ctypes import *
def _isIDE():
    try:
        hwnd = windll.user32.GetForegroundWindow()
        out = windll.kernel32.GetStdHandle(-0xb)  # stdin: 0xa, stdout: 0xb, stderr: 0xc
        rtn = windll.kernel32.SetConsoleTextAttribute(out, 0x7)
        return not rtn
    except NameError:
        return False
isIDE = _isIDE()

def clz(a: str, color: str):
    if color == 'red':
        return '\033[31m{}\033[0m'.format(a)
    elif color == 'green':
        return '\033[32m{}\033[0m'.format(a)
    elif color == 'yellow':
        return '\033[33m{}\033[0m'.format(a)
    elif color == 'blue':
        return '\033[34m{}\033[0m'.format(a)
    elif color == 'white':
        return '\033[37m{}\033[0m'.format(a)
    elif color == 'whiteblue':
        return '\033[37;44m{}\033[0m'.format(a)
    else:
        return a


def printError(errorinfo: str):
    if isIDE:
        print(clz(errorinfo, 'red'))
    else:
        print(errorinfo)


def printWarn(warninfo: str):
    if isIDE:
        print(clz(warninfo, 'yellow'))
    else:
        print(warninfo)

def printInfo(info:str):
    if isIDE:
        print(clz(info, 'blue'))
    else:
        print(info)

def printHighlight(info:str):
    if isIDE:
        print(clz(info, 'whiteblue'))
    else:
        print(info)
if __name__ == '__main__':
    # print(clz("123", "red"))
    # printWarn(342453)
    print(clz("123", "whiteblue"))