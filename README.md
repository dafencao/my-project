<!--
 * @Author: 嘉欣 罗 2592734121@qq.com
 * @Date: 2022-12-22 12:49:07
 * @LastEditors: 嘉欣 罗 2592734121@qq.com
 * @LastEditTime: 2022-12-26 19:53:56
 * @FilePath: \psad-backend\README.md
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
-->

# 产品选型与设计平台后端

#### backend for product selection and design platform

# 环境

```
python3.8
```

## 安装依赖包

```
pip install -r requirements.txt -i http://pypi.douban.com/simple --trusted-host pypi.douban.com
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
清华源
```

若报错：

```
distutils.errors.DistutilsPlatformError: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools":https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

打开链接下载 Microsoft C++ 生成工具

## 配置数据库环境

安装 mysql 8.0

运行/db/mysql/psad.sql 数据库文件

/core/config/config.py 配置 MySQL 数据库 IP 地址、端口号、用户名和密码等

## 修改前后端对应 IP 地址和端口号

/main.py:

```
    uvicorn.run(
        app='main:app',
        host="x.x.x.x",
        port=xxxx,
        reload=True,
        # debug=True
        )
```

## 启动

```
cd psad-backend
python ./main.py
```

## api 文档

http://127.0.0.1:8010/api/docs

## 官方文档：

- Peewee
- https://www.osgeo.cn/peewee
- FastAPI
- https://fastapi.tiangolo.com/tutorial/sql-databases/
- Pydantic
- https://docs.pydantic.dev/

## 一些开发规范和参考

- FastAPI and MySQL - 项目生成器
- https://gitee.com/switchwg/fastapi-mysql-generator
-
- Fastapi 接口文档注释
- https://zhuanlan.zhihu.com/p/336032542
-
- fastapi+peewee
- https://juejin.cn/post/6844904099457024008
-
- python中的orm：peewee和peewee_async
- https://www.cnblogs.com/traditional/p/11326736.html
- 
- peewee与异步操作 
- https://www.jianshu.com/p/a7e639e62a16
- 
- peewee 同步、异步、断线重连、连接池 
- https://www.cnblogs.com/gcxblogs/p/14969019.html
- 
- FastAPI如何关闭接口文档？ 
- https://cloud.tencent.com/developer/article/1697199
- 
- FastAPI SwaggerUI静态资源
- https://www.cnblogs.com/darling331/p/16348634.html
- 
- kafka安装
- https://www.jianshu.com/p/ddb061a78f65
## 注：

vscode 隐藏**pycache**:
ctrl+shift+p 搜索 User Settings 打开
搜索 file.exclude
添加

```
**/__pycache__
```
xuange