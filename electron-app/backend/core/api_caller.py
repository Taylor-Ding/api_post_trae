import requests
import json

class APICaller:
    def __init__(self, config):
        self.config = config
    
    def call_api(self, url, method='POST', headers=None, data=None):
        """
        调用HTTP接口
        确保空值在JSON序列化时被完整保留
        """
        if headers is None:
            headers = {
                'Content-Type': 'application/json'
            }
        
        try:
            # 使用json参数自动序列化，确保None被转换为null
            if method.upper() == 'POST':
                response = requests.post(
                    url,
                    headers=headers,
                    json=data,  # 使用json参数而不是data，确保None被正确处理
                    timeout=self.config.get('api_timeout', 30)
                )
            elif method.upper() == 'GET':
                response = requests.get(
                    url,
                    headers=headers,
                    params=data,
                    timeout=self.config.get('api_timeout', 30)
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()  # 抛出HTTP错误
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"API call failed: {str(e)}")