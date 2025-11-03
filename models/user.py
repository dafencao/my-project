"""
纯增删改查操作，写在model里面
"""

from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, IntegerField, ForeignKeyField, DateTimeField
from playhouse.shortcuts import model_to_dict, dict_to_model
from sqlalchemy.orm import relationship
from models.userrole import Userrole
from schemas.request import sys_user_schema
from core import security
from peewee import fn, JOIN
import datetime

from utils.tools_func import convert_arr, convert_num_arr


# 用户类


class Level(BaseModel):
    """
    部门表，
    """
    id = IntegerField(primary_key=True)
    name = CharField()
    code = CharField()

    class Meta:
        table_name = 'level'  # 自定义映射的表名

    class Config:
        orm_mode = True

    @classmethod
    async def add(cls, level):  # 获取
        return await async_db.create(Level, **level)

    @classmethod
    async def delete_by_id(cls, id):  # 获取
        return await async_db.execute(
            Level.delete().where(Level.id == id))

    @classmethod
    async def update_by_model(cls, model):  # 获取
        return await async_db.execute(
            model.save())

    @classmethod
    async def select_all(cls):  # 获取
        db = await async_db.execute(Level.select().dicts())
        if db:
            result = list(db)
        else:
            result = []
        return result


# TODO:Userpost=>Post


class Userpost(BaseModel):
    """
    岗位表，
    """
    id = IntegerField(primary_key=True)
    name = CharField()  # 岗位
    code = CharField()

    class Meta:
        table_name = 'userpost'  # 自定义映射的表名

    # 也可以根据类名选择表的名称
    # class Meta:
    #     database = db

    class Config:
        orm_mode = True

    @classmethod
    async def add(cls, post):  # 获取
        return await async_db.create(Userpost, **post)

    @classmethod
    async def delete_by_id(cls, id):  # 获取
        return await async_db.execute(
            Userpost.delete().where(Userpost.id == id))

    @classmethod
    async def update_by_model(cls, model):  # 获取
        return await async_db.execute(
            model.save())

    @classmethod
    async def select_all(cls):  # 获取
        db = await async_db.execute(Userpost.select().dicts())
        if db:
            result = list(db)
        else:
            result = []
        return result


# TODO:Userline=>Line /ProductLine
class Userline(BaseModel):
    """
    产品线表
    """
    id = IntegerField(primary_key=True)
    name = CharField()  # 所属产品线
    code = CharField()

    class Meta:
        table_name = 'userline'  # 自定义映射的表名

    # 也可以根据类名选择表的名称
    # class Meta:
    #     database = db

    class Config:
        orm_mode = True

    @classmethod
    async def select_all(cls):  # 获取
        db = await async_db.execute(Userline.select().dicts())
        if db:
            result = list(db)
        else:
            result = []
        return result

    @classmethod
    async def add(cls, line: dict):  # 添加
        result = await async_db.create(Userpost, **line)
        return result

    @classmethod
    async def delete_by_id(cls, id):  # 获取
        return await async_db.execute(
            Userline.delete().where(Userline.id == id))

    @classmethod
    async def update_by_model(cls, model):  # 更新
        # print("update name")
        # print(name)

        # c = Userline.create(id=id,
        #                     name=name,
        #                     update_at=datetime.date.today())
        result = await async_db.execute(model.save())
        return result


class Department(BaseModel):
    """
    部门表，
    """
    id = IntegerField(primary_key=True)
    name = CharField()
    code = CharField()

    class Meta:
        table_name = 'department'  # 自定义映射的表名

    class Config:
        orm_mode = True

    @classmethod
    async def select_all(cls):  # 获取
        db = await async_db.execute(Department.select().dicts())
        if db:
            result = list(db)
        else:
            result = []
        return result

    @classmethod
    async def delete_by_id(cls, id):  # 获取
        return await async_db.execute(
            Department.delete().where(Department.id == id))


class UserLineRelp(BaseModel):
    """
    用户所属产品线表
    """
    id = IntegerField(primary_key=True)
    # user_id = IntegerField()
    # line_id = IntegerField()
    userId = IntegerField(column_name='user_id')
    lineId = IntegerField(column_name='line_id')

    class Meta:
        table_name = 'user_line_relp'  # 自定义映射的表名

    class Config:
        orm_mode = True

    @classmethod
    async def add(cls, relp: dict):  # 添加
        result = await async_db.create(UserLineRelp, **relp)
        return result

    @classmethod
    async def delete_by_userId(cls, id):  # 获取
        return await async_db.execute(
            UserLineRelp.delete().where(UserLineRelp.userId == id))

    @classmethod
    async def delete_by_userId_and_lineId(cls, userId, lineId):  # 获取
        return await async_db.execute(
            UserLineRelp.delete().where(
                UserLineRelp.lineId == lineId, UserLineRelp.userId == userId))


