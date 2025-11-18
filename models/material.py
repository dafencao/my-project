from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, IntegerField, DecimalField
from playhouse.shortcuts import model_to_dict, dict_to_model
from sqlalchemy.orm import relationship
from peewee import IntegrityError





class MaterialInfo(BaseModel):
    # 材料唯一标识（格式：MAT-序号）
    material_id = CharField(max_length=20, primary_key=True)
    # 母材材质（如TC4钛合金、6061铝合金）
    base_material = CharField(max_length=50)
    # 母材牌号（行业标准牌号）
    material_grade = CharField(max_length=50, default='')
    # 化学成分（如Ti-6Al-4V）
    chemical_composition = CharField(max_length=100, default='')
    # 抗拉强度（MPa，室温测试值）
    tensile_strength = IntegerField(default=0)
    # 硬度（HRC）
    hardness = DecimalField(max_digits=5,decimal_places=1,default=0.0)
    # 熔点（℃）
    melting_point = IntegerField(default=0)
    # 热导率（W/(m·K)，室温测试值）
    thermal_conductivity = DecimalField(max_digits=6,decimal_places=2,default=0.00)
    # 填充焊丝规格（无则填"无"）
    filler_wire_spec = CharField(max_length=50, default='无')
    # 保护气类型（如氩气、氦气）
    shielding_gas_type = CharField(max_length=30)
    # 保护气纯度（%）
    shielding_gas_purity = DecimalField(max_digits=5,decimal_places=2,default=0.00)
    class Meta:
        table_name = 'material_info'

    class Config:   
        orm_mode = True


    @classmethod
    async def add_material(cls, material):  # 添加部门
        result = await async_db.create(MaterialInfo,**material)
        return result.material_id
    

    @classmethod
    async def del_by_material_id(cls, material_id):
        await async_db.execute(MaterialInfo.delete().where(MaterialInfo.material_id == material_id))


    @classmethod
    async def update_material(cls, material):
        # 检查是否提供了material_id
        if 'material_id' not in material or not material['material_id']:
            raise ValueError('母材编码不能为空')
        
        # 检查母材是否存在
        existing_material = await cls.get_material_by_id(material['material_id'])
        if not existing_material:
            raise ValueError(f"母材编码 '{material['material_id']}' 不存在")
        
        # 创建更新字典（排除material_id本身，避免更新主键）
        update_data = {k: v for k, v in material.items() if k != 'material_id'}
        
        # 如果没有实际要更新的字段，直接返回
        if not update_data:
            return 0
        
        # 执行更新
        query = MaterialInfo.update(**update_data).where(
            MaterialInfo.material_id == material['material_id']
        )
        affected_rows = await async_db.execute(query)
        
        return affected_rows
    

    @classmethod
    async def search_materials(cls, filter_params: dict, page: int = 1, page_size: int = 20):
        """
        使用安全的查询方式
        """
        try:
            # 使用只选择必要字段的方式
            select_fields = [
                MaterialInfo.material_id,
                MaterialInfo.base_material,
                MaterialInfo.material_grade,
                MaterialInfo.chemical_composition,
                MaterialInfo.tensile_strength,
                MaterialInfo.hardness,
                MaterialInfo.melting_point,
                MaterialInfo.thermal_conductivity,
                MaterialInfo.filler_wire_spec,
                MaterialInfo.shielding_gas_type,
                MaterialInfo.shielding_gas_purity
            ]
            
            # 构建查询
            query = MaterialInfo.select(*select_fields)
            
            # 应用筛选条件
            query = cls._apply_filters(query, filter_params)
            
            # 计算总数
            total_count = await async_db.count(query)
            
            # 应用分页
            offset = (page - 1) * page_size
            materials = await async_db.execute(query.offset(offset).limit(page_size))
            
            # 转换为字典列表
            material_list = []
            for material in materials:
                material_list.append({
                    'material_id': material.material_id,
                    'base_material': material.base_material,
                    'material_grade': material.material_grade or "",
                    'chemical_composition': material.chemical_composition or "",
                    'tensile_strength': material.tensile_strength or 0,
                    'hardness': float(material.hardness) if material.hardness else 0.0,
                    'melting_point': material.melting_point or 0,
                    'thermal_conductivity': float(material.thermal_conductivity) if material.thermal_conductivity else 0.00,
                    'filler_wire_spec': material.filler_wire_spec or "无",
                    'shielding_gas_type': material.shielding_gas_type,
                    'shielding_gas_purity': float(material.shielding_gas_purity) if material.shielding_gas_purity else 0.00
                })
            
            return {
                "data": material_list,
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
            print(f"搜索材料数据库错误: {e}")
            raise e

    @classmethod
    def _apply_filters(cls, query, filters: dict):
        """
        应用筛选条件到查询
        """
        from peewee import fn
        
        # 精确匹配的字段
        exact_match_fields = ['base_material', 'material_grade', 'chemical_composition', 
                            'filler_wire_spec', 'shielding_gas_type']
        
        # 范围匹配的字段
        range_fields = {
            'tensile_strength': ('tensile_strength_min', 'tensile_strength_max'),
            'hardness': ('hardness_min', 'hardness_max'),
            'melting_point': ('melting_point_min', 'melting_point_max'),
            'thermal_conductivity': ('thermal_conductivity_min', 'thermal_conductivity_max'),
            'shielding_gas_purity': ('shielding_gas_purity_min', 'shielding_gas_purity_max')
        }
        
        # 应用精确匹配条件
        for field in exact_match_fields:
            if field in filters and filters[field]:
                # 使用模糊匹配
                query = query.where(getattr(MaterialInfo, field).contains(filters[field]))
        
        # 应用范围匹配条件
        for field, (min_key, max_key) in range_fields.items():
            field_attr = getattr(MaterialInfo, field)
            
            if min_key in filters and filters[min_key] is not None:
                query = query.where(field_attr >= filters[min_key])
            
            if max_key in filters and filters[max_key] is not None:
                query = query.where(field_attr <= filters[max_key])
        
        return query

    @classmethod
    def _model_to_dict(cls, material):
        """
        将模型对象转换为字典
        """
        return {
            'material_id': material.material_id,
            'base_material': material.base_material,
            'material_grade': material.material_grade,
            'chemical_composition': material.chemical_composition,
            'tensile_strength': material.tensile_strength,
            'hardness': float(material.hardness) if material.hardness else 0.0,
            'melting_point': material.melting_point,
            'thermal_conductivity': float(material.thermal_conductivity) if material.thermal_conductivity else 0.00,
            'filler_wire_spec': material.filler_wire_spec,
            'shielding_gas_type': material.shielding_gas_type,
            'shielding_gas_purity': float(material.shielding_gas_purity) if material.shielding_gas_purity else 0.00
        }
    

    @classmethod
    async def select_all(cls):
        """查询所有母材 - 排除基类字段"""
        try:
            # 明确指定要查询的字段，排除 createAt 和 updateAt
            query = (cls
                    .select(
                        cls.material_id,
                        cls.base_material,
                        cls.material_grade,
                        cls.chemical_composition,
                        cls.tensile_strength,
                        cls.hardness,
                        cls.melting_point,
                        cls.thermal_conductivity,
                        cls.filler_wire_spec,
                        cls.shielding_gas_type,
                        cls.shielding_gas_purity
                        # 不选择 createAt 和 updateAt
                    )
                    .order_by(cls.material_id)
                    .dicts())
            
            db_result = await async_db.execute(query)
            return list(db_result)
            
        except Exception as e:
            print(f"查询所有母材失败: {e}")
            raise e