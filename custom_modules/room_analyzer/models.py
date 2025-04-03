from pydantic import BaseModel, Field
from typing import TypedDict, Optional

class RoomDescription(BaseModel):
    num_room: int = Field(description="방의 수")
    num_balcony: int = Field(description="발코니 수")
    num_wc: int = Field(description="화장실 수")
    description: str = Field(description="방구조에 대한 설명")
    
class CheckDescription(BaseModel):
    num_room_accuracy: bool = Field(description="방 갯수 일치여부")
    num_balcony_accuracy: bool = Field(description="발코니 수 일치여부")
    num_wc_accuracy: bool = Field(description="화장실 수 일치여부")
    description_adequacy: bool = Field(description="방구조에 대한 설명의 적절성")

class GraphState(TypedDict):
    image_id:str
    image_url: str
    image_str: Optional[str]
    image_description: Optional[RoomDescription]
    description_accuracy: Optional[CheckDescription]
    error: Optional[str]
    regenerate_count: int