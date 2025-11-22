from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, IntegerField, DecimalField, DoesNotExist
from peewee import JOIN
from models.material import MaterialInfo
from models.equipment import EquipmentParam
from schemas.request.processDesign_schema import ProcessDesignFilter


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