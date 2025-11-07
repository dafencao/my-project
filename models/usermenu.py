"""
纯增删改查操作，写在model里面
"""

from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, IntegerField,DateTimeField,BigAutoField,BigIntegerField
from playhouse.shortcuts import model_to_dict, dict_to_model
from sqlalchemy.orm import relationship
from schemas.request import sys_usermenu_schema
from peewee import fn
import time



class Usermenu(BaseModel):
    """
    用户菜单表 
    """
    menu_id = BigAutoField(primary_key=True, verbose_name="菜单ID(自增主键)")
    menu_name = CharField(max_length=50, verbose_name="菜单名称")
    parent_id = BigIntegerField( verbose_name="父菜单ID(为空表示一级菜单)")
    order_num = IntegerField( verbose_name="显示顺序")
    path = CharField(max_length=200, verbose_name="路由地址")
    component = CharField(max_length=255, verbose_name="组件路径")
    query = CharField(max_length=255, verbose_name="路由参数")
    is_cache = IntegerField(default=0, verbose_name="是否缓存(0-不缓存,1-缓存)")
    menu_type = CharField(max_length=1, verbose_name="菜单类型(M-目录,C-菜单,F-按钮)")
    visible = CharField(max_length=1, default="0", verbose_name="菜单状态(0-显示,1-隐藏)")
    status = CharField(max_length=1, default="0", verbose_name="状态(0-正常,1-禁用)")
    perms = CharField(max_length=100, verbose_name="权限标识(如 sys:menu:add)")
    icon = CharField(max_length=100, verbose_name="菜单图标")
    create_at = DateTimeField(verbose_name="创建时间")
    update_at = DateTimeField(verbose_name="更新时间")

    class Meta:
        table_name = 'sys_menu'  # 自定义映射的表名

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
        return await async_db.execute(Usermenu.delete().where(Usermenu.menu_id ==
                                id))

    @classmethod
    async def del_by_usermenu_ids(cls, usermenu_ids: list):

        return await async_db.execute(Usermenu.delete().where(Usermenu.menu_id.in_(usermenu_ids)))



    # @classmethod
    # async def select_by_roleId(cls, role_id: str):  # 通过roleid查询用户信息

    #     result =await async_db.execute( Usermenu.select().where(Usermenu.menu_id == role_id).dicts())
    #     result = list(result)
    #     print(result)
    #     return result

    
    @classmethod
    async def select_by_roleId(cls, role_id: str):
        from models.userrole import RoleMenuRelp
        """通过role_id查询角色对应的菜单信息 """
        try:
            # 在方法内部导入，避免循环导入
            from models.userrole import RoleMenuRelp
            
            # 显式指定要查询的字段，避免自动添加不存在的字段
            role_menu_query = RoleMenuRelp.select(
                RoleMenuRelp.id,
                RoleMenuRelp.role_id,
                RoleMenuRelp.menu_id
            ).where(RoleMenuRelp.role_id == role_id)
            
            role_menus = await async_db.execute(role_menu_query.dicts())
            
            if not role_menus:
                print(f"角色 {role_id} 没有分配任何菜单权限")
                return []
            
            # 提取menu_id列表
            menu_ids = [rm['menu_id'] for rm in role_menus]
            
            # 查询对应的菜单信息
            menu_query = Usermenu.select().where(Usermenu.menu_id.in_(menu_ids))
            result = await async_db.execute(menu_query.dicts())
            result = list(result)
            
            print(f"角色 {role_id} 的菜单权限: {result}")
            return result
        
        except Exception as e:
            print(f"查询角色菜单失败: {e}")
            return []


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
