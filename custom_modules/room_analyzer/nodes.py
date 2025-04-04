from .models import GraphState, RoomDescription, CheckDescription
import time
import requests
import base64
from langchain_core.messages import HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel
import logging
from langchain.output_parsers import PydanticOutputParser
from langchain import hub
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from typing import Optional

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


parser = PydanticOutputParser(pydantic_object=RoomDescription)
check_parser = PydanticOutputParser(pydantic_object=CheckDescription)


def download_image(state: GraphState) -> GraphState:
    """
    Download image with retry logic and error handling
    If the image is already downloaded, load it from the file system

    Args:
        state (GraphState): The current graph state

    Returns:
        GraphState: Updated state with image_str or error
    """
    logger.info("---DOWNLOAD IMAGE ---")
    
    # 이미지 저장 경로 설정
    save_dir = "downloaded_images"
    os.makedirs(save_dir, exist_ok=True)
    
    # 이미지 파일명 생성 (image_id 기반)
    filename = f"{state['image_id']:03d}.png"
    file_path = os.path.join(save_dir, filename)
    
    # 파일 로드 시도 플래그
    loaded_from_file = False
    
    # 이미 파일이 존재하는지 확인
    if os.path.exists(file_path):
        logger.info(f"이미지 파일이 이미 존재합니다: {file_path}")
        try:
            # 파일에서 이미지 로드
            with open(file_path, 'rb') as f:
                image_data = f.read()
            
            # 이미지를 base64로 인코딩
            img_str = base64.b64encode(image_data).decode('utf-8')
            
            # 파일 로드 성공
            loaded_from_file = True
            
            return {
                **state,
                "image_str": img_str,
                "error": None,
                "loaded_from_file": True  # 파일에서 로드했음을 표시
            }
        except Exception as e:
            logger.warning(f"기존 파일 로드 실패: {str(e)}. 다시 다운로드합니다.")
            # 파일 로드 실패 시 loaded_from_file은 False 유지
    
    # 파일이 없거나 로드에 실패한 경우에만 다운로드 시도
    if not loaded_from_file:
        logger.info("파일에서 로드하지 못했으므로 이미지를 다운로드합니다.")
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = requests.get(state['image_url'], timeout=30)
                response.raise_for_status()
                
                # 이미지 데이터가 PNG인지 확인
                if not response.content.startswith(b'\x89PNG\r\n\x1a\n'):
                    raise ValueError("이미지가 PNG 형식이 아닙니다")
                
                # 이미지를 base64로 인코딩
                img_str = base64.b64encode(response.content).decode('utf-8')
                
                return {
                    **state,
                    "image_str": img_str,
                    "error": None,
                    "loaded_from_file": False  # 새로 다운로드했음을 표시
                }
                
            except Exception as e:
                if attempt == max_retries - 1:
                    error_msg = f"이미지 다운로드 실패: {str(e)}"
                    logger.error(error_msg)
                    return {
                        **state,
                        "error": error_msg
                    }
                time.sleep(1)
                logger.warning(f"이미지 다운로드 재시도 {attempt + 1}/{max_retries}")
    
    # 이 코드는 실행되지 않아야 함 (위에서 모든 경우에 return 했으므로)
    logger.error("다운로드 이미지 함수 실행 중 예상치 못한 흐름 발생")
    return {
        **state,
        "error": "다운로드 이미지 함수 실행 중 예상치 못한 흐름 발생"
    }

def save_image(state: GraphState) -> None:
    """
    Save image to file system without modifying state
    This function is intended to be called as a parallel task

    Args:
        state (GraphState): The current graph state
    """
    logger.info("---SAVE IMAGE ---")
    try:
        save_path = "downloaded_images"
        os.makedirs(save_path, exist_ok=True)
        filename = f"{state['image_id']:03d}"
        base64_string = state['image_str']
        file_path = os.path.join(save_path, filename)

        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        image_data = base64.b64decode(base64_string)
        
        with open(file_path+".png", 'wb') as f:
            f.write(image_data)
            
        logger.info(f"이미지가 저장되었습니다: {file_path}.png")
    except Exception as e:
        # 이미지 저장 실패 시 에러 로깅만 하고 진행
        logger.error(f"이미지 저장 실패: {str(e)}")
    
    # 병렬 작업이므로 반환값 없음

def get_default_llm():
    """기본 LLM 인스턴스를 반환합니다."""
    return ChatGoogleGenerativeAI(model='gemini-2.0-flash-lite', temperature=0)
        
