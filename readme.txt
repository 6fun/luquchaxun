本系统为录取查询系统
1. 只需把excel文件（需要扩展名为.xlsx）放入data目录下即可，excel文件中，查询必需的字段为“考生号”和“姓名”，其他字段随意。
2. 本系统采用把数据全部读入内存后在内存中查询，性能极好。
3. 本系统是采用 python 开发，依赖多个开源框架，安装后请在命令行运行如下指令，即可安装成功依赖。
pip install fastapi uvicorn pandas openpyxl python-multipart itsdangerous
4、运行，windows下可以直接点击 run.bat运行，可以使用命令行 运行如下指令：
uvicorn main:app --reload
