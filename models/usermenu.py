"""
纯增删改查操作，写在model里面
"""

from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, IntegerField, ForeignKeyField, TimeField, BooleanField
from playhouse.shortcuts import model_to_dict, dict_to_model
from sqlalchemy.orm import relationship
from schemas.request import sys_usermenu_schema
from peewee import fn
import time


class Usermenu(BaseModel):
    """
    用户菜单表 
    """
    id = IntegerField(primary_key=True)
    parentId = IntegerField(column_name='parent_id')  # 父级id
    # roleId = CharField(column_name='role_id')  # 角色id
    name = CharField()  # 菜单名称
    menuType = IntegerField(column_name='menu_type')  # 类型（1：一级菜单，2：子菜单）
    icon = CharField()  # 图标
    description = CharField()  # 描述
    componentName = CharField(column_name='component_name')  # 前端组件名称
    component = CharField()  # 前端组件路径
    permsType = CharField(column_name='perms_type')  # 权限策略
    route = BooleanField()  # 是否是路由菜单
    sortNo = IntegerField(column_name='sort_no')  # 菜单排序
    url = CharField()  # 菜单路径
    status = CharField()
    keepAlive = BooleanField(column_name='keep_alive')  # 是否缓存路由
    leaf = BooleanField()  # 是否是叶子节点
    redirect = CharField()  # 菜单跳转地址
    createBy = CharField(column_name='create_by')
    updateBy = CharField(column_name='update_by')

    class Meta:
        table_name = 'menu'  # 自定义映射的表名

    # 也可以根据类名选择表的名称
    # class Meta:
    #     database = db

    class Config:
        orm_mode = True

    @classmethod
    async def select_all(cls):
        return await async_db.execute(Usermenu.select().dicts())
    @classmethod
    async def fuzzy_query(cls, queryusermenu):
        # fn.abs(userinfo.full_pressure - queryUser.full_pressure).alias('count')

        # db = Usermenu.select().where(
        #     Usermenu.name.contains(queryusermenu.name),
        # ).dicts()
        db =await async_db.execute( Usermenu.select().where(
            Usermenu.name.contains(queryusermenu.name),
            Usermenu.component.contains(queryusermenu.component),
            Usermenu.url.contains(queryusermenu.url),
            Usermenu.menuType == queryusermenu.menuType if queryusermenu.menuType != None else True,
            Usermenu.sortNo == queryusermenu.sortNo if queryusermenu.sortNo != None else True,
        ).order_by(Usermenu.sortNo).dicts())
        # print('db')
        # print(db)

        return list(db)

    @classmethod
    async def add_usermenu(cls, menu):  # 添加角色
        result =await async_db.create( Usermenu,**menu )
        return result.id
    @classmethod
    # menu:Model Usermenu
    async def update_menu(cls, menu):
        result =await async_db.update( menu )
        return result

    # @router.put("/sys/permission/edit", summary="编辑菜单", name="编辑菜单")
    # async def edit_menu(
    #         menu: sys_usermenu_schema.MenuUpdate
    # ) -> Any:
    #     menu.updateAt = datetime.strftime(
    #         datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
    #     print(menu)
    #     if menu.menuType == 1:
    #         menu.parentId = 0
    #     menu = dict_to_model(Usermenu, dict(menu))
    #
    #     try:
    #         result = await Usermenu.update_menu(menu)
    #         # result = menu.save()
    #     except Exception as e:
    #         print(e)
    #         return resp.fail(resp.DataUpdateFail, detail=str(e))
    #     return resp.ok(data=result)

    @classmethod
    async def del_by_usermenu_id(cls, id):
        return await async_db.execute(Usermenu.delete().where(Usermenu.id ==
                                id))

    @classmethod
    async def del_by_usermenu_ids(cls, usermenu_ids: list):

        return await async_db.execute(Usermenu.delete().where(Usermenu.id.in_(usermenu_ids)))



    @classmethod
    async def select_by_roleId(cls, roleId: str):  # 通过roleid查询用户信息
        print('roleId')
        print(roleId)
        result =await async_db.execute( Usermenu.select().where(Usermenu.roleId == roleId).dicts())
        result = list(result)
        print('result')
        print(result)
        return result

    @classmethod
    async def select_by_ids(cls, ids: list):  # 通过menuid查询菜单信息
        # print('ids')
        # print(ids)
        result = await async_db.execute(Usermenu.select(
            Usermenu.id,
            Usermenu.url,#.alias('path'),
            Usermenu.component,
            Usermenu.icon,
            Usermenu.keepAlive,
            Usermenu.name,#.alias('title'),
            Usermenu.parentId,
            Usermenu.sortNo,
            Usermenu.menuType
        ).where(Usermenu.id.in_(ids)).dicts())
        result = list(result)
        return result
