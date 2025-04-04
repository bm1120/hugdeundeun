from .models import GraphState
from typing import Literal
from .nodes import logger

def decide_to_generate(state: GraphState) -> Literal["end", "generate"]:
    """
    Determines whether to generate an answer, or end the workflow.

    Args:
        state (GraphState): The current graph state

    Returns:
        str: Binary decision for next node to call
    """
    if state.get('error'):
        logger.error(f"에러 발생: {state['error']}")
        return "end"  # 에러 발생 시 워크플로우 종료
        
    if not state.get('image_str'):
        logger.error("이미지가 없습니다.")
        return "end"  # 이미지가 없으면 워크플로우 종료
        
    logger.info("이미지 생성 진행")
    return "generate"

def decide_to_regenerate(state: GraphState) -> Literal["nextstep", "regenerate", "end"]:
    """
    Determines whether to regenerate an answer, proceed to next step, or end the workflow.

    Args:
        state (GraphState): The current graph state

    Returns:
        str: Decision for next node to call
    """
    # 현재 regenerate_count 출력 (디버깅용)
    current_count = state.get('regenerate_count', 0)
    logger.info(f"현재 재생성 횟수: {current_count}")
    
    # 재시도 최대 횟수 정의
    max_regenerations = 3
    
    # 최대 재시도 횟수 초과 여부 확인 (어떤 조건에서든 우선 확인)
    if current_count >= max_regenerations:
        logger.error(f"최대 재시도 횟수({max_regenerations})에 도달했습니다. 워크플로우를 종료합니다.")
        return "end"
    
    # 에러 여부 확인
    if state.get('error'):
        logger.warning(f"에러 발생: {state['error']}")
        return "regenerate"
        
    # 검증 결과 확인
    accuracy = state.get('description_accuracy')
    if not accuracy:
        logger.warning("검증 결과가 없습니다. 재생성합니다.")
        return "regenerate"
        
    # 모든 검증 통과 확인
    if (accuracy.num_room_accuracy and 
        accuracy.num_balcony_accuracy and 
        accuracy.num_wc_accuracy and 
        accuracy.description_adequacy):
        logger.info("모든 검증이 통과되었습니다.")
        return "nextstep"
        
    # 검증 실패로 재생성 진행
    logger.warning(f"검증 실패. 재생성합니다. (시도 {current_count + 1}/{max_regenerations})")
    return "regenerate"