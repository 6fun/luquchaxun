from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import pandas as pd
import random
import string
from pathlib import Path
from contextlib import asynccontextmanager

# 生成验证码的字符集（纯数字）
CAPTCHA_CHARS = string.digits

@asynccontextmanager
async def lifespan(app: FastAPI):
    """生命周期管理，启动时加载数据"""
    try:
        # 加载数据
        data_dir = Path("data")
        files = list(data_dir.glob("*.xlsx"))
        
        if not files:
            raise RuntimeError("未找到Excel文件")
        
        # 读取第一个文件
        file_path = files[0]
        df = pd.read_excel(file_path, sheet_name=0, engine='openpyxl')
        
        # 验证必要字段
        required_columns = {"姓名", "考生号"}
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            raise RuntimeError(f"缺少必要字段: {', '.join(missing)}")
        
        # 将数据保存到应用状态
        df[['考生号']] = df[['考生号']].astype(str)
        app.state.df = df
        app.state.data_loaded = True
        
        yield
    
    except Exception as e:
        print(f"程序启动失败: {str(e)}")
        raise

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 配置会话中间件（生产环境应使用更安全的密钥）
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secure-key-123!@#",
    session_cookie="secure_session"
)

def generate_captcha(length=4):
    """生成数字验证码"""
    return ''.join(random.choices(CAPTCHA_CHARS, k=length))

@app.get("/", response_class=HTMLResponse)
async def query_form(request: Request):
    """显示查询表单"""
    captcha = generate_captcha()
    request.session["captcha"] = captcha
    return templates.TemplateResponse("form.html", {
        "request": request,
        "captcha": captcha
    })

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        data_dir = Path("data")
        files = list(data_dir.glob("*.xlsx"))
        
        if not files:
            raise RuntimeError("未找到Excel文件")
        
        file_path = files[0]
        # 关键修改：指定字段类型为字符串
        df = pd.read_excel(
            file_path,
            sheet_name=0,
            engine='openpyxl',
            dtype={"姓名": str, "考生号": str}  # 强制转换为字符串类型
        )
        
        # 清洗数据：去除首尾空格
        df["姓名"] = df["姓名"].str.strip()
        df["考生号"] = df["考生号"].str.strip()
        
        # 验证字段
        required_columns = {"姓名", "考生号"}
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            raise RuntimeError(f"缺少必要字段: {', '.join(missing)}")
        
        app.state.df = df
        yield
    
    except Exception as e:
        print(f"程序启动失败: {str(e)}")
        raise

# 修改后的查询部分
@app.post("/search/", response_class=HTMLResponse)
async def search_data(
    request: Request,
    name: str = Form(...),
    examinee_id: str = Form(...),
    captcha_input: str = Form(...)
):
    # 验证部分保持不变...
    
    # 获取数据
    df = app.state.df
    
    # 清洗输入数据
    clean_name = name.strip()
    clean_id = examinee_id.strip()
    
    # 执行查询
    result = df[
        (df["姓名"] == clean_name) & 
        (df["考生号"] == clean_id)
    ]

    # 生成新验证码
    new_captcha = generate_captcha()
    request.session["captcha"] = new_captcha
    
    if not result.empty:
        record = result.iloc[0].to_dict()
        return templates.TemplateResponse("result.html", {
            "request": request,
            "exists": True,
            "record": record,
            "captcha": new_captcha
        })
    
    return templates.TemplateResponse("result.html", {
        "request": request,
        "exists": False,
        "captcha": new_captcha
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)