class UserPostRelp(BaseModel):
    """
    用户所属岗位表
    """
    id = IntegerField(primary_key=True)
    # user_id = IntegerField()
    # post_id = IntegerField()
    userId = IntegerField(column_name='user_id')
    postId = IntegerField(column_name='post_id')

    class Meta:
        table_name = 'user_post_relp'  # 自定义映射的表名

    class Config:
        orm_mode = True

    @classmethod
    async def add(cls, relp: dict):  # 添加
        result = await async_db.create(UserPostRelp, **relp)
        return result

    @classmethod
    async def delete_by_userId(cls, id):  # 获取
        return await async_db.execute(
            UserPostRelp.delete().where(UserPostRelp.userId == id))

    @classmethod
    async def delete_by_userId_and_postId(cls, userId, postId):  # 获取
        return await async_db.execute(
            UserPostRelp.delete().where(
                UserPostRelp.userId == userId,
                UserPostRelp.postId == postId))


class UserRoleRelp(BaseModel):
    """
    用户角色关系表
    """
    id = IntegerField(primary_key=True)
    userId = IntegerField(column_name='user_id')
    roleId = IntegerField(column_name='role_id')

    class Meta:
        table_name = 'user_role_relp'  # 自定义映射的表名

    class Config:
        orm_mode = True

    # @classmethod
    # def add(cls, id: int):  # 通过id查询用户信息
    @classmethod
    async def select_by_userId(cls, userId):  # 添加
        result = await async_db.execute(
            UserRoleRelp.select().where(UserRoleRelp.userId == userId).dicts())
        return list(result)

    @classmethod
    async def add(cls, relp: dict):  # 添加
        result = await async_db.create(UserRoleRelp, **relp)
        return result

    @classmethod
    async def delete_by_userId(cls, id):  # 获取
        return await async_db.execute(
            UserRoleRelp.delete().where(UserRoleRelp.userId == id))

    @classmethod
    async def delete_by_roleId(cls, id):  # 获取
        return await async_db.execute(
            UserRoleRelp.delete().where(UserRoleRelp.roleId == id))
    @classmethod
    async def update_by_model(cls, model):  # 更新
        result = await async_db.execute(model.save())
        return result


