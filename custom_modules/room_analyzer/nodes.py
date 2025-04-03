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

    Args:
        state (GraphState): The current graph state

    Returns:
        GraphState: Updated state with image_str or error
    """
    logger.info("---DOWNLOAD IMAGE ---")
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            response = requests.get(state['image_url'], timeout=30)
            response.raise_for_status()
            
            # 이미지 데이터가 PNG인지 확인
            if not response.content.startswith(b'\x89PNG\r\n\x1a\n'):
                raise ValueError("이미지가 PNG 형식이 아닙니다")
            
            # 이미지를 base64로 직접 인코딩
            img_str = base64.b64encode(response.content).decode('utf-8')
            
            return {
                **state,
                "image_str": img_str,
                "error": None
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


        
def describe_image(state: GraphState, llm:BaseChatModel = ChatGoogleGenerativeAI(model='gemini-2.0-flash-lite', temperature=0)) -> GraphState:
    """
    Generate Description of image with improved prompt and error handling

    Args:
        state (GraphState): The current graph state

    Returns:
        GraphState: Updated state with image_description or error
    """
    logger.info("---GENERATE IMAGE DESCRIPTION---")
    
    current_count = state.get('regenerate_count', 0)

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
            
            return {
                **state,
                "image_description": info,
                "error": None,
                "regenerate_count": current_count+1
            }
            
        except Exception as e:
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
            
def check_image_description(state: GraphState, llm:BaseChatModel = ChatGoogleGenerativeAI(model='gemini-2.0-flash-lite', temperature=0)) -> GraphState:
    """
    Check Description of image with improved error handling

    Args:
        state (GraphState): The current graph state

    Returns:
        GraphState: Updated state with description_accuracy or error
    """
    logger.info("---CHECK IMAGE DESCRIPTION---")
    
    if not state.get('image_description'):
        return {
            **state,
            "error": "방구조 설명이 없습니다"
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
            
            return {
                **state,
                "description_accuracy": info,
                "error": None
            }
            
        except Exception as e:
            if attempt == max_retries - 1:
                error_msg = f"방구조 검증 실패: {str(e)}"
                logger.error(error_msg)
                return {
                    **state,
                    "error": error_msg
                }
            time.sleep(1)
            logger.warning(f"방구조 검증 재시도 {attempt + 1}/{max_retries}")