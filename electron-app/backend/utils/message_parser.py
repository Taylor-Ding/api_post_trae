class MessageParser:
    """
    解析请求报文，提取关键字段
    """

    @staticmethod
    def parse_main_map_element(request_data, add_log=None):
        """
        解析txHeader中的mainMapElemntInfo字段

        返回值类型：
        - 'cust_no': 客户号 (04开头)
        - 'medium_no': 介质号 (05开头)
        - None: 解析失败
        """
        log_func = add_log if add_log else (lambda x: None)

        if not request_data:
            log_func("错误: 请求报文为空")
            raise ValueError("请求报文不能为空")

        if not isinstance(request_data, dict):
            log_func("错误: 请求报文格式错误，必须是JSON对象")
            raise ValueError("请求报文格式错误，必须是JSON对象")

        tx_header = request_data.get('txHeader')
        if not tx_header:
            log_func("错误: 请求报文中未找到txHeader字段")
            raise ValueError("请求报文中未找到txHeader字段")

        main_map_element = tx_header.get('mainMapElemntInfo')
        log_func(f"解析mainMapElemntInfo字段: {main_map_element}")

        if main_map_element is None or main_map_element == "":
            log_func("错误: mainMapElemntInfo字段为null或空字符串")
            raise ValueError("mainMapElemntInfo字段为null或空字符串")

        if not isinstance(main_map_element, str):
            main_map_element = str(main_map_element)
            log_func(f"警告: mainMapElemntInfo字段不是字符串，已自动转换: {main_map_element}")

        if main_map_element.startswith("04"):
            cust_no = main_map_element[2:]
            if not cust_no:
                log_func("错误: mainMapElemntInfo字段04开头但后续没有客户号")
                raise ValueError("mainMapElemntInfo字段04开头但后续没有客户号")
            log_func(f"成功解析客户号: {cust_no}")
            return {'type': 'cust_no', 'value': cust_no}

        elif main_map_element.startswith("05"):
            medium_no = main_map_element[2:]
            if not medium_no:
                log_func("错误: mainMapElemntInfo字段05开头但后续没有介质号")
                raise ValueError("mainMapElemntInfo字段05开头但后续没有介质号")
            log_func(f"成功解析介质号: {medium_no}")
            return {'type': 'medium_no', 'value': medium_no}

        else:
            log_func(f"错误: mainMapElemntInfo字段格式错误，必须以04或05开头，当前值: {main_map_element}")
            raise ValueError(f"mainMapElemntInfo字段格式错误，必须以04或05开头，当前值: {main_map_element}")

    @staticmethod
    def get_cust_no(request_data, add_log=None):
        """
        从请求报文中获取客户号
        """
        result = MessageParser.parse_main_map_element(request_data, add_log)
        if result and result['type'] == 'cust_no':
            return result['value']
        return None

    @staticmethod
    def get_medium_no(request_data, add_log=None):
        """
        从请求报文中获取介质号
        """
        result = MessageParser.parse_main_map_element(request_data, add_log)
        if result and result['type'] == 'medium_no':
            return result['value']
        return None