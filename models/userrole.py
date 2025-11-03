

"""
纯增删改查操作，写在model里面
"""

from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, IntegerField, ForeignKeyField, TimeField
from playhouse.shortcuts import model_to_dict, dict_to_model
from sqlalchemy.orm import relationship

from models.usermenu import Usermenu
from schemas.request import sys_user_schema

from peewee import fn, JOIN
import time

from utils.tools_func import convert_arr, convert_num_arr


class RoleMenuRelp(BaseModel):
    """
    角色菜单关系表/权限表
    """
    id = IntegerField(primary_key=True)
    roleId = IntegerField(column_name='role_id')
    menuId = IntegerField(column_name='menu_id')

    class Meta:
        table_name = 'role_menu_relp'

    class Config:
        orm_mode = True

    @classmethod
    async def select_by_role_id(cls, id: int):  # 通过id查询用户信息
        db =  await async_db.execute(RoleMenuRelp.select(
            RoleMenuRelp.roleId,
            fn.group_concat(RoleMenuRelp.menuId).python_value(convert_num_arr).alias('menuIds')).where(RoleMenuRelp.roleId == id).group_by(RoleMenuRelp.roleId).dicts())
        # result = list(db)[0]
        if db:

            result = list(db)[0]
            return result
        else:
            return {'roleId': id, 'menuIds': []}
        # print(result)
        # return result
    @classmethod
    async def add(cls, relp:dict):
        result = await async_db.create(RoleMenuRelp,**relp)
        return result.id
    @classmethod
    async def delete_by_roleId(cls, id):
        return await async_db.execute(RoleMenuRelp.delete().where(RoleMenuRelp.roleId == id))

    @classmethod
    async def delete_by_roleId_and_menuId(cls, roleId,menuId):
        return await async_db.execute(RoleMenuRelp.delete().where(RoleMenuRelp.roleId == roleId,RoleMenuRelp.menuId==menuId))
class Permission(BaseModel):
    """
    权限表 
    """
    id = IntegerField(primary_key=True)  # id
    url = CharField()  # 权限名称
    # name = CharField( )  # 权限名称
    description = CharField()  # 权限名称

    class Meta:
        table_name = 'permission'  # 自定义映射的表名

    class Config:
        orm_mode = True

    @classmethod
    async def get_all_perm(cls):
        result =await async_db.execute( Permission.select().dicts())

        return list(result)


class RolePermRelp(BaseModel):

    id = IntegerField(primary_key=True)  # id
    roleId = IntegerField(column_name='role_id')  # id
    permId = IntegerField(column_name='perm_id')  # id

    class Meta:
        table_name = 'role_perm_relp'  # 自定义映射的表名

    class Config:
        orm_mode = True

    # @classmethod
    # async def add_role_perm(cls, roleId, permId):
    #     result = await async_db.create(RolePermRelp,{'roleId' : roleId, 'permId' : permId})
    #     return result

    @classmethod
    async def add(cls, relp: dict):
        result = await async_db.create(RoleMenuRelp, **relp)
        return result.id
    @classmethod
    async def delete_by_roleId(cls, id):
        return await async_db.execute(RolePermRelp.delete().where(RolePermRelp.roleId == id))

