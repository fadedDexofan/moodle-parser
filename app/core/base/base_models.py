from tortoise import fields, models


class BaseDBModel(models.Model):
    id = fields.UUIDField(unique=True, pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    async def to_dict(self):
        d = {field: getattr(self, field) for field in self._meta.db_fields}
        for field in self._meta.backward_fk_fields:
            d[field] = await getattr(self, field).all().values()
        return d

    class Meta:
        abstract = True
