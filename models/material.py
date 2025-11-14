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