class Userrole(BaseModel):
    """
    角色表 
    """

    id = IntegerField(primary_key=True)  # id
    roleCode = CharField(column_name='role_code')  # 角色编码
    roleName = CharField(column_name='role_name')  # 角色名称
    updateBy = CharField(column_name='update_by')  # 更新人
    createBy = CharField(column_name='create_by')
    description = CharField()

    class Meta:
        table_name = 'role'  # 自定义映射的表名
        legacy_table_names = False

    # 也可以根据类名选择表的名称
    # class Meta:
    #     database = db

    class Config:
        orm_mode = True

    @classmethod
    async def query_role_perm(cls,userRoleId):
        db =await async_db.execute( Userrole.select(
            Userrole.id,
            fn.group_concat(Usermenu.url)
            .python_value(convert_arr)
            .alias('perm')
        ).join(
            RoleMenuRelp, JOIN.LEFT_OUTER,
            on=(Userrole.id == RoleMenuRelp.roleId)
        ).join(
            Usermenu,
            JOIN.LEFT_OUTER,
            on=(Usermenu.id ==
                RoleMenuRelp.menuId)
        ).where(Usermenu.menuType == 0,Userrole.id==userRoleId).group_by(Userrole.id).dicts())
        if db:
            result = list(db)
            rolePremissionList = {}
            for item in result:
                rolePremissionList[item['id']] = item['perm']
            return rolePremissionList[userRoleId]
        else:
            return []
        # db = Userrole.select(
        #     Userrole.id,
        #     fn.group_concat(Permission.url)
        #     .python_value(convert_arr)
        #     .alias('perm')
        #
        # ).join(
        #     RolePermRelp, JOIN.LEFT_OUTER,
        #     on=(Userrole.id == RolePermRelp.roleId)
        #
        # ).join(
        #     Permission,
        #     JOIN.LEFT_OUTER,
        #     on=(Permission.id ==
        #         RolePermRelp.permId)
        # ).group_by(Userrole.id).dicts()
        # return list(db)

    @classmethod
    async def query_role_perm_by_role_id(cls, roleId):
        db =await async_db.execute( Userrole.select(
            Userrole.id,
            fn.group_concat(Permission.url)
            .python_value(convert_arr)
            .alias('perm')
            ).join(
                RolePermRelp, JOIN.LEFT_OUTER,
                on=(Userrole.id == RolePermRelp.roleId)
            ).join(
                Permission,
                JOIN.LEFT_OUTER,
                on=(Permission.id ==
                    RolePermRelp.permId)
            ).where(Userrole.id == roleId).group_by(Userrole.id).dicts())

        return list( db )

    @classmethod
    async def fuzzy_query(cls, queryuserrole):

        # fn.abs(userinfo.full_pressure - queryUser.full_pressure).alias('count')

        db = await async_db.execute(Userrole.select().where(
            Userrole.roleCode.contains(queryuserrole.roleCode),
            Userrole.roleName.contains(queryuserrole.roleName)
        ).order_by(Userrole.updateAt.desc(),Userrole.createAt.desc()).dicts())

        # .order_by(
        #     # fn.abs(User.flow_rate-queryUser.flowRate),
        # )
        # db = db.offset((queryuserrole.current - 1) *
        #                queryuserrole.pageSize).limit(queryuserrole.pageSize)
        print("查找结果", db)
        return list(db)

    @classmethod
    async def select_all(cls):  # 通过id删除信息
        db =await async_db.execute( Userrole.select(Userrole.id, Userrole.roleName,
                             Userrole.roleCode).dicts())
        return list(db)

    @classmethod
    async def add_role(cls, userrole):  # 添加角色
        result = await async_db.create(Userrole,**userrole)
        return result.id

    @classmethod
    async def del_by_userroleid(cls, userroleid):  # 通过id删除信息
        await async_db.execute(Userrole.delete().where(Userrole.id ==
                                userroleid) )

    @classmethod
    async def update_userrole(cls, id, userrole):
        # 字典结构更新userrole数据
        # print(userrole)
        return await async_db.execute( Userrole.update(userrole).where(Userrole.id == id))

    @classmethod
    async def update_by_model(cls,  userrole):
        # 字典结构更新userrole数据
        # print(userrole)
        return await async_db.update(userrole)
    @classmethod
    async def select_by_id(cls, id: str):  # 通过id查询用户信息
        result =await async_db.execute( Userrole.select().where(Userrole.id == id))
        print('result')
        print(result)
        result=result[0]
        return result

    @classmethod
    async def single_by_roleName(cls, roleName: str):  # 通过用户名查找用户
        db =await async_db.execute( Userrole.select().where(Userrole.roleName == roleName))
        if db == None:
            return None
        return db[0]
        # db = User.select().where(User.account == account).dicts()
        # return db[0]
