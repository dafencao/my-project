from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, IntegerField, DecimalField, DoesNotExist
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import IntegrityError


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
    async def add_process(cls, process):  # 添加部门
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
    async def select_all(cls):
        """查询所有设备 - 排除基类字段"""
        try:
            # 明确指定要查询的字段，排除 createAt 和 updateAt
            query = (cls
                    .select(
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
                        # 不选择 createAt 和 updateAt
                    )
                    .order_by(cls.process_id)
                    .dicts())
            
            db_result = await async_db.execute(query)
            return list(db_result)
            
        except Exception as e:
            print(f"查询所有工艺失败: {e}")
            raise e