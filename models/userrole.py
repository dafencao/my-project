

"""
纯增删改查操作，写在model里面
"""

from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, IntegerField, TimeField,DateTimeField
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
    role_id = IntegerField(column_name='role_id')
    menu_id = IntegerField(column_name='menu_id')
    class Meta:
        table_name = 'sys_role_menu'

    class Config:   
        orm_mode = True

    @classmethod
    async def select_by_role_id(cls, id: int):  # 通过id查询用户信息
        db =  await async_db.execute(RoleMenuRelp.select(
            RoleMenuRelp.roleId,
            fn.group_concat(RoleMenuRelp.menu_id).python_value(convert_num_arr).alias('menuIds')).where(RoleMenuRelp.role_id == id).group_by(RoleMenuRelp.roleId).dicts())
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
        return await async_db.execute(RoleMenuRelp.delete().where(RoleMenuRelp.role_id == id))

    @classmethod
    async def delete_by_roleId_and_menuId(cls, roleId,menuId):
        return await async_db.execute(RoleMenuRelp.delete().where(RoleMenuRelp.roleId == roleId,RoleMenuRelp.menuId==menuId))
class Permission(BaseModel):
    """
    权限表 
    """
    perm_id = IntegerField(primary_key=True)  # id
    perm_key = CharField(max_length=100, null=False, unique=True, verbose_name="权限字符串(如 sys:user:add)")
    data_scope = CharField(max_length=1, null=False, verbose_name="数据范围(1-全部,2-本部门,3-本人)")

    class Meta:
        table_name = 'sys_permission'  # 自定义映射的表名

    class Config:
        orm_mode = True

    @classmethod
    async def get_all_perm(cls):
        result =await async_db.execute( Permission.select().dicts())

        return list(result)


class RolePermRelp(BaseModel):

    id = IntegerField(primary_key=True)  # id
    role_id = IntegerField(null=False, verbose_name="角色ID关联 (sys_role.role_id)")
    perm_id = IntegerField(null=False, verbose_name="权限ID关联 (sys_permission.perm_id)")

    class Meta:
        table_name = 'sys_role_permission'  # 自定义映射的表名

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
        return await async_db.execute(RolePermRelp.delete().where(RolePermRelp.role_id == id))

class Userrole(BaseModel):
    """
    角色表 
    """
    # 角色ID：自增主键，对应 bigint 类型
    role_id = IntegerField(primary_key=True, verbose_name="角色ID")
    # 角色名称：varchar(30)，非空
    role_name = CharField(max_length=30, null=False, verbose_name="角色名称")
    # 角色状态：char(1)，'0' 正常、'1' 禁用，非空
    status = CharField(max_length=1, null=False, default='0', verbose_name="角色状态")
    # 删除标志：char(1)，'0' 未删除、'1' 已删除，非空
    del_flag = CharField(max_length=1, null=False, default='0', verbose_name="删除标志")
    update_at = DateTimeField
    create_at = DateTimeField


    # id = IntegerField(primary_key=True)  # id
    # roleCode = CharField(column_name='role_code')  # 角色编码
    # roleName = CharField(column_name='role_name')  # 角色名称
    # updateBy = CharField(column_name='update_by')  # 更新人
    # createBy = CharField(column_name='create_by')
    # description = CharField()

    class Meta:
        table_name = 'sys_role'  # 自定义映射的表名
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
            Userrole.role_id,
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

        conditions = []
    
        # 角色名称模糊查询
        if hasattr(queryuserrole, 'role_name') and queryuserrole.role_name:
            conditions.append(Userrole.role_name.contains(queryuserrole.role_name))
        
        # 执行查询
        query = Userrole.select().where(*conditions).order_by(
            Userrole.update_at.desc,
            Userrole.create_at.desc
        )
    
        # 添加分页（如果请求中有分页参数）
        if hasattr(queryuserrole, 'current') and hasattr(queryuserrole, 'pageSize'):
            query = query.offset((queryuserrole.current - 1) * queryuserrole.pageSize).limit(queryuserrole.pageSize)
        
        db = await async_db.execute(query.dicts())
        print("查找结果", db)
        return list(db)

    @classmethod
    async def select_all(cls):  # 查看所有的角色
        db =await async_db.execute( Userrole.select(Userrole.role_id, Userrole.role_name,
                             Userrole.status).dicts())
        return list(db)

    @classmethod
    async def add_role(cls, userrole):  # 添加角色
        result = await async_db.create(Userrole,**userrole)
        return result.role_id

    @classmethod
    async def del_by_userroleid(cls, userroleid):  # 通过id删除信息
        await async_db.execute(Userrole.delete().where(Userrole.role_id ==
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
    async def select_by_id(cls, id: int):  # 通过id查询用户信息
        try:
        # 方法1：使用dicts()获取字典结果
            query = Userrole.select().where(Userrole.role_id == id)
            result = await async_db.execute(query.dicts())
            
            if result and len(result) > 0:
                return result[0]  # 返回第一条记录
            else:
                return None
            
        except Exception as e:
            print(f"查询角色失败: {e}")
            return None

    @classmethod
    async def single_by_roleName(cls, roleName: str):  # 通过用户名查找用户
        db =await async_db.execute( Userrole.select().where(Userrole.roleName == roleName))
        if db == None:
            return None
        return db[0]
        # db = User.select().where(User.account == account).dicts()
        # return db[0]