def describe_image(state: GraphState, llm: Optional[BaseChatModel] = None) -> GraphState:
    """
    Generate Description of image with improved prompt and error handling

    Args:
        state (GraphState): The current graph state
        llm (BaseChatModel, optional): 사용할 LLM 모델. 기본값은 None이며, None인 경우 기본 모델 사용

    Returns:
        GraphState: Updated state with image_description or error
    """
    logger.info("---GENERATE IMAGE DESCRIPTION---")
    
    # 현재 regenerate_count 가져오기 및 로그 출력
    current_count = state.get('regenerate_count', 0)
    logger.info(f"describe_image 호출 시 재생성 카운트: {current_count}")
    
    # llm이 None이면 기본 LLM 사용
    if llm is None:
        llm = get_default_llm()
    
    if not state.get('image_str'):
        return {
            **state,
            "error": "이미지 데이터가 없습니다",
            "regenerate_count": current_count
        }
        
    max_retries = 3
    img_str = state['image_str']
    prompt = hub.pull("hugdeundeun-room-describe-prompt")
    
    for attempt in range(max_retries):
        try:
            message = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": prompt.format()
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_str}"},
                    },
                ],
            )

            ans = llm.invoke([message])
            info = parser.parse(ans.content)
            
            # 새 카운트 계산 및 로깅
            new_count = current_count + 1
            logger.info(f"describe_image 완료 후 재생성 카운트 증가: {current_count} -> {new_count}")
            
            return {
                **state,
                "image_description": info,
                "error": None,
                "regenerate_count": new_count
            }
            
        except Exception as e:
            # 429 에러(리소스 초과) 처리 로직 추가
            if "429" in str(e) or "ResourceExhausted" in str(e) or "quota" in str(e):
                logger.warning(f"API 할당량 초과 감지됨: {str(e)}")
                logger.warning("60초 대기 후 재시도합니다...")
                time.sleep(60)  # 1분 대기
                
                # 마지막 시도가 아니면 계속 진행
                if attempt < max_retries - 1:
                    continue
            
            if attempt == max_retries - 1:
                error_msg = f"방구조 설명 생성 실패: {str(e)}"
                logger.error(error_msg)
                return {
                    **state,
                    "error": error_msg,
                    "regenerate_count": current_count  # regenerate_count 유지
                }
            time.sleep(1)
            logger.warning(f"방구조 설명 재시도 {attempt + 1}/{max_retries}")
            
def check_image_description(state: GraphState, llm: BaseChatModel = None) -> GraphState:
    """
    Check Description of image with improved error handling

    Args:
        state (GraphState): The current graph state
        llm (BaseChatModel, optional): 사용할 LLM 모델. 기본값은 None이며, None인 경우 기본 모델 사용

    Returns:
        GraphState: Updated state with description_accuracy or error
    """
    logger.info("---CHECK IMAGE DESCRIPTION---")
    
    # 현재 regenerate_count 가져오기 및 로그 출력
    current_count = state.get('regenerate_count', 0)
    logger.info(f"check_image_description 호출 시 재생성 카운트: {current_count}")
    
    # llm이 None이면 기본 LLM 사용
    if llm is None:
        llm = get_default_llm()
    
    if not state.get('image_description'):
        return {
            **state,
            "error": "방구조 설명이 없습니다",
            "regenerate_count": current_count  # regenerate_count 유지
        }
        
    max_retries = 3
    description = state['image_description']
    img_str = state['image_str']
    check_prompt_template = hub.pull("hugdeundeun-room-check-prompt")

    for attempt in range(max_retries):
        try:
            message = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": check_prompt_template.format(**{
                            "num_room":description.num_room,
                            "num_balcony":description.num_balcony,
                            "num_wc":description.num_wc,
                            "description":description.description})
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_str}"},
                    },
                ],
            )

            ans = llm.invoke([message])
            info = check_parser.parse(ans.content)
            
            # 검증 결과에 따른 처리
            if (info.num_room_accuracy and 
                info.num_balcony_accuracy and 
                info.num_wc_accuracy and 
                info.description_adequacy):
                logger.info("방구조 인식 검증 성공")
                return {
                    **state,
                    "description_accuracy": info,
                    "error": None,
                    "regenerate_count": current_count  # 성공 시 카운트 유지
                }
            else:
                # 실패 원인 로깅
                failed_items = []
                if not info.num_room_accuracy: failed_items.append("방 개수")
                if not info.num_balcony_accuracy: failed_items.append("발코니 수")
                if not info.num_wc_accuracy: failed_items.append("화장실 수") 
                if not info.description_adequacy: failed_items.append("방구조 설명")
                
                logger.warning(f"방구조 인식 실패 항목: {', '.join(failed_items)}")
                
                # 카운트 증가 및 로깅
                new_count = current_count + 1
                logger.info(f"검증 실패로 인한 재생성 카운트 증가: {current_count} -> {new_count}")
                
                return {
                    **state,
                    "description_accuracy": info,
                    "error": "방구조 인식 실패",
                    "regenerate_count": new_count  # 실패 시 카운트 증가
                }
            
        except Exception as e:
            # 429 에러(리소스 초과) 처리 로직 추가
            if "429" in str(e) or "ResourceExhausted" in str(e) or "quota" in str(e):
                logger.warning(f"API 할당량 초과 감지됨: {str(e)}")
                logger.warning("60초 대기 후 재시도합니다...")
                time.sleep(60)  # 1분 대기
                
                # 마지막 시도가 아니면 계속 진행
                if attempt < max_retries - 1:
                    continue
                    
            if attempt == max_retries - 1:
                error_msg = f"방구조 검증 실패: {str(e)}"
                logger.error(error_msg)
                return {
                    **state,
                    "error": error_msg,
                    "regenerate_count": current_count  # 예외 발생 시 카운트 유지
                }
            time.sleep(1)
            logger.warning(f"방구조 검증 재시도 {attempt + 1}/{max_retries}")