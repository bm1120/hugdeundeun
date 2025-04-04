from langgraph.graph import StateGraph, START, END
from .nodes import download_image, save_image, describe_image, check_image_description, get_default_llm
from .edges import decide_to_generate, decide_to_regenerate
from .models import GraphState
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Optional, Dict, List, Any, TypedDict

# 병렬 노드 반환 타입 정의
class SaveImageBranch(TypedDict):
    """이미지 저장 작업의 병렬 분기 결과"""
    save_result: None  # 이미지 저장 결과 (상태를 변경하지 않음)

def make_workflow(llm: Optional[BaseChatModel] = None) -> StateGraph:
    """
    LLM을 인자로 받아 방 구조 분석 워크플로우를 생성하는 함수
    
    이미지 다운로드 후 저장은 병렬로 진행하고, 이미지 분석은 메인 흐름에서 진행

    Args:
        llm (BaseChatModel, optional): 사용할 LLM 모델. 기본값은 None이며, 
                                      None인 경우 기본 모델 사용

    Returns:
        StateGraph: 컴파일된 LangGraph 워크플로우
    """
    # llm이 None인 경우 기본 모델 설정
    llm_instance = llm or get_default_llm()

    # Define a new graph
    workflow = StateGraph(GraphState)

    # Define the nodes
    workflow.add_node("download_image", download_image)
    
    # 이미지 저장 병렬 노드: 상태를 변경하지 않고 별도 작업만 수행
    def save_image_branch(state: GraphState) -> Dict[str, Dict[str, Any]]:
        """다운로드된 이미지를 저장하는 병렬 노드"""
        # 이미지 저장 실행
        save_image(state)
        # 상태 변경 없이 병렬 노드 결과 반환
        return {"save_result": None}
    
    # 병렬 노드 추가: 다운로드 이미지를 계속 사용하면서 저장도 병렬로 수행
    workflow.add_node("save_image_branch", save_image_branch)
    
    # LLM을 사용하는 노드들에 llm_instance 전달
    workflow.add_node("describe_image", lambda state: describe_image(state, llm=llm_instance))
    workflow.add_node("check_image_description", lambda state: check_image_description(state, llm=llm_instance))

    # Add edges
    workflow.add_edge(START, "download_image")
    
    # 이미지 다운로드 후 병렬 처리
    # 1. 이미지 저장 브랜치
    workflow.add_edge("download_image", "save_image_branch")
    # 이미지 저장 브랜치는 결과를 반환하지만 메인 워크플로우에 영향을 주지 않음
    
    # 2. 메인 경로: 다운로드 → 이미지 설명
    workflow.add_conditional_edges(
        "download_image",
        decide_to_generate,
        {
            "end": END,
            "generate": "describe_image"
        }
    )

    workflow.add_edge("describe_image", "check_image_description")

    workflow.add_conditional_edges(
        "check_image_description",
        decide_to_regenerate,
        {
            "nextstep": END,
            "regenerate": "describe_image",
            "end": END
        }
    )

    # Compile
    graph = workflow.compile()

    return graph