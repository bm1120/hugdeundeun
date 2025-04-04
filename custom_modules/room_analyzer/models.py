from pydantic import BaseModel, Field
from typing import TypedDict, Optional

class RoomDescription(BaseModel):
    """방 구조에 대한 설명을 담는 모델"""
    num_room: int = Field(description="방의 수")
    num_balcony: int = Field(description="발코니 수")
    num_wc: int = Field(description="화장실 수")
    description: str = Field(description="방구조에 대한 설명")
    
class CheckDescription(BaseModel):
    """방 구조 설명의 정확도를 검증하는 모델"""
    num_room_accuracy: bool = Field(description="방 갯수 일치여부")
    num_balcony_accuracy: bool = Field(description="발코니 수 일치여부")
    num_wc_accuracy: bool = Field(description="화장실 수 일치여부")
    description_adequacy: bool = Field(description="방구조에 대한 설명의 적절성")

class GraphState(TypedDict):
    """LangGraph 워크플로우의 상태를 관리하는 모델"""
    image_id: str  # 이미지 식별자
    image_url: str  # 이미지 URL
    image_str: Optional[str]  # Base64로 인코딩된 이미지 문자열
    image_description: Optional[RoomDescription]  # 이미지 설명
    description_accuracy: Optional[CheckDescription]  # 설명 정확도
    error: Optional[str]  # 에러 메시지
    regenerate_count: int = 0  # 재생성 시도 횟수, 기본값 0
    loaded_from_file: Optional[bool] = None  # 파일에서 로드되었는지 여부