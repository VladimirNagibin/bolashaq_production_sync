from pydantic import BaseModel, Field, field_validator  # , EmailStr


# === Модели запроса ===
class ProductItem(BaseModel):
    product: str | None = Field(default=None, max_length=500)
    product_id: int | None = Field(default=None, ge=0)
    product_code: str | None  = None
    article: str | None = None
    price: float | None = Field(default=0.0, ge=0)
    quantity: int | None = Field(default=1, ge=0)
    
    class Config:
        extra = "ignore"


class SiteRequestPayload(BaseModel):
    # === Мета ===
    type_event: str #  = Field(default="new_request", pattern="^(new_request|update|cancel)$")
    message_id: int | None = None # Field(default=None, max_length=100)
    
    # === Контакты ===
    name: str | None = Field(default=None, max_length=255)
    phone: str | None = None
    email: str | None = None
    # phone: str | None = Field(default=None, pattern=r'^[\d\+\s\-\(\)]{7,20}$')
    # email: EmailStr | None = None  # Автоматическая валидация формата email
    bin_company: str | None = Field(default=None, max_length=50)
    comment: str | None = Field(default=None, max_length=2000)
    
    # === Товары (единичный + список) ===
    product_id: int | None = Field(default=None, ge=0)
    # product_name: str | None = Field(default=None, alias="product", max_length=500)
    product: str | None = Field(default=None, max_length=500)
    products: list[ProductItem] = Field(default_factory=list)
    
    class Config:
        populate_by_name = True
        extra = "ignore"
    
    @field_validator('products')
    @classmethod
    def ensure_products_list(cls, v):
        if v is None:
            return []
        return v if isinstance(v, list) else [v]
    
    @field_validator('phone')
    @classmethod
    def clean_phone(cls, v):
        if v:
            # Удаляем всё кроме цифр и +
            return ''.join(c for c in v if c.isdigit() or c == '+')
        return v