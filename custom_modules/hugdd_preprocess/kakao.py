import requests
import time
class kakaomap_rest_api:
    def __init__(self, api_token):
        self.api_token = api_token
    
    def convert_address_to_coordinates(self, address):
        """
        입력받은 주소를 WGS84 좌표계 좌표로 변환(카카오맵api)
        """
    
        url = 'https://dapi.kakao.com/v2/local/search/address.json?query=' + address
        
        header = {'Authorization': 'KakaoAK ' + self.api_token}
     
        r = requests.get(url, headers=header)
        
        if (r.status_code == 200) and len(r.json()["documents"])>0:
            lng = float(r.json()["documents"][0]["address"]['x'])
            lat = float(r.json()["documents"][0]["address"]['y'])
        else:
            return None
        return lat, lng

    
    def search_by_category(self, category_group_code,  x, y, radius):
        """
        카테고리로 장소를 검색하는 함수
        
        Args:
            api_key (str): 카카오 개발자 REST API 키
            category_group_code (str): 카테고리 그룹 코드
            x(float): 경도(longitude)
            y(float): 위도(latitude)
            radius (int): 검색 반경 (미터 단위)
            
        
        Returns:
            dict: 검색 결과
        """
        url = "https://dapi.kakao.com/v2/local/search/category.json"
        
        headers = {
            "Authorization": f"KakaoAK {self.api_token}",
            "Content-Type": "application/json"
        }
        
        params = {
            "category_group_code": category_group_code,
            "radius": radius,
            "x":f"{x}",
            "y":f"{y}",
            "sort":"distance",
            "size":"5"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"API 요청 중 오류 발생: {e}")
            return None

    def calculate_transit_time(self, origin_y, origin_x, dest_y, dest_x):
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
            "roadevent":2
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                result = response.json()
                return result['routes'][0]['summary']['duration'] / 60, result['routes'][0]['summary']['distance']
            return None
        except:
            return None
            