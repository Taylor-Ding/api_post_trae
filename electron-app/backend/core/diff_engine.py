# 尝试导入DeepDiff，如果失败则使用备用实现
try:
    from deepdiff import DeepDiff
except ImportError:
    # 备用实现：简单的字典差异比较
    class DeepDiff:
        def __init__(self, t1, t2, ignore_order=False):
            self.t1 = t1
            self.t2 = t2
            self.ignore_order = ignore_order
            self.result = self._compare(t1, t2)
        
        def _compare(self, obj1, obj2, path="root"):
            differences = {}
            
            if type(obj1) != type(obj2):
                differences[path] = {'old_value': obj1, 'new_value': obj2}
            elif isinstance(obj1, dict):
                all_keys = set(obj1.keys()) | set(obj2.keys())
                for key in all_keys:
                    new_path = f"{path}['{key}']"
                    if key not in obj1:
                        differences[new_path] = {'new_value': obj2[key]}
                    elif key not in obj2:
                        differences[new_path] = {'old_value': obj1[key]}
                    else:
                        sub_diff = self._compare(obj1[key], obj2[key], new_path)
                        differences.update(sub_diff)
            elif isinstance(obj1, list):
                if not self.ignore_order:
                    if obj1 != obj2:
                        differences[path] = {'old_value': obj1, 'new_value': obj2}
                else:
                    # 忽略顺序的简单比较
                    if sorted(obj1, key=str) != sorted(obj2, key=str):
                        differences[path] = {'old_value': obj1, 'new_value': obj2}
            elif obj1 != obj2:
                differences[path] = {'old_value': obj1, 'new_value': obj2}
            
            return differences
        
        def to_dict(self):
            return self.result
import re

class DiffEngine:
    def __init__(self, config):
        self.config = config
    
    def _should_ignore_field(self, field_name):
        """
        判断字段是否应该被忽略
        """
        ignore_patterns = self.config.get('ignore_fields', [])
        for pattern in ignore_patterns:
            if re.match(pattern, field_name):
                return True
        return False
    
    def _filter_dict(self, data):
        """
        过滤掉需要忽略的字段
        """
        if isinstance(data, dict):
            return {
                k: self._filter_dict(v) 
                for k, v in data.items() 
                if not self._should_ignore_field(k)
            }
        elif isinstance(data, list):
            return [self._filter_dict(item) for item in data]
        else:
            return data
    
    def compare(self, before_data, after_data):
        """
        比对前后数据的差异
        """
        # 过滤需要忽略的字段
        filtered_before = self._filter_dict(before_data)
        filtered_after = self._filter_dict(after_data)
        
        # 使用DeepDiff进行比对，忽略顺序差异
        diff = DeepDiff(
            filtered_before,
            filtered_after,
            ignore_order=True
        )
        
        return diff