# TODO:Userinfo=>User
class Userinfo(BaseModel):
    """
    用户信息表 
    """

    id = IntegerField(primary_key=True)  # id
    email = CharField()  # 邮箱
    birthday = CharField()  # 生日
    avatar = CharField()  # 头像
    oraCode = IntegerField(column_name='ora_code')  # 部门code
    password = CharField()  # 密码
    realName = CharField(column_name='real_name')  # 真实姓名
    userRoleId = IntegerField(column_name='user_role_id')  # 角色
    selectedRoles = CharField(column_name='selected_roles')  # 角色
    sex = CharField()  # 性别
    account = CharField()  # 用户名
    level = IntegerField()  # 层级
    jobAge = IntegerField(column_name='job_age')  # 从业年限
    phone = CharField()  # 手机号

    # postId = ForeignKeyField(Userpost, 'id', column_name='post_id')  # 从事岗位id
    # lineId = ForeignKeyField(Userline, 'id', column_name='line_id')  # 所属产品线id

    # updateBy = CharField()

    class Meta:
        table_name = 'user'  # 自定义映射的表名

    # 也可以根据类名选择表的名称
    # class Meta:
    #     database = db

    class Config:
        orm_mode = True

    @classmethod
    def select_by_role_id(cls, id: int):  # 通过id查询信息

        pass

    @classmethod
    async def select_by_id(cls, id: int):  # 通过id查询用户信息

        # result = Userinfo.select().join(Userpost,
        #                                 on=(Userinfo.postId == Userpost.id)).join(Userline,
        #                                                                           on=(Userinfo.lineId == Userline.id)).where(Userinfo.id == id).first()

        # db = Userinfo.select().where(Userinfo.id == id).first()
        db = await async_db.execute(Userinfo.select(
            Userinfo,
            fn.group_concat(Userline.id)
            .python_value(convert_num_arr)
            .alias('lineIds'),
            fn.group_concat(Userline.name)
            .python_value(convert_arr)
            .alias('line'),
            fn.group_concat(Userpost.id)
            .python_value(convert_num_arr)
            .alias('postIds'),
            fn.group_concat(Userpost.name)
            .python_value(convert_arr)
            .alias('post'),

            Department.name.alias('department'),
            Level.name.alias('levelName'),
            UserRoleRelp.roleId.alias('userRoleId'),

            Userrole.roleName.alias('userRole')
        ).join(UserLineRelp, JOIN.LEFT_OUTER,
               on=(Userinfo.id == UserLineRelp.userId)
               ).join(
            Userline,
            JOIN.LEFT_OUTER,
            on=(Userline.id ==
                UserLineRelp.lineId)
        ).join(
            UserPostRelp,
            JOIN.LEFT_OUTER,
            on=(
                    Userinfo.id ==
                    UserPostRelp.userId)
        ).join(
            Userpost,
            JOIN.LEFT_OUTER,
            on=(Userpost.id == UserPostRelp.postId)
        ).join(
            UserRoleRelp,
            JOIN.LEFT_OUTER,
            on=(Userinfo.id ==
                UserRoleRelp.userId)
        ).join(
            Userrole,
            JOIN.LEFT_OUTER,
            on=(Userrole.id ==
                UserRoleRelp.roleId)
        ).join(
            Department,
            JOIN.LEFT_OUTER,
            on=(Userinfo.oraCode ==
                Department.id)
        ).join(
            Level,
            JOIN.LEFT_OUTER,
            on=(Userinfo.level ==
                Level.id)
        ).group_by(Userinfo.id).where(Userinfo.id == id).dicts())

        # result = model_to_dict(db)
        result = list(db)
        if len(result)>0:
            result=result[0]
        # print('result')
        # print(result)
        return result

    # 通过id查询用户角色信息

    @classmethod
    async def select_user_role(cls, id: int):

        result = await async_db.execute(UserRoleRelp.select(UserRoleRelp.roleId).where(
            UserRoleRelp.userId == id).dicts())
        result = await async_db.execute(Userinfo.select(UserRoleRelp.roleId).join(UserRoleRelp, JOIN.LEFT_OUTER,
                                                                                  on=(
                                                                                          Userinfo.id == UserRoleRelp.userId)).where(
            UserRoleRelp.userId == id).dicts())
        result = list(result)
        print('result')
        print(result)
        return result

    @classmethod
    async def fuzzy_query(cls, queryuserinfo):

        # fn.abs(userinfo.full_pressure - queryUser.full_pressure).alias('count')

        # db = Userinfo.select().join(Userpost,
        #     on=(Userinfo.postId == Userpost.id)).join(Userline,
        #     on=(Userinfo.lineId ==Userline.id)).where(
        #     Userinfo.account.contains(queryuserinfo.account),
        #     Userinfo.id.contains(queryuserinfo.id),
        # ).dicts()
        # --------------------------------------------------------------------------------
        # group_concat 拼接字段
        # python_value 指定在转换数据库光标返回的值时要使用的特定函数 参数为函数名

        # user line 联表查询
        # db = Userinfo.select(Userinfo,
        #                      fn.group_concat(Userline.name).python_value(
        #                          convert_arr).alias('line'),
        #                      ).join(UserLineRelp, JOIN.LEFT_OUTER,
        #                             on=(Userinfo.id == UserLineRelp.userId)
        #                             ).join(Userline, JOIN.LEFT_OUTER,
        #                                    on=(Userline.id ==
        #                                        UserLineRelp.lineId)
        #                                    ).group_by(Userinfo.id)

        # user line post联表查询
        db = await async_db.execute(Userinfo.select(
            Userinfo,
            fn.group_concat(Userline.name).python_value(
                convert_arr).alias('line'),
            fn.group_concat(Userpost.name).python_value(
                convert_arr).alias('post'),
            UserRoleRelp.roleId.alias('userRoleId'),
            Userrole.roleName.alias('userRole'),

            Department.name.alias('oraCode')
        ).join(UserLineRelp,
               JOIN.LEFT_OUTER,
               on=(Userinfo.id == UserLineRelp.userId)
               ).join(
            Userline,
            JOIN.LEFT_OUTER,
            on=(Userline.id ==
                UserLineRelp.lineId)
        ).join(
            UserPostRelp,
            JOIN.LEFT_OUTER,
            on=(Userinfo.id ==
                UserPostRelp.userId)
        ).join(
            Userpost,
            JOIN.LEFT_OUTER,
            on=(Userpost.id == UserPostRelp.postId)
        ).join(
            UserRoleRelp,
            JOIN.LEFT_OUTER,
            on=(Userinfo.id ==
                UserRoleRelp.userId)
        ).join(
            Userrole,
            JOIN.LEFT_OUTER,
            on=(Userrole.id ==
                UserRoleRelp.roleId)
        ).join(
            Department,
            JOIN.LEFT_OUTER,
            on=(Userinfo.oraCode ==
                Department.id)
        ).group_by(Userinfo.id).order_by(Userinfo.updateAt.desc()).where(
            Userinfo.account.contains(queryuserinfo.account) if queryuserinfo.account else True,
            Userinfo.realName.contains(queryuserinfo.realName) if queryuserinfo.realName else True,
            Userinfo.phone.contains(queryuserinfo.phone) if queryuserinfo.phone else True,
            Userinfo.email.contains(queryuserinfo.email) if queryuserinfo.email else True,
            Userinfo.sex.contains(queryuserinfo.sex) if queryuserinfo.sex else True,
            Userinfo.userRoleId == queryuserinfo.userRole if queryuserinfo.userRole else True
            # Userrole.roleName.contains(queryuserinfo.userRole)if queryuserinfo.userRole else True
        ).order_by(Userinfo.updateAt.desc()).dicts())
        # and Userrole.roleName.contains(queryuserinfo.userRole)
        # db.where(  db)
        # result = list(db.offset((queryuserinfo.current - 1) *
        #                         queryuserinfo.pageSize).limit(queryuserinfo.pageSize).dicts())
        if db:
            result = list(db)
        else:
            result = []
        return result

    @classmethod
    async def fuzzy_query_by_dict(cls, queryuserinfo):

        # fn.abs(User.full_pressure - queryUser.full_pressure).alias('count')
        # 查询数据并切片转列表，返回第一条
        db = await async_db.execute(Userinfo.select().where(
            Userinfo.account.contains(queryuserinfo['account']),
            Userinfo.realname.contains(queryuserinfo['realname']),
            Userinfo.selectedroles.contains(queryuserinfo['selectedroles']),
            Userinfo.email.contains(queryuserinfo['email']),
            Userinfo.oracode.contains(queryuserinfo['oraCode']),
            Userinfo.phone.contains(queryuserinfo['phone']),

            Userinfo.level.contains(queryuserinfo['level']),
            Userinfo.sex.contains(queryuserinfo['sex']),

            # (queryUser.flow_rate == None) | (
            #     User.flow_rate == queryUser.flow_rate),

        ).order_by(
            # fn.abs(User.flow_rate-queryUser['flowRate']),
        ).dicts())
        db = db.offset((queryuserinfo['current'] - 1) *
                       queryuserinfo['pageSize']).limit(queryuserinfo['pageSize'])
        return list(db)

    @classmethod
    async def single_by_account(cls, account: str):  # 通过用户名查找用户
        db = await async_db.execute(Userinfo.select().where(Userinfo.account == account).dicts())
        db = list(db)
        print(db)
        if db == None:
            return None
        if len(db)==0:
            return None
        # return model_to_dict(db)
        # db = User.select().where(User.account == account).dicts()
        return db[0]

    @classmethod
    async def get_userinfo_by_phone(cls, phone: str):  # 通过手机号查找用户
        return await async_db.execute(Userinfo.filter(Userinfo.phone == phone).first())

    # @classmethod
    # def single_by_phone(cls, phone: str):
    #     db = Userinfo.select()
    #
    #     if phone != None:
    #         db = db.where(Userinfo.phone == phone)
    #     return db.first()
    #     if db:
    #         return model_to_dict(db)

    @classmethod
    async def fetch_all(cls, page: int = 1, page_size: int = 10):  # 获取所有信息
        db = await async_db.execute(Userinfo.select())
        userinfo_list, paginate = paginator(db, page, page_size, "id desc")

        return userinfo_list, paginate

    @classmethod
    async def add_user(cls, userinfo):  # 添加用户
        # nickname: str,email: str,password: str,authority_id,avatar: str   name=user.name,
        # nickname=nickname,email=email,password=password,authority_id=authority_id,avatar=avatar
        # print("user")
        # print(userinfo)
        result = await async_db.create(Userinfo, **userinfo)

        return result.id

    @classmethod
    async def del_by_userid(cls, userid):  # 通过用户id删除信息
        return await async_db.execute(Userinfo.delete().where(Userinfo.id ==
                                                              userid))

    @classmethod
    async def update_user(cls, user):
        result = await async_db.update(user)

        # result = await async_db.execute(user.save())

        return result

    # @classmethod
    # def get_user_permission(cls, account: str):
    #     db = User.select().where(User.phone == phone)
    #     return db.first()

    @classmethod
    async def update_password(cls, account, password, oldpassword):
        # 修改密码
        db = await async_db.execute(Userinfo.select(Userinfo.password).where(
            Userinfo.account == account).dicts())
        db1 = list(db)
        db2 = db1[0]
        db3 = db2['password']
        if db3 == oldpassword:
            #     print(db)
            u = await async_db.execute(Userinfo.update(password).where(Userinfo.account == account))
            # u.execute()
        else:
            print("密码错误")
