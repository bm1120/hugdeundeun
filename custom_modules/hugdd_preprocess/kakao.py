import requests
import time
from typing import Dict, List, Optional, Tuple, Union

class kakaomap_rest_api:
    """
    카카오맵 REST API를 사용하기 위한 클래스
    
    이 클래스는 카카오맵 API를 사용하여 다음과 같은 기능을 제공합니다:
    - 주소를 좌표로 변환
    - 카테고리 기반 장소 검색
    - 좌표 기반 행정동/법정동 정보 조회
    - 좌표 기반 지번/도로명 주소 조회
    - 키워드 기반 장소 검색
    
    Attributes:
        api_token (str): 카카오맵 API 인증 토큰
        category_group_codes (Dict[str, str]): 카테고리 그룹 코드와 설명이 포함된 딕셔너리
    """
    
    def __init__(self, api_token: str) -> None:
        """
        Args:
            api_token (str): 카카오맵 API 인증 토큰
        """
        self.api_token = api_token
        self.category_group_codes = {
            'MT1': '대형마트',
            'CS2': '편의점',
            'PS3': '어린이집, 유치원',
            'SC4': '학교',
            'AC5': '학원',
            'PK6': '주차장',
            'OL7': '주유소, 충전소',
            'SW8': '지하철역',
            'BK9': '은행',
            'CT1': '문화시설',
            'AG2': '중개업소',
            'PO3': '공공기관',
            'AT4': '관광명소',
            'AD5': '숙박',
            'FD6': '음식점',
            'CE7': '카페',
            'HP8': '병원',
            'PM9': '약국'
        }
    
    def convert_address_to_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        """
        입력받은 주소를 WGS84 좌표계 좌표로 변환합니다.

        Args:
            address (str): 변환할 주소

        Returns:
            Optional[Tuple[float, float]]: (위도, 경도) 좌표값. 변환 실패 시 None 반환
        """
        url = 'https://dapi.kakao.com/v2/local/search/address.json?query=' + address
        header = {'Authorization': 'KakaoAK ' + self.api_token}
     
        r = requests.get(url, headers=header)
        
        if (r.status_code == 200) and len(r.json()["documents"])>0:
            lng = float(r.json()["documents"][0]["address"]['x'])
            lat = float(r.json()["documents"][0]["address"]['y'])
            return lat, lng
        return None
    
    def search_by_category(self, category_group_code: str, x: float, y: float, radius: int, size: int = 5) -> Optional[Dict]:
        """
        카테고리로 장소를 검색합니다.

        Args:
            category_group_code (str): 카테고리 그룹 코드
            x (float): 경도(longitude)
            y (float): 위도(latitude)
            radius (int): 검색 반경 (미터 단위)
            size (int, optional): 검색 결과 수 (최대 15건, 기본값: 5)

        Returns:
            Optional[Dict]: 검색 결과. 오류 발생 시 None 반환
        """
        url = "https://dapi.kakao.com/v2/local/search/category.json"
        
        headers = {
            "Authorization": f"KakaoAK {self.api_token}",
            "Content-Type": "application/json"
        }
        
        params = {
            "category_group_code": category_group_code,
            "radius": radius,
            "x": f"{x}",
            "y": f"{y}",
            "sort": "distance",
            "size": f"{size}"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"API 요청 중 오류 발생: {e}")
            return None

    def calculate_transit_time(self, origin_y: float, origin_x: float, dest_y: float, dest_x: float) -> Optional[Tuple[float, int]]:
        """
        출발지와 목적지 간의 이동 시간을 계산합니다.

        Args:
            origin_y (float): 출발지 위도
            origin_x (float): 출발지 경도
            dest_y (float): 목적지 위도
            dest_x (float): 목적지 경도

        Returns:
            Optional[Tuple[float, int]]: (이동 시간(분), 거리(미터)) 또는 None
        """
        time.sleep(0.2)
        url = "https://apis-navi.kakaomobility.com/v1/directions"
        headers = {"Authorization": f"KakaoAK {self.api_token}"}
        params = {
            "origin": f"{origin_y},{origin_x}",
            "destination": f"{dest_y},{dest_x}",
            "priority": "RECOMMEND",
            "car_fuel": "GASOLINE",
            "car_hipass": True,
            "alternatives": False,
            "road_details": False,
            "roadevent": 2
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                result = response.json()
                return result['routes'][0]['summary']['duration'] / 60, result['routes'][0]['summary']['distance']
            return None
        except:
            return None

    def get_category_info(self, category_code: Optional[str] = None) -> Dict[str, str]:
        """
        카테고리 코드 정보를 조회합니다.

        Args:
            category_code (Optional[str]): 카테고리 코드. None일 경우 전체 카테고리 정보 반환

        Returns:
            Dict[str, str]: 카테고리 코드와 설명이 포함된 딕셔너리
        """
        if category_code is None:
            return self.category_group_codes
        return {category_code: self.category_group_codes.get(category_code, '존재하지 않는 카테고리 코드입니다.')}

    def get_region_info(self, x: float, y: float, input_coord: str = 'WGS84', output_coord: str = 'WGS84') -> Optional[Dict]:
        """
        좌표를 기반으로 행정동/법정동 정보를 조회합니다.

        Args:
            x (float): X 좌표값 (경위도인 경우 경도)
            y (float): Y 좌표값 (경위도인 경우 위도)
            input_coord (str): 입력 좌표계 (WGS84, WCONGNAMUL, CONGNAMUL, WTM, TM)
            output_coord (str): 출력 좌표계 (WGS84, WCONGNAMUL, CONGNAMUL, WTM, TM)

        Returns:
            Optional[Dict]: 행정동/법정동 정보가 포함된 딕셔너리. 오류 발생 시 None 반환
        """
        url = "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json"
        
        headers = {
            "Authorization": f"KakaoAK {self.api_token}",
            "Content-Type": "application/json"
        }
        
        params = {
            "x": f"{x}",
            "y": f"{y}",
            "input_coord": input_coord,
            "output_coord": output_coord
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"API 요청 중 오류 발생: {e}")
            return None

    def get_address_info(self, x: float, y: float, input_coord: str = 'WGS84') -> Optional[Dict]:
        """
        좌표를 기반으로 지번 주소와 도로명 주소 정보를 조회합니다.

        Args:
            x (float): X 좌표값 (경위도인 경우 경도)
            y (float): Y 좌표값 (경위도인 경우 위도)
            input_coord (str): 입력 좌표계 (WGS84, WCONGNAMUL, CONGNAMUL, WTM, TM)

        Returns:
            Optional[Dict]: 지번 주소와 도로명 주소 정보가 포함된 딕셔너리. 오류 발생 시 None 반환
        """
        url = "https://dapi.kakao.com/v2/local/geo/coord2address.json"
        
        headers = {
            "Authorization": f"KakaoAK {self.api_token}",
            "Content-Type": "application/json"
        }
        
        params = {
            "x": f"{x}",
            "y": f"{y}",
            "input_coord": input_coord
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"API 요청 중 오류 발생: {e}")
            return None

    def search_places(self, query: str, x: Optional[float] = None, y: Optional[float] = None, 
                     radius: Optional[int] = None, rect: Optional[str] = None, 
                     page: int = 1, size: int = 15, sort: str = 'accuracy', 
                     category_group_code: Optional[str] = None) -> Optional[Dict]:
        """
        키워드로 장소를 검색합니다.

        Args:
            query (str): 검색을 원하는 질의어
            x (Optional[float]): 중심 좌표의 X 혹은 경도(longitude) 값
            y (Optional[float]): 중심 좌표의 Y 혹은 위도(latitude) 값
            radius (Optional[int]): 중심 좌표부터의 반경거리 (미터 단위, 최소: 0, 최대: 20000)
            rect (Optional[str]): 사각형의 지정 범위 내 제한 검색을 위한 좌표
            page (int): 결과 페이지 번호 (최소: 1, 최대: 45, 기본값: 1)
            size (int): 한 페이지에 보여질 문서의 개수 (최소: 1, 최대: 15, 기본값: 15)
            sort (str): 결과 정렬 순서 (distance 또는 accuracy, 기본값: accuracy)
            category_group_code (Optional[str]): 카테고리 그룹 코드

        Returns:
            Optional[Dict]: 검색 결과가 포함된 딕셔너리. 오류 발생 시 None 반환
        """
        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        
        headers = {
            "Authorization": f"KakaoAK {self.api_token}",
            "Content-Type": "application/json"
        }
        
        params = {
            "query": query,
            "page": page,
            "size": size,
            "sort": sort
        }
        
        if x is not None and y is not None:
            params["x"] = f"{x}"
            params["y"] = f"{y}"
            
        if radius is not None:
            params["radius"] = radius
            
        if rect is not None:
            params["rect"] = rect
            
        if category_group_code is not None:
            params["category_group_code"] = category_group_code
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"API 요청 중 오류 발생: {e}")
            return None

    def print_methods_info_en(self) -> None:
        """
        Prints information about all available methods in English.
        """
        methods_info = {
            'convert_address_to_coordinates': 'Converts an address to WGS84 coordinates',
            'search_by_category': 'Searches for places by category within a specified radius',
            'calculate_transit_time': 'Calculates transit time and distance between two points',
            'get_category_info': 'Retrieves category code information',
            'get_region_info': 'Retrieves administrative/legal district information based on coordinates',
            'get_address_info': 'Retrieves land lot and road address information based on coordinates',
            'search_places': 'Searches for places by keyword with various filtering options'
        }
        
        print("\nAvailable Methods:")
        print("-" * 50)
        for method, description in methods_info.items():
            print(f"{method}:")
            print(f"  {description}")
            print("-" * 50)

    def print_methods_info_ko(self) -> None:
        """
        모든 사용 가능한 메서드의 정보를 한국어로 출력합니다.
        """
        methods_info = {
            'convert_address_to_coordinates': '주소를 WGS84 좌표로 변환합니다',
            'search_by_category': '지정된 반경 내에서 카테고리별 장소를 검색합니다',
            'calculate_transit_time': '두 지점 간의 이동 시간과 거리를 계산합니다',
            'get_category_info': '카테고리 코드 정보를 조회합니다',
            'get_region_info': '좌표를 기반으로 행정동/법정동 정보를 조회합니다',
            'get_address_info': '좌표를 기반으로 지번/도로명 주소 정보를 조회합니다',
            'search_places': '키워드로 장소를 검색하며 다양한 필터링 옵션을 제공합니다',
            'get_category_counts': '주어진 좌표 주변의 카테고리별 장소 수를 반환합니다'
        }
        
        print("\n사용 가능한 메서드:")
        print("-" * 50)
        for method, description in methods_info.items():
            print(f"{method}:")
            print(f"  {description}")
            print("-" * 50)

    def get_category_counts(self, x: float, y: float) -> Dict[str, int]:
        """
        주어진 좌표 주변의 카테고리별 장소 수를 반환합니다.
        각 카테고리별로 다른 검색 반경을 사용합니다.

        Args:
            x (float): 경도(longitude)
            y (float): 위도(latitude)

        Returns:
            Dict[str, int]: 카테고리 코드와 해당 카테고리의 장소 수가 포함된 딕셔너리
        """
        # 카테고리 코드와 기본 거리 설정
        category_distances = {
            'MT1': 1000,  # 대형마트
            'CS2': 300,   # 편의점
            'PS3': 500,   # 어린이집, 유치원
            'SC4': 500,   # 학교
            'AC5': 500,   # 학원
            'PK6': 500,   # 주차장
            'OL7': 1000,  # 주유소, 충전소
            'SW8': 1000,  # 지하철역
            'BK9': 500,   # 은행
            'CT1': 500,   # 문화시설
            'AG2': 500,   # 중개업소
            'PO3': 500,   # 공공기관
            'AT4': 500,   # 관광명소
            'AD5': 500,   # 숙박
            'FD6': 500,   # 음식점
            'CE7': 500,   # 카페
            'HP8': 500,   # 병원
            'PM9': 500    # 약국
        }
        
        category_counts = {}
        
        for category_code, distance in category_distances.items():
            try:
                result = self.search_by_category(category_code, x, y, distance, size=15)
                if result and 'documents' in result:
                    category_counts[category_code] = len(result['documents'])
                else:
                    category_counts[category_code] = 0
            except Exception as e:
                print(f"카테고리 {category_code} 검색 중 오류 발생: {e}")
                category_counts[category_code] = 0
        
        return category_counts
            