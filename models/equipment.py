from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, IntegerField, DecimalField, DoesNotExist
from playhouse.shortcuts import model_to_dict, dict_to_model
from sqlalchemy.orm import relationship
from peewee import fn




class EquipmentParam(BaseModel):
    equipment_id = CharField(max_length=20, primary_key=True)
    laser_equipment_model = CharField(max_length=100)
    laser_power_range = CharField(max_length=20)
    output_mode = CharField(choices=[('连续激光', '连续激光'), ('脉冲激光', '脉冲激光')])
    laser_wavelength = IntegerField(default=0)
    spot_diameter = DecimalField(max_digits=5, decimal_places=2, default=0.00)
    auxiliary_equipment_type = CharField(max_length=50, default='')
    auxiliary_equipment_model = CharField(max_length=50, default='')
    sensor_type = CharField(max_length=50, default='')
    sensor_precision = CharField(max_length=30, default='')
    class Meta:
        table_name = 'equipment_param'

    class Config:   
        orm_mode = True


    @classmethod
    async def add_equipment(cls, equipment):  # 添加部门
        result = await async_db.create(EquipmentParam,**equipment)
        return result.equipment_id
    

    @classmethod
    async def del_by_equipment_id(cls, equipment_id):
        await async_db.execute(EquipmentParam.delete().where(EquipmentParam.equipment_id == equipment_id))


    @classmethod
    async def update_equipment(cls, equipment):
        # 检查是否提供了equipment_id
        if 'equipment_id' not in equipment or not equipment['equipment_id']:
            raise ValueError('装备编码不能为空')
        
        # 检查装备是否存在
        existing_equipment = await cls.get_equipment_by_id(equipment['equipment_id'])
        if not existing_equipment:
            raise ValueError(f"母材编码 '{equipment['equipment_id']}' 不存在")
        
        # 创建更新字典（排除equipment_id本身，避免更新主键）
        update_data = {k: v for k, v in equipment.items() if k != 'equipment_id'}
        
        # 如果没有实际要更新的字段，直接返回
        if not update_data:
            return 0
        
        # 执行更新
        query = EquipmentParam.update(**update_data).where(
            EquipmentParam.equipment_id == equipment['equipment_id']
        )
        affected_rows = await async_db.execute(query)
        
        return affected_rows
    

    @classmethod
    async def get_equipment_by_id(cls, equipment_id: str):
        """
        根据设备ID获取激光焊接设备信息
        
        Args:
            equipment_id: 设备唯一标识
            
        Returns:
            EquipmentParam 对象或 None
        """
        try:
            # 明确指定要查询的字段
            query = cls.select(
                cls.equipment_id,
                cls.laser_equipment_model,
                cls.laser_power_range,
                cls.output_mode,
                cls.laser_wavelength,
                cls.spot_diameter,
                cls.auxiliary_equipment_type,
                cls.auxiliary_equipment_model,
                cls.sensor_type,
                cls.sensor_precision
            ).where(cls.equipment_id == equipment_id)
            
            equipment = await async_db.get(query)
            return equipment
            
        except DoesNotExist:
            return None
        except Exception as e:
            print(f"根据ID查询设备失败: {e}")
            raise e
        

    @classmethod
    async def select_all(cls):
        """查询所有设备 - 排除基类字段"""
        try:
            # 明确指定要查询的字段，排除 createAt 和 updateAt
            query = (cls
                    .select(
                        cls.equipment_id,
                        cls.laser_equipment_model,
                        cls.laser_power_range,
                        cls.output_mode,
                        cls.laser_wavelength,
                        cls.spot_diameter,
                        cls.auxiliary_equipment_type,
                        cls.auxiliary_equipment_model,
                        cls.sensor_type,
                        cls.sensor_precision
                        # 不选择 createAt 和 updateAt
                    )
                    .order_by(cls.equipment_id)
                    .dicts())
            
            db_result = await async_db.execute(query)
            return list(db_result)
            
        except Exception as e:
            print(f"查询所有设备失败: {e}")
            raise e
        

    @classmethod
    async def search_equipment(cls, filter_params: dict, page: int = 1, page_size: int = 20):
        """
        使用安全的查询方式筛选设备
        """
        try:
            # 使用只选择必要字段的方式
            select_fields = [
                cls.equipment_id,
                cls.laser_equipment_model,
                cls.laser_power_range,
                cls.output_mode,
                cls.laser_wavelength,
                cls.spot_diameter,
                cls.auxiliary_equipment_type,
                cls.auxiliary_equipment_model,
                cls.sensor_type,
                cls.sensor_precision
            ]
            
            # 构建查询
            query = cls.select(*select_fields)
            
            # 应用筛选条件
            query = cls._apply_equipment_filters(query, filter_params)
            
            # 计算总数
            total_count = await async_db.count(query)
            
            # 应用分页
            offset = (page - 1) * page_size
            equipment_list = await async_db.execute(query.offset(offset).limit(page_size))
            
            # 转换为字典列表
            equipment_data = []
            for equipment in equipment_list:
                equipment_data.append(cls._equipment_to_dict(equipment))
            
            return {
                "data": equipment_data,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": (total_count + page_size - 1) // page_size,
                    "has_prev": page > 1,
                    "has_next": page * page_size < total_count
                }
            }
            
        except Exception as e:
            print(f"搜索设备数据库错误: {e}")
            raise e

    @classmethod
    def _apply_equipment_filters(cls, query, filters: dict):
        """
        应用设备筛选条件到查询
        """
        # 精确匹配的字段
        exact_match_fields = ['laser_equipment_model', 'output_mode', 'auxiliary_equipment_type', 'sensor_type']
        
        # 应用精确匹配条件
        for field in exact_match_fields:
            if field in filters and filters[field]:
                # 使用模糊匹配
                query = query.where(getattr(cls, field).contains(filters[field]))
        
        # 处理激光功率范围筛选
        if 'laser_power_min' in filters and filters['laser_power_min'] is not None:
        # 方法1: 使用SUBSTRING_INDEX提取最小值
          min_power = fn.CAST(
              fn.SUBSTRING_INDEX(cls.laser_power_range, '-', 1), 
              'SIGNED'
          )
          query = query.where(min_power >= filters['laser_power_min'])
      
        if 'laser_power_max' in filters and filters['laser_power_max'] is not None:
            # 方法1: 使用SUBSTRING_INDEX提取最大值
            max_power = fn.CAST(
                fn.SUBSTRING_INDEX(cls.laser_power_range, '-', -1), 
                'SIGNED'
            )
            query = query.where(max_power <= filters['laser_power_max'])
          
        # 应用数值范围筛选条件
        range_fields = {
            'laser_wavelength': ('laser_wavelength_min', 'laser_wavelength_max'),
            'spot_diameter': ('spot_diameter_min', 'spot_diameter_max')
        }
        
        for field, (min_key, max_key) in range_fields.items():
            field_attr = getattr(cls, field)
            
            if min_key in filters and filters[min_key] is not None:
                query = query.where(field_attr >= filters[min_key])
            
            if max_key in filters and filters[max_key] is not None:
                query = query.where(field_attr <= filters[max_key])
        
        return query
    

    @classmethod
    def _equipment_to_dict(cls, equipment):
        """
        将设备模型对象转换为字典
        """
        return {
            'equipment_id': equipment.equipment_id,
            'laser_equipment_model': equipment.laser_equipment_model,
            'laser_power_range': equipment.laser_power_range,
            'output_mode': equipment.output_mode,
            'laser_wavelength': equipment.laser_wavelength,
            'spot_diameter': float(equipment.spot_diameter) if equipment.spot_diameter else 0.00,
            'auxiliary_equipment_type': equipment.auxiliary_equipment_type or "",
            'auxiliary_equipment_model': equipment.auxiliary_equipment_model or "",
            'sensor_type': equipment.sensor_type or "",
            'sensor_precision': equipment.sensor_precision or ""
        }