from peewee import IntegerField, CharField

from common.session import BaseModel, async_db


class FileInfo(BaseModel):
    id = CharField(primary_key=True)
    bizId = CharField(column_name='biz_id')
    bizType = CharField(column_name='biz_type')
    fileName = CharField(column_name='file_name')
    newName = CharField(column_name='new_name')
    fileType = CharField(column_name='file_type')
    fileSize = CharField(column_name='file_size')
    downloadUrl = CharField(column_name='download_url')
    viewUrl = CharField(column_name='view_url')


    class Meta:
        table_name = "file_info"

    class Config:
        orm_mode = True

    @classmethod
    async def add(cls,fileInfo):
        # result = await async_db.execute(FileInfo.create(**department))
        result = await async_db.create(FileInfo, **fileInfo)
        return result.id

    @classmethod
    async def update(cls, fileInfo):
        # result = await async_db.execute(FileInfo.create(**department))
        u = await async_db.execute(FileInfo.update(**fileInfo).where(FileInfo.id == fileInfo['id']))

        return u
    @classmethod
    async def fuzzy_query(cls, queryInfo):
        db = await async_db.execute(
            FileInfo.select().where(
                FileInfo.bizId.contains(queryInfo['bizId']),
                FileInfo.bizType.contains(queryInfo['bizType']
                                       )).order_by(
            FileInfo.createAt.desc()).dicts())
        result = list(db)
        return result
    # FileInfo.name == querydepartment['name']
    @classmethod
    async def select_all(cls):  # 获取
        db = await async_db.execute(FileInfo.select().dicts())
        # 附加 iterator() 方法调用还可以减少内存消耗
        return list(db)
    @classmethod
    async def delete_by_biz_id(cls,bizId):  # 获取
        await async_db.execute(
            FileInfo.delete().where(FileInfo.bizId==bizId))
    @classmethod
    async def delete_by_biz_id_list(cls,bizIdList):  # 获取
        await async_db.execute(
            FileInfo.delete().where(FileInfo.bizId.in_(bizIdList)))