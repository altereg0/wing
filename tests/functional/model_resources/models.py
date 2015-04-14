from datetime import datetime
import peewee

db = peewee.SqliteDatabase(':memory:')


class User(peewee.Model):
    name = peewee.CharField()
    is_active = peewee.BooleanField(default=False)
    modification_date = peewee.DateTimeField()

    class Meta:
        database = db

    def save(self, force_insert=False, only=None):
        self.modification_date = datetime.now()
        super().save(force_insert, only)


class Category(peewee.Model):
    title = peewee.CharField()
    slug = peewee.CharField()

    class Meta:
        database = db


class Post(peewee.Model):
    title = peewee.CharField()
    slug = peewee.CharField()
    category = peewee.ForeignKeyField(Category, null=True)
    content = peewee.TextField(default='')

    class Meta:
        database = db