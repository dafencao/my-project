from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, IntegerField, DecimalField, DoesNotExist
from peewee import JOIN
from models.material import MaterialInfo
from models.equipment import EquipmentParam
from models.process_design import ProcessDesign
from schemas.request.case_schema import CaseQualityFilter


class CaseQuality(BaseModel):
    case_id = CharField(max_length=20, primary_key=True)
    related_process_id = CharField(max_length=20)
    product_name = CharField(max_length=100)
    product_size = CharField(max_length=50)
    weld_depth = DecimalField(max_digits=5, decimal_places=2, default=0.00)
    weld_width = DecimalField(max_digits=5, decimal_places=2, default=0.00)
    tensile_strength = IntegerField(default=0)
    deformation_amount = DecimalField(max_digits=5, decimal_places=2)
    defect_type = CharField(max_length=100)
    defect_position = CharField(max_length=50, default='无')
    defect_cause = CharField(max_length=200, default='无')
    detection_method = CharField(max_length=50, default='')
    detection_result = CharField(max_length=10)  
    inspection_standard = CharField(max_length=50, default='')
    case_picture = CharField(max_length=255, default='')
    class Meta:
        table_name = 'case_quality'

    class Config:   
        orm_mode = True


    @classmethod
    async def add_caseQuality(cls, caseQuality):  # 添加加工工艺
        result = await async_db.create(CaseQuality,**caseQuality)
        return result.case_id


    @classmethod
    async def del_by_caseQuality_id(cls, caseQuality_id):
        await async_db.execute(CaseQuality.delete().where(CaseQuality.case_id == caseQuality_id))


    @classmethod
    async def update_case_quality(cls, case_quality):
        # 检查是否提供了case_id
        if 'case_id' not in case_quality or not case_quality['case_id']:
            raise ValueError('案例ID不能为空')
        
        # 检查案例是否存在
        existing_case = await cls.get_case_by_id(case_quality['case_id'])
        if not existing_case:
            raise ValueError(f"案例ID '{case_quality['case_id']}' 不存在")
        
        # 创建更新字典（排除case_id本身，避免更新主键）
        update_data = {k: v for k, v in case_quality.items() if k != 'case_id'}
        
        # 如果没有实际要更新的字段，直接返回
        if not update_data:
            return 0
        
        # 执行更新
        query = CaseQuality.update(**update_data).where(
            CaseQuality.case_id == case_quality['case_id']
        )
        affected_rows = await async_db.execute(query)
        
        return affected_rows
    

    @classmethod
    async def get_case_by_id(cls, case_id: str):
        """
        根据案例ID获取案例质量信息
        
        Args:
            case_id: 案例唯一标识
            
        Returns:
            CaseQuality 对象或 None
        """
        try:
            # 明确指定要查询的字段
            query = cls.select(
                cls.case_id,
                cls.related_process_id,
                cls.product_name,
                cls.product_size,
                cls.weld_depth,
                cls.weld_width,
                cls.tensile_strength,
                cls.deformation_amount,
                cls.defect_type,
                cls.defect_position,
                cls.defect_cause,
                cls.detection_method,
                cls.detection_result,
                cls.inspection_standard,
                cls.case_picture
            ).where(cls.case_id == case_id)
            
            case = await async_db.get(query)
            return case
            
        except DoesNotExist:
            return None
        except Exception as e:
            print(f"根据ID查询案例失败: {e}")
            raise e
        
        
    @classmethod
    async def select_all(cls, page: int = 1, page_size: int = 20):
        """查询所有案例质量 - 包含关联的工艺、材料和设备信息（分页）"""
        try:
            # 基础查询
            query = (CaseQuality
                    .select(
                        # 案例质量核心字段
                        CaseQuality.case_id,
                        CaseQuality.product_name,
                        CaseQuality.product_size,
                        CaseQuality.deformation_amount,
                        CaseQuality.defect_type,
                        CaseQuality.detection_result,
                        CaseQuality.inspection_standard,
                        CaseQuality.case_picture,
                        
                        # 关联工艺信息
                        ProcessDesign.laser_power,
                        ProcessDesign.welding_speed,
                        ProcessDesign.defocus_amount,
                        
                        # 关联材料信息
                        MaterialInfo.base_material,
                        MaterialInfo.material_grade,
                        
                        # 关联设备信息
                        EquipmentParam.laser_equipment_model,
                        EquipmentParam.laser_power_range,
                    )
                    .join(
                        ProcessDesign,
                        JOIN.LEFT_OUTER,
                        on=(CaseQuality.related_process_id == ProcessDesign.process_id)
                    )
                    .join(
                        MaterialInfo,
                        JOIN.LEFT_OUTER,
                        on=(ProcessDesign.related_material_id == MaterialInfo.material_id)
                    )
                    .join(
                        EquipmentParam,
                        JOIN.LEFT_OUTER,
                        on=(ProcessDesign.related_equipment_id == EquipmentParam.equipment_id)
                    )
                    .order_by(CaseQuality.case_id.asc()))
            
            # 计算总数
            total_count = await async_db.count(query)
            
            # 应用分页
            query = query.paginate(page, page_size)
            
            # 执行查询
            db_result = await async_db.execute(query.dicts())
            cases = list(db_result)
            
            # 返回分页结果
            return {
                "items": cases,
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size
            }
            
        except Exception as e:
            print(f"查询所有案例质量失败: {e}")
            raise e
        
    
    @classmethod
    async def select_with_filter(
        cls, 
        filter_params: CaseQualityFilter,
        page: int = 1,
        page_size: int = 20
    ):
        """根据筛选条件查询案例质量 - 支持分页"""
        try:
            # 基础查询
            query = (CaseQuality
                    .select(
                        # 案例质量表字段
                        CaseQuality.case_id,
                        CaseQuality.related_process_id,
                        CaseQuality.product_name,
                        CaseQuality.product_size,
                        CaseQuality.weld_depth,
                        CaseQuality.weld_width,
                        CaseQuality.tensile_strength,
                        CaseQuality.deformation_amount,
                        CaseQuality.defect_type,
                        CaseQuality.defect_position,
                        CaseQuality.defect_cause,
                        CaseQuality.detection_method,
                        CaseQuality.detection_result,
                        CaseQuality.inspection_standard,
                        
                        # 关联工艺设计表字段
                        ProcessDesign.laser_power,
                        ProcessDesign.welding_speed,
                        ProcessDesign.defocus_amount,
                        ProcessDesign.incident_angle,
                        
                        # 关联材料信息表字段
                        MaterialInfo.base_material,
                        MaterialInfo.material_grade,
                        MaterialInfo.material_thickness,
                        
                        # 关联设备参数表字段
                        EquipmentParam.laser_equipment_model,
                        EquipmentParam.laser_power_range,
                        EquipmentParam.output_mode,
                    )
                    .join(ProcessDesign, JOIN.LEFT_OUTER,
                        on=(CaseQuality.related_process_id == ProcessDesign.process_id))
                    .join(MaterialInfo, JOIN.LEFT_OUTER,
                        on=(ProcessDesign.related_material_id == MaterialInfo.material_id))
                    .join(EquipmentParam, JOIN.LEFT_OUTER,
                        on=(ProcessDesign.related_equipment_id == EquipmentParam.equipment_id)))
            
            # 应用筛选条件
            # 基础信息筛选
            if filter_params.case_id:
                query = query.where(CaseQuality.case_id.contains(filter_params.case_id))
            
            if filter_params.related_process_id:
                query = query.where(CaseQuality.related_process_id == filter_params.related_process_id)
            
            if filter_params.product_name:
                query = query.where(CaseQuality.product_name.contains(filter_params.product_name))
            
            if filter_params.product_size:
                query = query.where(CaseQuality.product_size.contains(filter_params.product_size))
            
            # 焊缝质量参数范围筛选
            if filter_params.weld_depth_min is not None:
                query = query.where(CaseQuality.weld_depth >= filter_params.weld_depth_min)
            if filter_params.weld_depth_max is not None:
                query = query.where(CaseQuality.weld_depth <= filter_params.weld_depth_max)
            
            if filter_params.weld_width_min is not None:
                query = query.where(CaseQuality.weld_width >= filter_params.weld_width_min)
            if filter_params.weld_width_max is not None:
                query = query.where(CaseQuality.weld_width <= filter_params.weld_width_max)
            
            if filter_params.tensile_strength_min is not None:
                query = query.where(CaseQuality.tensile_strength >= filter_params.tensile_strength_min)
            if filter_params.tensile_strength_max is not None:
                query = query.where(CaseQuality.tensile_strength <= filter_params.tensile_strength_max)
            
            if filter_params.deformation_amount_min is not None:
                query = query.where(CaseQuality.deformation_amount >= filter_params.deformation_amount_min)
            if filter_params.deformation_amount_max is not None:
                query = query.where(CaseQuality.deformation_amount <= filter_params.deformation_amount_max)
            
            # 缺陷相关筛选
            if filter_params.defect_type:
                query = query.where(CaseQuality.defect_type.contains(filter_params.defect_type))
            
            if filter_params.defect_position:
                query = query.where(CaseQuality.defect_position.contains(filter_params.defect_position))
            
            if filter_params.defect_cause:
                query = query.where(CaseQuality.defect_cause.contains(filter_params.defect_cause))
            
            # 检测相关筛选
            if filter_params.detection_method:
                query = query.where(CaseQuality.detection_method.contains(filter_params.detection_method))
            
            if filter_params.detection_result:
                query = query.where(CaseQuality.detection_result.contains(filter_params.detection_result))
            
            if filter_params.inspection_standard:
                query = query.where(CaseQuality.inspection_standard.contains(filter_params.inspection_standard))
            
            # 关联工艺参数筛选
            if filter_params.laser_power_min is not None:
                query = query.where(ProcessDesign.laser_power >= filter_params.laser_power_min)
            if filter_params.laser_power_max is not None:
                query = query.where(ProcessDesign.laser_power <= filter_params.laser_power_max)
            
            if filter_params.welding_speed_min is not None:
                query = query.where(ProcessDesign.welding_speed >= filter_params.welding_speed_min)
            if filter_params.welding_speed_max is not None:
                query = query.where(ProcessDesign.welding_speed <= filter_params.welding_speed_max)
            
            if filter_params.defocus_amount_min is not None:
                query = query.where(ProcessDesign.defocus_amount >= filter_params.defocus_amount_min)
            if filter_params.defocus_amount_max is not None:
                query = query.where(ProcessDesign.defocus_amount <= filter_params.defocus_amount_max)
            
            # 关联材料筛选
            if filter_params.base_material:
                query = query.where(MaterialInfo.base_material.contains(filter_params.base_material))
            
            if filter_params.material_grade:
                query = query.where(MaterialInfo.material_grade.contains(filter_params.material_grade))
            
            # 关联设备筛选
            if filter_params.laser_equipment_model:
                query = query.where(EquipmentParam.laser_equipment_model.contains(filter_params.laser_equipment_model))
            
            if filter_params.laser_power_range:
                query = query.where(EquipmentParam.laser_power_range.contains(filter_params.laser_power_range))
            
            # 计算总数
            total_query = query
            total_count = await async_db.count(total_query)
            
            # 分页处理
            query = query.order_by(CaseQuality.case_id.asc())
            
            # 手动分页实现
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            
            # 执行查询
            db_result = await async_db.execute(query.dicts())
            cases = list(db_result)
        
            # 返回分页结果
            return {
                "items": cases,
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size
            }
            
        except Exception as e:
            print(f"筛选查询案例质量失败: {e}")
            raise e