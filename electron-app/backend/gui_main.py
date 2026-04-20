import os
import sys
import json
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from core.db_router import DBRouter
from core.api_caller import APICaller
from core.diff_engine import DiffEngine
from utils.config_manager import ConfigManager
from utils.log_manager import LogManager
from utils.message_parser import MessageParser
from utils.table_query_config import QueryConditionExtractor

class DataCheckerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("数据一致性自动化核对工具")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)

        # 加载配置
        config_file = os.path.join(os.path.dirname(__file__), "config", "config.json")
        self.config_manager = ConfigManager(config_file)
        self.config = self.config_manager.config
        
        # 初始化日志
        self.log_manager = LogManager()
        self.logger = self.log_manager.logger
        
        # 初始化各模块
        self.db_router = DBRouter(self.config)
        self.api_caller = APICaller(self.config)
        self.diff_engine = DiffEngine(self.config)

        # 存储结果
        self.results = []

        self.create_widgets()

    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左侧面板 - 配置区
        left_panel = ttk.Frame(main_frame, width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))

        # 请求地址
        ttk.Label(left_panel, text="请求地址", font=('Arial', 11, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        self.url_entry = ttk.Entry(left_panel, width=50)
        self.url_entry.pack(fill=tk.X, pady=(0, 10))
        self.url_entry.insert(0, "http://localhost:8080/api/business")

        # 请求报文
        ttk.Label(left_panel, text="请求报文", font=('Arial', 11, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        self.request_text = scrolledtext.ScrolledText(left_panel, height=20, width=60)
        self.request_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        # 默认示例报文
        default_json = {
            "txHeader": {
                "mainMapElemntInfo": "056217991000103398751"
            },
            "txBody": {
                "txComn7": {
                    "custNo": "00000194476241"
                },
                "txEntity": {
                    "mediumNo": "6217991000103398751"
                }
            }
        }
        self.request_text.insert(tk.END, json.dumps(default_json, indent=2, ensure_ascii=False))

        # 检查表选择
        ttk.Label(left_panel, text="检查表", font=('Arial', 11, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        self.table_combobox = ttk.Combobox(left_panel, values=["tb_dpmst_medium"], state="readonly")
        self.table_combobox.current(0)
        self.table_combobox.pack(fill=tk.X, pady=(0, 10))

        # 执行按钮
        self.execute_btn = ttk.Button(left_panel, text="执行核对", command=self.execute_check)
        self.execute_btn.pack(fill=tk.X, pady=10)

        # 右侧面板 - 结果区
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 标签页
        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 日志标签页
        self.log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.log_frame, text="📜 执行日志")
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=30, width=80, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 清空日志按钮
        ttk.Button(self.log_frame, text="清空日志", command=self.clear_log).pack(side=tk.RIGHT, padx=5, pady=5)

        # 结果标签页
        self.result_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.result_frame, text="📊 断言结果")
        self.result_text = scrolledtext.ScrolledText(self.result_frame, height=30, width=80, state=tk.DISABLED)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 响应标签页
        self.response_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.response_frame, text="📨 响应报文")
        self.response_text = scrolledtext.ScrolledText(self.response_frame, height=30, width=80, state=tk.DISABLED)
        self.response_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def add_log(self, message, level="INFO"):
        """添加日志"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = os.popen('date "+%Y-%m-%d %H:%M:%S"').read().strip()
        color_tags = {
            "INFO": "blue",
            "ERROR": "red",
            "WARN": "orange",
            "SQL": "purple"
        }
        tag = level
        if tag not in color_tags:
            tag = "INFO"
        self.log_text.insert(tk.END, f"[{timestamp}] [{level}] {message}\n", tag)
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)

    def clear_log(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def clear_result(self):
        """清空结果"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)
        self.response_text.config(state=tk.NORMAL)
        self.response_text.delete(1.0, tk.END)
        self.response_text.config(state=tk.DISABLED)

    def execute_check(self):
        """执行数据一致性检查"""
        self.clear_log()
        self.clear_result()
        self.results = []

        try:
            # 获取请求地址和报文
            api_url = self.url_entry.get().strip()
            request_data_str = self.request_text.get(1.0, tk.END).strip()
            
            if not api_url:
                messagebox.showerror("错误", "请输入请求地址")
                return
            
            if not request_data_str:
                messagebox.showerror("错误", "请输入请求报文")
                return

            # 解析JSON
            try:
                request_data = json.loads(request_data_str)
            except json.JSONDecodeError as e:
                messagebox.showerror("错误", f"JSON格式错误: {str(e)}")
                return

            # 解析 mainMapElemntInfo
            self.add_log("解析mainMapElemntInfo字段...")
            main_map = request_data.get("txHeader", {}).get("mainMapElemntInfo", "")
            
            if main_map:
                routing_key = MessageParser.parse_main_map_element(main_map)
                self.add_log(f"mainMapElemntInfo字段值: {main_map}")
                self.add_log(f"解析成功: 类型={routing_key['type']}, 值={routing_key['value']}")
            else:
                self.add_log("WARN: 未找到mainMapElemntInfo字段")
                routing_key = None

            # 获取检查表
            table_name = self.table_combobox.get()

            # 提取查询条件
            self.add_log(f"开始提取表 {table_name} 的查询条件...")
            conditions = QueryConditionExtractor.extract_conditions(request_data, table_name, routing_key, self.add_log)
            self.add_log(f"最终查询条件: {json.dumps(conditions, ensure_ascii=False)}")

            # 查询执行前数据
            self.add_log("开始查询执行前的数据...")
            primary_key = conditions.get("medium_no") or conditions.get("cust_no")
            if primary_key:
                before_data, db_name, table_full_name = self.db_router.query_data(
                    primary_key, 
                    table_name, 
                    f"medium_no = '{conditions.get('medium_no', '')}'" if conditions.get('medium_no') else f"cust_no = '{conditions.get('cust_no', '')}'"
                )
                self.add_log(f"路由到: {db_name}.{table_full_name}")
                self.add_log(f"SQL查询: SELECT * FROM \"{table_full_name}\" WHERE {list(conditions.keys())[0]} = '{list(conditions.values())[0]}'")
                self.add_log(f"查询到 {len(before_data)} 条记录")
            else:
                self.add_log("ERROR: 无法获取查询条件")
                return

            # 调用API
            self.add_log(f"开始调用API: {api_url}")
            api_response = self.api_caller.call_api(api_url, data=request_data)
            self.add_log("API调用成功")
            
            # 显示响应
            self.response_text.config(state=tk.NORMAL)
            self.response_text.insert(tk.END, json.dumps(api_response, indent=2, ensure_ascii=False))
            self.response_text.config(state=tk.DISABLED)

            # 查询执行后数据
            self.add_log("开始查询执行后的数据...")
            after_data, _, _ = self.db_router.query_data(
                primary_key, 
                table_name, 
                f"medium_no = '{conditions.get('medium_no', '')}'" if conditions.get('medium_no') else f"cust_no = '{conditions.get('cust_no', '')}'"
            )
            self.add_log(f"查询到 {len(after_data)} 条记录")

            # 比对数据
            self.add_log("开始比对数据差异...")
            diff = self.diff_engine.compare(before_data, after_data)

            # 显示结果
            self.result_text.config(state=tk.NORMAL)
            if diff:
                self.result_text.insert(tk.END, "❌ 数据一致性检查失败！\n\n", "error")
                self.result_text.insert(tk.END, f"差异详情:\n{json.dumps(diff, indent=2, ensure_ascii=False)}", "diff")
                self.add_log("ERROR: 数据不一致！")
            else:
                self.result_text.insert(tk.END, "✅ 数据一致性检查通过！\n\n", "success")
                self.result_text.insert(tk.END, "执行前后数据完全一致，无差异。")
                self.add_log("数据一致，无差异")
            self.result_text.config(state=tk.DISABLED)

            # 切换到结果标签页
            self.notebook.select(1)

        except Exception as e:
            self.add_log(f"ERROR: {str(e)}")
            messagebox.showerror("执行失败", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = DataCheckerGUI(root)
    root.mainloop()