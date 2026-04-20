class TableQueryConfig:
    """
    表查询条件配置
    定义每个表的查询条件从报文中哪个路径提取
    """

    @staticmethod
    def get_default_config():
        """
        获取默认的表查询条件配置
        """
        return {
            "tb_dpmst_medium": {
                "primary_key": "medium_no",
                "condition_field": "medium_no",
                "source_paths": {
                    "medium_no": "txBody.txEntity.mediumNo",
                    "cust_no": "txBody.txComn7.custNo"
                },
                "description": "介质信息表，可通过mediumNo或custNo查询"
            }
        }

    @staticmethod
    def get_table_config(table_name):
        """
        获取指定表的查询条件配置
        """
        config = TableQueryConfig.get_default_config()
        return config.get(table_name)

    @staticmethod
    def get_all_tables():
        """
        获取所有已配置的表
        """
        config = TableQueryConfig.get_default_config()
        return list(config.keys())


class QueryConditionExtractor:
    """
    从报文中提取查询条件
    """

    @staticmethod
    def extract_value(data, path):
        """
        根据路径从报文中提取值
        例如: "txBody.txEntity.mediumNo"
        """
        if not data or not path:
            return None

        keys = path.split('.')
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current

    @staticmethod
    def extract_conditions(request_data, table_name, routing_key=None, add_log=None):
        """
        从报文中提取指定表的查询条件

        参数:
            request_data: 请求报文数据
            table_name: 表名
            routing_key: 从mainMapElemntInfo解析出的路由键 {'type': 'cust_no'|'medium_no', 'value': 'xxx'}
            add_log: 日志记录函数

        返回:
            dict: 查询条件，例如 {'medium_no': '6217991000103398751'}
        """
        log = add_log if add_log else (lambda x: None)

        config = TableQueryConfig.get_table_config(table_name)
        if not config:
            log(f"警告: 表 {table_name} 没有配置查询条件")
            return {}

        log(f"提取表 {table_name} 的查询条件...")
        log(f"  - 主键字段: {config['primary_key']}")
        log(f"  - 条件字段: {config['condition_field']}")

        conditions = {}

        # 根据路由键类型和表配置确定查询条件
        if routing_key:
            log(f"  - 路由键类型: {routing_key['type']}, 值: {routing_key['value']}")

            if routing_key['type'] == 'medium_no':
                # 如果路由键是mediumNo，直接使用
                conditions[config['condition_field']] = routing_key['value']
                log(f"  - 使用路由键中的mediumNo: {routing_key['value']}")

            elif routing_key['type'] == 'cust_no':
                # 如果路由键是custNo，需要根据报文中的信息查询对应的mediumNo
                log(f"  - 路由键为custNo，需要从报文中提取mediumNo进行关联查询")

                # 尝试从报文中提取custNo
                cust_no_source = config['source_paths'].get('cust_no')
                if cust_no_source:
                    cust_no_from_request = QueryConditionExtractor.extract_value(request_data, cust_no_source)
                    if cust_no_from_request:
                        log(f"  - 从报文提取custNo: {cust_no_from_request}")

                        # 检查custNo是否与路由键中的custNo一致
                        if str(cust_no_from_request) == str(routing_key['value']):
                            log(f"  - custNo匹配，继续提取mediumNo")

                            # 尝试从报文中提取mediumNo
                            medium_no_source = config['source_paths'].get('medium_no')
                            if medium_no_source:
                                medium_no = QueryConditionExtractor.extract_value(request_data, medium_no_source)
                                if medium_no:
                                    conditions[config['condition_field']] = medium_no
                                    log(f"  - 从报文提取mediumNo: {medium_no}")
                                else:
                                    log(f"  - 警告: 无法从报文中提取mediumNo，custNo查询需要后续数据库关联")
                            else:
                                log(f"  - 警告: 表配置中没有medium_no字段，无法进行关联查询")
                        else:
                            log(f"  - 错误: 报文中的custNo与路由键不匹配")
                            raise ValueError(f"报文中的custNo ({cust_no_from_request}) 与路由键中的custNo ({routing_key['value']}) 不匹配")
                    else:
                        log(f"  - 错误: 无法从报文中提取custNo")
                        raise ValueError("无法从报文中提取custNo")

        else:
            # 没有路由键，尝试直接从报文中提取所有可能的条件
            log(f"  - 没有路由键，直接从报文中提取条件字段")
            for field_name, source_path in config['source_paths'].items():
                value = QueryConditionExtractor.extract_value(request_data, source_path)
                if value:
                    log(f"  - 提取到 {field_name}: {value}")
                    # 对于tb_dpmst_medium，我们主要关心medium_no
                    if field_name == config['condition_field']:
                        conditions[config['condition_field']] = value

        if not conditions:
            log(f"  - 错误: 无法提取到有效的查询条件")
            raise ValueError(f"无法为表 {table_name} 提取查询条件")

        log(f"  - 最终查询条件: {conditions}")
        return conditions