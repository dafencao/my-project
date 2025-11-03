from venv import create

# TODO:userinfo=>user_text
from peewee import CharField, IntegerField, DateTimeField, JOIN, Model, fn
from peewee_async import select

from common.session import BaseModel, paginator, db, async_db
from utils.tools_func import convert_num_arr, convert_arr


# from user_test import TestPost

class TestPost(BaseModel):
    id = IntegerField(primary_key=True)
    post = CharField()

    #
    # createAt = DateTimeField(column_name='create_at')
    # updateAt = DateTimeField(column_name='update_at')

    class Meta:
        table_name = 'testpost'


class UserTest(BaseModel):
    """
    我的测试表
    """
    id = IntegerField(primary_key=True)  # id

    oraCode = IntegerField(column_name='ora_code')  # 部门
    password = CharField()  # 密码
    realName = CharField(column_name='real_name')  # 真实姓名
    phone = CharField()  # 电话号码
    account = CharField()
    email = CharField()  # 邮箱
    postid = IntegerField()
    createAt = DateTimeField(column_name='create_at')
    updateAt = DateTimeField(column_name='update_at')
    class Meta:
        table_name = 'user_test'  # 映射到我自己创建的练习表格名

    # @classmethod
    # async def select_all(cls):  # 通过id查询用户信息
    #     db = await async_db.execute(select(
    #         UserTest,
    #         fn.group_concat(TestPost)
    #         .python_value(convert_num_arr).alias('post')).
    #                                 join(UserTest, JOIN.LEFT_OUTER,
    #                                      on=(UserTest,TestPost)).where(UserTest.postid == TestPost.id).dicts())
    #
    #     result = list(db)[0]
    #     return result





    @classmethod
    async def add_user(cls, user_test):  # 添加用户
        result = await async_db.create(UserTest, **user_test)
        # result = db.create(UserTest, **user_test)

        return result.id

    @classmethod
    async def add_post(cls, testpost):  # 添加部门
        result = await async_db.create(TestPost, **testpost)
        return result.id


    @classmethod
    async def del_by_user_testid(cls, user_testid):  # 通过用户id删除信息
        result =  await async_db.execute(UserTest.delete().where(UserTest.id ==
                                                              user_testid))
        return result

    @classmethod
    async def update_user_test(cls, user_test:Model):   #更新
        result = await async_db.update(user_test)

        # result = await async_db.execute(user.save())

        return result
    @classmethod
    async def select_by_user_test_id(cls, id:int):  # id查询
        result = await async_db.execute(
                UserTest.select(UserTest,
                                fn.group_concat(UserTest.id)
                                .python_value(convert_num_arr)
                                .alias('testId'),
                                fn.group_concat(UserTest.realName)
                                .python_value(convert_arr)
                                .alias('testName'),
                                TestPost.post.alias('testpost'))
                .join(TestPost, JOIN.LEFT_OUTER,
                     on=(UserTest.postid == TestPost.id)
                     )
                    .group_by(UserTest.id).where(UserTest.id == id).dicts())
        return list(result)


    @classmethod
    async def select_by_user_test_putin(cls, putin):  # 模糊查询
        putin = str('%' + putin + '%')
        # result = await async_db.execute(
        #     UserTest.select().where(UserTest.realName ** putin).dicts())
        result = await async_db.execute(
            UserTest.select().where(UserTest.realName.contains(putin)).dicts())
        return list(result)










