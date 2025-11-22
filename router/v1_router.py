'''
Author: 嘉欣 罗 2592734121@qq.com
Date: 2022-12-22 12:49:07
LastEditors: Please set LastEditors
LastEditTime: 2023-05-09 14:56:59
FilePath: \psad-backend\router\v1_router.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import os

"""

版本路由区分

# 可以在这里添加所需要的依赖
https://fastapi.tiangolo.com/tutorial/bigger-applications/#import-fastapi

"""

# from common.deps import check_authority

# from api.v1.sys_scheduler import router as scheduler_router


# from api.v1.user_des import router as userinfo_router
from common.deps import check_jwt_token, verify_current_user_perm
from api.v1.fan_introduction import router as fan_introduction_router
from api.v1.user_action import router as user_action_router
from api.v1.usermenu import router as usermenu_router
from api.v1.userrole import router as userrole_router
from api.v1.user import router as user_router
from api.v1.fan_category import router as fan_category_router
from api.v1.fan_application_model import router as application_model_router
from api.v1.perf import router as performance_router
from fastapi import APIRouter, Depends
from api.v1.items import router as items_router
from api.v1.fan import router as fan_router
from api.v1.file import router as file_router
from api.v1.permission import router as permission_router
from api.v1.sys_manage import router as sys_manage_router
from api.v1.department import router as department_router
from api.v1.audit import router as audit_router
from api.v1.intro_control import router as intro_control_router
# from api.v1.jaka import router as jaka_control_router
from api.v1.line_deep import router as line_deep_router
from api.v1.material import router as material_router
from api.v1.equipment import router as equipment_router
from api.v1.process_design import router as process_router
from api.v1.case import router as case_router



api_v1_router = APIRouter()

# api_v1_router.include_router(items_router, tags=["测试API"], dependencies=[Depends(check_jwt_token)])
# check_authority 权限验证内部包含了 token 验证 如果不校验权限可直接 dependencies=[Depends(check_jwt_token)]
if os.getenv('DEBUG') == 'True':
    api_v1_router.include_router(items_router, prefix="/api", tags=["测试接口"])
api_v1_router.include_router(sys_manage_router, prefix="/api/sys", tags=["系统管理接口"])
# api_v1_router.include_router(userinfo_router, prefix="/api/user", tags=["用户"])
api_v1_router.include_router(fan_router, prefix="/api/fan", tags=["风机"])
api_v1_router.include_router(
    application_model_router, prefix="/api/fan/appl", tags=["应用车型大类"])
api_v1_router.include_router(
    fan_category_router, prefix="/api/fan/category", tags=["风机类型"])

api_v1_router.include_router(file_router, prefix="/api", tags=["文件"])
api_v1_router.include_router(
    performance_router, prefix="/api/perf", tags=["性能曲线"])
api_v1_router.include_router(
    permission_router, prefix="/api/perm", tags=["权限管理"])

# api_v1_router.include_router(userinfo_router, prefix="/api/userinfo", tags=["用户信息"])
# api_v1_router.include_router(userrole_router, prefix="/api/userrole", tags=["用户角色"])
# api_v1_router.include_router(usermenu_router, prefix="/api/usermenu", tags=["用户菜单"])
api_v1_router.include_router(
    user_router, prefix="/api/user", tags=["用户信息"])
#
api_v1_router.include_router(
    userrole_router, prefix="/phm-web-service-gz", tags=["用户角色"])
api_v1_router.include_router(
    usermenu_router, prefix="/phm-web-service-gz", tags=["用户菜单"])
api_v1_router.include_router(
    fan_introduction_router, prefix="/api", tags=["风机产品信息"])
api_v1_router.include_router(
    user_action_router, prefix="/api", tags=["用户行为信息"])
api_v1_router.include_router(
    department_router, prefix="/api", tags=["部门管理"])
api_v1_router.include_router(
    audit_router, prefix="/api", tags=["审核记录"])
api_v1_router.include_router(
    intro_control_router, prefix="/api", tags=["产品介绍控制"])
# api_v1_router.include_router(
#     jaka_control_router, prefix="/api", tags=["jaka界面"])
api_v1_router.include_router(
    line_deep_router, prefix="/api", tags=["熔深测量"])
# # api_v1_router.include_router(scheduler_router, tags=["任务调度"])

# api_v1_router.include_router(scheduler_router, tags=["任务调度"])
api_v1_router.include_router(
    material_router, prefix="/api", tags=["焊接母材信息"])
api_v1_router.include_router(
    equipment_router, prefix="/api", tags=["焊接装置信息"])
api_v1_router.include_router(
    process_router, prefix="/api", tags=["焊接工艺设计"])
api_v1_router.include_router(
    case_router, prefix="/api", tags=["焊接工艺案例和质量检测数据表"])
