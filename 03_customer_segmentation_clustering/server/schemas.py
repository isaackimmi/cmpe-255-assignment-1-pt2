from pydantic import BaseModel, Field

class Observation(BaseModel):
    annual_income_k: float = Field(ge=15)
    spend_score: float = Field(ge=1, le=99)
    purchase_frequency: float = Field(ge=0.2)
    avg_order_value: float = Field(ge=5)
