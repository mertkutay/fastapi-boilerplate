from tortoise import fields, models


class User(models.Model):
    id = fields.BigIntField(pk=True)
    email = fields.CharField(254, unique=True)
    password = fields.CharField(128)
    full_name = fields.CharField(180, default="")
    is_active = fields.BooleanField(default=True)
    is_superuser = fields.BooleanField(default=False)
    is_verified = fields.BooleanField(default=False)

    def __str__(self) -> str:
        return f"User(email={self.email})"


class OutstandingToken(models.Model):
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", on_delete=fields.CASCADE
    )

    jti = fields.CharField(255, unique=True)
    token = fields.TextField()

    created_at = fields.DatetimeField()
    expires_at = fields.DatetimeField()

    def __str__(self) -> str:
        return f"OutstandingToken(user={self.user}, jti={self.jti})"


class BlacklistedToken(models.Model):
    token: fields.OneToOneRelation[OutstandingToken] = fields.OneToOneField(
        "models.OutstandingToken", on_delete=fields.CASCADE
    )

    blacklisted_at = fields.DatetimeField()

    def __str__(self) -> str:
        return f"Blacklisted token for {self.token.user}"
