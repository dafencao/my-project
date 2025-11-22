from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, IntegerField, DecimalField, DoesNotExist
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import JOIN
from models.material import MaterialInfo
from models.equipment import EquipmentParam
from schemas.request.processDesign_schema import ProcessDesignFilter


class ProcessDesign(BaseModel):
    process_id = CharField(max_length=20, primary_key=True)
    related_material_id = CharField(max_length=20)
    related_equipment_id = CharField(max_length=20)
    laser_power = IntegerField()
    welding_speed = IntegerField()
    defocus_amount = DecimalField(max_digits=5, decimal_places=1)
    incident_angle = DecimalField(max_digits=5, decimal_places=1)
    welding_sequence = CharField(max_length=50, default='')
    
    # 使用CharField的choices参数模拟ENUM类型
    GROOVE_TYPES = [
        ('无坡口', '无坡口'),
        ('V型坡口', 'V型坡口'),
        ('U型坡口', 'U型坡口'),
        ('X型坡口', 'X型坡口')
    ]
    groove_type = CharField(choices=GROOVE_TYPES)
    
    groove_angle = IntegerField(default=0)
    joint_type = CharField(max_length=50)
    joint_thickness = DecimalField(max_digits=5, decimal_places=2)
    scanning_mode = CharField(max_length=30, default='无')
    scanning_frequency = IntegerField(default=0)
    scanning_amplitude = DecimalField(max_digits=5, decimal_places=2, default=0.00)
    heat_treatment_method = CharField(max_length=50, default='无')
    heat_treatment_temp = IntegerField(default=0)
    heat_treatment_time = DecimalField(max_digits=5, decimal_places=1, default=0.0)
    heat_input = DecimalField(max_digits=8, decimal_places=2, default=0.00)

    class Meta:
        table_name = 'process_design'

    class Config:   
        orm_mode = True


    @classmethod
    async def add_process(cls, process):  # 添加加工工艺
        result = await async_db.create(ProcessDesign,**process)
        return result.process_id
    
    @classmethod
    async def del_by_process_id(cls, process_id):
        await async_db.execute(ProcessDesign.delete().where(ProcessDesign.process_id == process_id))
    

    @classmethod
    async def update_process(cls, process):
        # 检查是否提供了process_id
        if 'process_id' not in process or not process['process_id']:
            raise ValueError('工艺编码不能为空')
        
        # 检查装备是否存在
        existing_process = await cls.get_process_by_id(process['process_id'])
        if not existing_process:
            raise ValueError(f"工艺编码 '{process['process_id']}' 不存在")
        
        # 创建更新字典（排除)process_id本身，避免更新主键）
        update_data = {k: v for k, v in process.items() if k != 'process_id'}
        
        # 如果没有实际要更新的字段，直接返回
        if not update_data:
            return 0
        
        # 执行更新
        query = ProcessDesign.update(**update_data).where(
            ProcessDesign.process_id == process['process_id']
        )
        affected_rows = await async_db.execute(query)
        
        return affected_rows
    

    @classmethod
    async def get_process_by_id(cls, process_id: str):
        """
        根据工艺ID获取激光焊接工艺信息
        """
        try:
            # 明确指定要查询的字段
            query = cls.select(
                cls.process_id,
                cls.related_material_id,
                cls.related_equipment_id,
                cls.laser_power,
                cls.welding_speed,
                cls.defocus_amount,
                cls.incident_angle,
                cls.welding_sequence,
                cls.groove_type,
                cls.groove_angle,
                cls.joint_type,
                cls.joint_thickness,
                cls.scanning_mode,
                cls.scanning_frequency,
                cls.scanning_amplitude,
                cls.heat_treatment_method,
                cls.heat_treatment_temp,
                cls.heat_treatment_time,
                cls.heat_input
            ).where(cls.process_id == process_id)
            
            process = await async_db.get(query)
            return process
            
        except DoesNotExist:
            return None
        except Exception as e:
            print(f"根据ID查询工艺失败: {e}")
            raise e
        

    @classmethod
    async def select_all(cls, page: int = 1, page_size: int = 20):
        """查询所有工艺 - 包含关联的材料和设备信息（分页）"""
        try:
            # 基础查询
            query = (ProcessDesign
                    .select(
                        # 明确指定所有工艺表字段
                        ProcessDesign.process_id,
                        ProcessDesign.related_material_id,
                        ProcessDesign.related_equipment_id,
                        ProcessDesign.laser_power,
                        ProcessDesign.welding_speed,
                        ProcessDesign.defocus_amount,
                        ProcessDesign.incident_angle,
                        ProcessDesign.welding_sequence,
                        ProcessDesign.groove_type,
                        ProcessDesign.groove_angle,
                        ProcessDesign.joint_type,
                        ProcessDesign.joint_thickness,
                        ProcessDesign.scanning_mode,
                        ProcessDesign.scanning_frequency,
                        ProcessDesign.scanning_amplitude,
                        ProcessDesign.heat_treatment_method,
                        ProcessDesign.heat_treatment_temp,
                        ProcessDesign.heat_treatment_time,
                        ProcessDesign.heat_input,
                        
                        # 材料表字段
                        MaterialInfo.base_material.alias('base_material'),
                        MaterialInfo.material_grade.alias('material_grade'),
                        EquipmentParam.laser_equipment_model.alias('laser_equipment_model'),
                        EquipmentParam.laser_power_range.alias('laser_power_range'),
                        
                        # 设备表字段
                        EquipmentParam.equipment_id.alias('equipment_id'),
                        EquipmentParam.laser_equipment_model.alias('laser_equipment_model'),
                        EquipmentParam.laser_power_range.alias('laser_power_range'),
                        EquipmentParam.output_mode.alias('output_mode'),
                        EquipmentParam.laser_wavelength.alias('laser_wavelength'),
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
                    .order_by(ProcessDesign.process_id.asc()))
            
            # 计算总数
            total_count = await async_db.count(query)
            
            # 应用分页
            query = query.paginate(page, page_size)
            
            # 执行查询
            db_result = await async_db.execute(query.dicts())
            processes = list(db_result)
            
            # 返回分页结果
            return {
                "items": processes,
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size
            }
            
        except Exception as e:
            print(f"查询所有工艺失败: {e}")
            raise e
        
    
    @classmethod
    async def select_with_filter(
    cls, 
    filter_params: ProcessDesignFilter,
    page: int = 1,
    page_size: int = 20
):
        """根据筛选条件查询工艺 - 支持分页"""
        try:
            # 基础查询
            query = (ProcessDesign
                    .select(
                        ProcessDesign.process_id,
                        ProcessDesign.related_material_id,
                        ProcessDesign.related_equipment_id,
                        ProcessDesign.laser_power,
                        ProcessDesign.welding_speed,
                        ProcessDesign.defocus_amount,
                        ProcessDesign.incident_angle,
                        ProcessDesign.welding_sequence,
                        ProcessDesign.groove_type,
                        ProcessDesign.groove_angle,
                        ProcessDesign.joint_type,
                        ProcessDesign.joint_thickness,
                        ProcessDesign.scanning_mode,
                        ProcessDesign.scanning_frequency,
                        ProcessDesign.scanning_amplitude,
                        ProcessDesign.heat_treatment_method,
                        ProcessDesign.heat_treatment_temp,
                        ProcessDesign.heat_treatment_time,
                        ProcessDesign.heat_input,
                        
                        # 关联表字段
                        MaterialInfo.base_material.alias('base_material'),
                        MaterialInfo.material_grade.alias('material_grade'),
                        EquipmentParam.laser_equipment_model.alias('laser_equipment_model'),
                        EquipmentParam.laser_power_range.alias('laser_power_range'),
                    )
                    .join(MaterialInfo, JOIN.LEFT_OUTER,
                        on=(ProcessDesign.related_material_id == MaterialInfo.material_id))
                    .join(EquipmentParam, JOIN.LEFT_OUTER,
                        on=(ProcessDesign.related_equipment_id == EquipmentParam.equipment_id)))
            
            # 应用筛选条件
            if filter_params.process_id:
                query = query.where(ProcessDesign.process_id.contains(filter_params.process_id))
            
            if filter_params.related_material_id:
                query = query.where(ProcessDesign.related_material_id == filter_params.related_material_id)
            
            if filter_params.related_equipment_id:
                query = query.where(ProcessDesign.related_equipment_id == filter_params.related_equipment_id)
            
            # 激光参数范围筛选
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
            
            if filter_params.incident_angle_min is not None:
                query = query.where(ProcessDesign.incident_angle >= filter_params.incident_angle_min)
            if filter_params.incident_angle_max is not None:
                query = query.where(ProcessDesign.incident_angle <= filter_params.incident_angle_max)
            
            # 坡口和接头筛选
            if filter_params.groove_type:
                query = query.where(ProcessDesign.groove_type == filter_params.groove_type)
            
            if filter_params.groove_angle_min is not None:
                query = query.where(ProcessDesign.groove_angle >= filter_params.groove_angle_min)
            if filter_params.groove_angle_max is not None:
                query = query.where(ProcessDesign.groove_angle <= filter_params.groove_angle_max)
            
            if filter_params.joint_type:
                query = query.where(ProcessDesign.joint_type.contains(filter_params.joint_type))
            
            if filter_params.joint_thickness_min is not None:
                query = query.where(ProcessDesign.joint_thickness >= filter_params.joint_thickness_min)
            if filter_params.joint_thickness_max is not None:
                query = query.where(ProcessDesign.joint_thickness <= filter_params.joint_thickness_max)
            
            # 扫描参数筛选
            if filter_params.scanning_mode:
                query = query.where(ProcessDesign.scanning_mode.contains(filter_params.scanning_mode))
            
            if filter_params.scanning_frequency_min is not None:
                query = query.where(ProcessDesign.scanning_frequency >= filter_params.scanning_frequency_min)
            if filter_params.scanning_frequency_max is not None:
                query = query.where(ProcessDesign.scanning_frequency <= filter_params.scanning_frequency_max)
            
            if filter_params.scanning_amplitude_min is not None:
                query = query.where(ProcessDesign.scanning_amplitude >= filter_params.scanning_amplitude_min)
            if filter_params.scanning_amplitude_max is not None:
                query = query.where(ProcessDesign.scanning_amplitude <= filter_params.scanning_amplitude_max)
            
            # 热处理筛选
            if filter_params.heat_treatment_method:
                query = query.where(ProcessDesign.heat_treatment_method.contains(filter_params.heat_treatment_method))
            
            if filter_params.heat_treatment_temp_min is not None:
                query = query.where(ProcessDesign.heat_treatment_temp >= filter_params.heat_treatment_temp_min)
            if filter_params.heat_treatment_temp_max is not None:
                query = query.where(ProcessDesign.heat_treatment_temp <= filter_params.heat_treatment_temp_max)
            
            if filter_params.heat_treatment_time_min is not None:
                query = query.where(ProcessDesign.heat_treatment_time >= filter_params.heat_treatment_time_min)
            if filter_params.heat_treatment_time_max is not None:
                query = query.where(ProcessDesign.heat_treatment_time <= filter_params.heat_treatment_time_max)
            
            # 热输入筛选
            if filter_params.heat_input_min is not None:
                query = query.where(ProcessDesign.heat_input >= filter_params.heat_input_min)
            if filter_params.heat_input_max is not None:
                query = query.where(ProcessDesign.heat_input <= filter_params.heat_input_max)
            
            # 计算总数
            total_query = query
            total_count = await async_db.count(total_query)
            
            # 分页处理
            query = query.order_by(ProcessDesign.process_id.asc())
            query = query.paginate(page, page_size)
            
            # 执行查询
            db_result = await async_db.execute(query.dicts())
            processes = list(db_result)
        
            # 返回分页结果
            return {
                "items": processes,
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size
            }
            
        except Exception as e:
            print(f"筛选查询工艺失败: {e}")
            raise e