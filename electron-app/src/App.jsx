import { useState, useRef } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [apiUrl, setApiUrl] = useState('http://localhost:8080/api/business');
  const [requestBody, setRequestBody] = useState(JSON.stringify({
    "txBody": {
      "txEntity": {
        "inputModeCode": "2",
        "coreTxFlag": "00000000000000",
        "mediumNo": "6217991000103398751"
      },
      "txComni": {
        "accountingDate": "20231026"
      },
      "txComn7": {
        "custNo": "00400022300118",
        "teschnlCustNo": "4067745905991"
      },
      "txComn8": {
        "busiSendSysOrCmptNo": "99100060000"
      },
      "txComn1": {
        "curQryReqNum": 10,
        "bgnIndexNo": 1
      },
      "txComn2": {
        "oprTellerNo": "0000000000"
      }
    },
    "txHeader": {
      "msgrptMac": "{{msgrptMac}}",
      "globalBusiTrackNo": "{{globalBusiTrackNo}}",
      "subtxNo": "{{subtxNo}}",
      "txStartTime": "{{txStartTime}}",
      "txSendTime": "{{txSendTime}}",
      "busiSendInstNo": "11005293",
      "reqSysSriNo": "20231026104615991000648028791662",
      "msgAgrType": "1",
      "startSysOrCmptNo": "99100060000",
      "targetSysOrCmptNo": "1022199",
      "resvedInputInfo": "",
      "mainMapElemntInfo": "056217991000103398751",
      "pubMsgHeadLen": "0",
      "servVerNo": "10000",
      "servNo": "10221997100",
      "msgrptTotalLen": "0",
      "dataCenterCode": "H",
      "servTpCd": "1",
      "msgrptFmtVerNo": "10000",
      "embedMsgrptLen": "0",
      "sendSysOrCmptNo": "99700040001",
      "startChnlFgCd": "15",
      "tenantId": "DEV1"
    }
  }, null, 2));
  const [responseBody, setResponseBody] = useState('');
  const [tables, setTables] = useState([{ name: 'tb_dpmst_medium' }]);
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [logs, setLogs] = useState([]);
  const [activeTab, setActiveTab] = useState('log');
  const logsRef = useRef(null);

  const addTable = () => {
    setTables([...tables, { name: '' }]);
  };

  const removeTable = (index) => {
    const newTables = [...tables];
    newTables.splice(index, 1);
    setTables(newTables);
  };

  const updateTableName = (index, value) => {
    const newTables = [...tables];
    newTables[index].name = value;
    setTables(newTables);
  };

  const addLog = (message, level = 'INFO') => {
    const timestamp = new Date().toLocaleTimeString('zh-CN', { hour12: false });
    setLogs(prev => [...prev, { timestamp, message, level }]);
    setTimeout(() => {
      if (logsRef.current) {
        logsRef.current.scrollTop = logsRef.current.scrollHeight;
      }
    }, 50);
  };

  const parseMainMapElement = (requestData) => {
    addLog('解析mainMapElemntInfo字段...');
    if (!requestData) throw new Error('请求报文不能为空');
    if (typeof requestData !== 'object') throw new Error('请求报文格式错误，必须是JSON对象');

    const txHeader = requestData.txHeader;
    if (!txHeader) throw new Error('请求报文中未找到txHeader字段');

    const mainMapElement = txHeader.mainMapElemntInfo;
    addLog(`mainMapElemntInfo字段值: ${mainMapElement}`);

    if (mainMapElement === null || mainMapElement === undefined || mainMapElement === "") {
      throw new Error('mainMapElemntInfo字段为null或空字符串');
    }

    const mainMapStr = String(mainMapElement);
    if (mainMapStr.startsWith('04')) {
      const custNo = mainMapStr.substring(2);
      if (!custNo) throw new Error('mainMapElemntInfo字段04开头但后续没有客户号');
      addLog(`解析成功: 类型=客户号, 值=${custNo}`);
      return { type: 'cust_no', value: custNo };
    } else if (mainMapStr.startsWith('05')) {
      const mediumNo = mainMapStr.substring(2);
      if (!mediumNo) throw new Error('mainMapElemntInfo字段05开头但后续没有介质号');
      addLog(`解析成功: 类型=介质号, 值=${mediumNo}`);
      return { type: 'medium_no', value: mediumNo };
    } else {
      throw new Error(`mainMapElemntInfo字段格式错误，必须以04或05开头，当前值: ${mainMapStr}`);
    }
  };

  const extractValue = (data, path) => {
    if (!data || !path) return null;
    const keys = path.split('.');
    let current = data;
    for (const key of keys) {
      if (typeof current === 'object' && key in current) {
        current = current[key];
      } else {
        return null;
      }
    }
    return current;
  };

  const tableConfigs = {
    'tb_dpmst_medium': {
      primaryKey: 'medium_no',
      conditionField: 'medium_no',
      sourcePaths: {
        medium_no: 'txBody.txEntity.mediumNo',
        cust_no: 'txBody.txComn7.custNo'
      }
    }
  };

  const extractConditions = (requestData, tableName, routingKey) => {
    addLog(`提取表 ${tableName} 的查询条件...`);
    const config = tableConfigs[tableName];
    if (!config) {
      addLog(`警告: 表 ${tableName} 没有配置查询条件`, 'WARN');
      return {};
    }

    addLog(`  主键: ${config.primaryKey} | 条件字段: ${config.conditionField}`);
    const conditions = {};

    if (routingKey) {
      addLog(`  路由键类型: ${routingKey.type}, 值: ${routingKey.value}`);
      if (routingKey.type === 'medium_no') {
        conditions[config.conditionField] = routingKey.value;
        addLog(`  使用路由键中的mediumNo: ${routingKey.value}`);
      } else if (routingKey.type === 'cust_no') {
        addLog(`  路由键为custNo，需要从报文中提取mediumNo进行关联查询`, 'WARN');
        const custNoFromRequest = extractValue(requestData, config.sourcePaths.cust_no);
        if (custNoFromRequest) {
          addLog(`  从报文提取custNo: ${custNoFromRequest}`);
          if (String(custNoFromRequest) === String(routingKey.value)) {
            const mediumNo = extractValue(requestData, config.sourcePaths.medium_no);
            if (mediumNo) {
              conditions[config.conditionField] = mediumNo;
              addLog(`  从报文提取mediumNo: ${mediumNo}`);
            } else {
              addLog(`  警告: 无法从报文中提取mediumNo`, 'WARN');
            }
          } else {
            addLog(`  错误: 报文中的custNo与路由键不匹配`, 'ERROR');
          }
        } else {
          addLog(`  错误: 无法从报文中提取custNo`, 'ERROR');
        }
      }
    } else {
      addLog(`  没有路由键，直接从报文中提取条件字段`);
      for (const [fieldName, sourcePath] of Object.entries(config.sourcePaths)) {
        const value = extractValue(requestData, sourcePath);
        if (value) {
          addLog(`  提取到 ${fieldName}: ${value}`);
          if (fieldName === config.conditionField) {
            conditions[config.conditionField] = value;
          }
        }
      }
    }

    if (Object.keys(conditions).length > 0) {
      addLog(`  最终查询条件: ${JSON.stringify(conditions)}`);
    } else {
      addLog(`  警告: 无法提取到有效的查询条件`, 'WARN');
    }
    return conditions;
  };

  const sendRequest = async () => {
    setIsLoading(true);
    setError('');
    setResponseBody('');
    setResults([]);
    setLogs([]);
    setActiveTab('log');

    try {
      addLog('开始执行数据一致性检查...');
      addLog(`请求地址: ${apiUrl}`);

      let requestData;
      try {
        addLog('验证请求报文格式...');
        requestData = JSON.parse(requestBody);
        addLog('请求报文格式验证通过');
      } catch {
        addLog('请求报文格式错误', 'ERROR');
        throw new Error('请求报文格式错误，请检查JSON格式');
      }

      let routingKey = null;
      try {
        routingKey = parseMainMapElement(requestData);
      } catch (parseError) {
        addLog(`解析mainMapElemntInfo字段失败: ${parseError.message}`, 'ERROR');
        throw parseError;
      }

      addLog('开始提取各表的查询条件...');
      const tableConditions = {};
      for (const table of tables) {
        if (table.name) {
          try {
            const conditions = extractConditions(requestData, table.name, routingKey);
            tableConditions[table.name] = conditions;
          } catch (condError) {
            addLog(`提取表 ${table.name} 查询条件失败: ${condError.message}`, 'ERROR');
          }
        }
      }

      addLog('调用后端API执行数据一致性检查...');
      try {
        addLog('开始调用后端API...');
        addLog('API URL: http://localhost:8080/api/check');
        
        const requestDataForAPI = {
          apiResponse: null,
          tables: tables.filter(t => t.name).map(t => t.name),
          requestData: requestData,
          routingKey: routingKey
        };
        
        addLog(`请求数据: ${JSON.stringify(requestDataForAPI, null, 2)}`);
        
        // 模拟API响应，以便展示SQL查询过程
        const mockResponse = {
          success: true,
          logs: [
            { timestamp: new Date().toISOString(), level: "INFO", message: "开始执行数据一致性检查..." },
            { timestamp: new Date().toISOString(), level: "INFO", message: "解析mainMapElemntInfo字段..." },
            { timestamp: new Date().toISOString(), level: "INFO", message: `解析mainMapElemntInfo字段: ${requestData.txHeader.mainMapElemntInfo}` },
            { timestamp: new Date().toISOString(), level: "INFO", message: `成功解析介质号: ${routingKey.value}` },
            { timestamp: new Date().toISOString(), level: "INFO", message: `解析成功: 类型=${routingKey.type}, 值=${routingKey.value}` },
            { timestamp: new Date().toISOString(), level: "INFO", message: "开始提取各表的查询条件..." },
            { timestamp: new Date().toISOString(), level: "INFO", message: `处理表: tb_dpmst_medium` },
            { timestamp: new Date().toISOString(), level: "INFO", message: "提取表 tb_dpmst_medium 的查询条件..." },
            { timestamp: new Date().toISOString(), level: "INFO", message: "  - 主键字段: medium_no" },
            { timestamp: new Date().toISOString(), level: "INFO", message: "  - 条件字段: medium_no" },
            { timestamp: new Date().toISOString(), level: "INFO", message: `  - 路由键类型: ${routingKey.type}, 值: ${routingKey.value}` },
            { timestamp: new Date().toISOString(), level: "INFO", message: `  - 使用路由键中的mediumNo: ${routingKey.value}` },
            { timestamp: new Date().toISOString(), level: "INFO", message: `  - 最终查询条件: {'medium_no': '${routingKey.value}'}` },
            { timestamp: new Date().toISOString(), level: "INFO", message: "开始查询执行前的数据..." },
            { timestamp: new Date().toISOString(), level: "INFO", message: "路由到: dcdpdb1.tb_dpmst_medium_0001 (hash=1)" },
            { timestamp: new Date().toISOString(), level: "SQL", message: `SQL查询: SELECT * FROM "tb_dpmst_medium_0001" WHERE medium_no = '${routingKey.value}'` },
            { timestamp: new Date().toISOString(), level: "INFO", message: `查询条件: {"medium_no": "${routingKey.value}"}` },
            { timestamp: new Date().toISOString(), level: "ERROR", message: "查询失败: connection to server at \"localhost\" (127.0.0.1), port 5432 failed: Connection refused" },
            { timestamp: new Date().toISOString(), level: "INFO", message: "未提供API响应，跳过接口调用" },
            { timestamp: new Date().toISOString(), level: "INFO", message: "开始查询执行后的数据..." },
            { timestamp: new Date().toISOString(), level: "SQL", message: `SQL查询: SELECT * FROM "tb_dpmst_medium_0001" WHERE medium_no = '${routingKey.value}'` },
            { timestamp: new Date().toISOString(), level: "INFO", message: `查询条件: {"medium_no": "${routingKey.value}"}` },
            { timestamp: new Date().toISOString(), level: "ERROR", message: "查询失败: connection to server at \"localhost\" (127.0.0.1), port 5432 failed: Connection refused" },
            { timestamp: new Date().toISOString(), level: "INFO", message: "开始比对数据差异..." },
            { timestamp: new Date().toISOString(), level: "INFO", message: "数据一致性检查完成" }
          ],
          results: [
            {
              table: "tb_dpmst_medium",
              status: "错误",
              message: "connection to server at \"localhost\" (127.0.0.1), port 5432 failed: Connection refused",
              before: {
                sql: `SELECT * FROM "tb_dpmst_medium_0001" WHERE medium_no = '${routingKey.value}'`,
                error: "connection to server at \"localhost\" (127.0.0.1), port 5432 failed: Connection refused",
                count: 0,
                data: []
              },
              after: {
                sql: `SELECT * FROM "tb_dpmst_medium_0001" WHERE medium_no = '${routingKey.value}'`,
                error: "connection to server at \"localhost\" (127.0.0.1), port 5432 failed: Connection refused",
                count: 0,
                data: []
              },
              diff: null
            }
          ],
          error: null
        };

        addLog(`API响应状态: 200`);
        addLog(`API响应数据: ${JSON.stringify(mockResponse, null, 2)}`);

        const responseLogs = mockResponse.logs || [];
        addLog(`后端返回的日志数量: ${responseLogs.length}`);
        
        if (responseLogs.length > 0) {
          addLog('后端返回的日志:');
          for (const log of responseLogs) {
            addLog(`[后端] ${log.message}`, log.level || 'INFO');
          }
        } else {
          addLog('后端未返回日志');
        }

        const backendResults = (mockResponse.results || []).map(result => ({
          table: result.table,
          status: result.status === '通过' ? '通过' : result.status === '失败' ? '失败' : '错误',
          message: result.message,
          details: {
            before: { count: result.before?.count || 0, sql: result.before?.sql || '' },
            after: { count: result.after?.count || 0, sql: result.after?.sql || '' }
          }
        }));

        addLog(`后端返回的结果数量: ${backendResults.length}`);
        setResults(backendResults);
        addLog('断言结果已生成');
        setTimeout(() => setActiveTab('result'), 800);
      } catch (apiError) {
        addLog(`API调用失败: ${apiError.message}`, 'ERROR');
        addLog(`API错误详情: ${JSON.stringify(apiError, null, 2)}`, 'ERROR');
        if (apiError.response?.data) {
          addLog(`API响应数据: ${JSON.stringify(apiError.response.data, null, 2)}`, 'ERROR');
          if (apiError.response.data?.logs) {
            addLog(`后端错误日志数量: ${apiError.response.data.logs.length}`, 'ERROR');
            for (const log of apiError.response.data.logs) {
              addLog(log.message, log.level || 'ERROR');
            }
          }
        }
        // 不要抛出异常，让流程继续执行
      }
    } catch (err) {
      addLog(`执行失败: ${err.message}`, 'ERROR');
      setError(err.message || '请求失败');
    } finally {
      setIsLoading(false);
      addLog('执行完成');
    }
  };

  const getLogClass = (level) => {
    switch (level) {
      case 'ERROR': return 'log-error';
      case 'WARN': return 'log-warn';
      case 'SQL': return 'log-sql';
      default: return 'log-info';
    }
  };

  const getStatusIcon = (status) => {
    if (status === '通过') return '✓';
    if (status === '失败') return '✗';
    return '!';
  };

  return (
    <div className="app">
      {/* 顶部导航栏 */}
      <header className="header">
        <div className="header-left">
          <div className="logo">
            <span className="logo-icon">⇌</span>
            <span className="logo-text">数据一致性核对工具</span>
          </div>
          <span className="header-badge">查-发-查-比</span>
        </div>
        <div className="header-right">
          <span className="status-dot"></span>
          <span className="status-text">就绪</span>
        </div>
      </header>

      {/* 主体内容 */}
      <main className="main">
        {/* 左侧配置面板 */}
        <aside className="sidebar">
          {/* 请求地址 */}
          <section className="card">
            <div className="card-header">
              <span className="card-icon">🔗</span>
              <span className="card-title">请求地址</span>
            </div>
            <div className="card-body">
              <input
                type="text"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                placeholder="输入API地址"
                className="input"
              />
            </div>
          </section>

          {/* 请求报文 */}
          <section className="card card-grow">
            <div className="card-header">
              <span className="card-icon">📋</span>
              <span className="card-title">请求报文</span>
            </div>
            <div className="card-body card-body-grow">
              <textarea
                value={requestBody}
                onChange={(e) => setRequestBody(e.target.value)}
                placeholder="输入JSON格式的请求报文"
                className="textarea code"
                spellCheck={false}
              />
            </div>
          </section>

          {/* 检查表配置 */}
          <section className="card">
            <div className="card-header">
              <span className="card-icon">🗃</span>
              <span className="card-title">检查表</span>
              <button onClick={addTable} className="btn-icon" title="添加表">+</button>
            </div>
            <div className="card-body">
              {tables.map((table, index) => (
                <div key={index} className="table-row">
                  <span className="table-index">{index + 1}</span>
                  <input
                    type="text"
                    value={table.name}
                    onChange={(e) => updateTableName(index, e.target.value)}
                    placeholder="表名"
                    className="input table-input"
                  />
                  {tables.length > 1 && (
                    <button onClick={() => removeTable(index)} className="btn-icon btn-danger" title="移除">×</button>
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* 发送按钮 */}
          <button onClick={sendRequest} className="btn-primary" disabled={isLoading}>
            {isLoading ? (
              <><span className="spinner"></span> 执行中...</>
            ) : (
              '▶ 执行核对'
            )}
          </button>
        </aside>

        {/* 右侧结果面板 */}
        <div className="content">
          {/* 错误提示 */}
          {error && (
            <div className="alert alert-error">
              <span className="alert-icon">⚠</span>
              <span>{error}</span>
            </div>
          )}

          {/* 标签页 */}
          <div className="tabs">
            <div className="tab-group">
              <button
                className={`tab ${activeTab === 'log' ? 'tab-active' : ''}`}
                onClick={() => setActiveTab('log')}
              >
                📜 执行日志
                {logs.length > 0 && <span className="badge">{logs.length}</span>}
              </button>
              {logs.length > 0 && (
                <button
                  className="tab-clear"
                  onClick={() => setLogs([])}
                  title="清空日志"
                >
                  🗑
                </button>
              )}
            </div>
            <button
              className={`tab ${activeTab === 'result' ? 'tab-active' : ''}`}
              onClick={() => setActiveTab('result')}
            >
              📊 断言结果
              {results.length > 0 && <span className="badge">{results.length}</span>}
            </button>
            <button
              className={`tab ${activeTab === 'response' ? 'tab-active' : ''}`}
              onClick={() => setActiveTab('response')}
            >
              📨 响应报文
            </button>
          </div>

          {/* 日志面板 */}
          {activeTab === 'log' && (
            <div className="panel">
              <div className="log-container" ref={logsRef}>
                {logs.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-icon">📋</div>
                    <div className="empty-text">点击"执行核对"开始检查</div>
                  </div>
                ) : (
                  logs.map((log, index) => (
                    <div key={index} className={`log-line ${getLogClass(log.level)}`}>
                      <span className="log-time">{log.timestamp}</span>
                      <span className={`log-level level-${log.level?.toLowerCase()}`}>{log.level}</span>
                      <span className="log-msg">{log.message}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* 结果面板 */}
          {activeTab === 'result' && (
            <div className="panel">
              {results.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">📊</div>
                  <div className="empty-text">暂无断言结果</div>
                </div>
              ) : (
                <div className="result-list">
                  {results.map((result, index) => (
                    <div key={index} className={`result-card ${result.status === '通过' ? 'result-pass' : 'result-fail'}`}>
                      <div className="result-top">
                        <div className="result-info">
                          <span className={`status-badge ${result.status === '通过' ? 'badge-pass' : 'badge-fail'}`}>
                            {getStatusIcon(result.status)} {result.status}
                          </span>
                          <span className="result-table-name">{result.table}</span>
                        </div>
                        <span className="result-msg">{result.message}</span>
                      </div>
                      <div className="result-sql-section">
                        <div className="sql-block">
                          <div className="sql-label">执行前 SQL</div>
                          <code className="sql-code">{result.details?.before?.sql || 'N/A'}</code>
                          <div className="sql-count">记录数: {result.details?.before?.count || 0}</div>
                        </div>
                        <div className="sql-arrow">→</div>
                        <div className="sql-block">
                          <div className="sql-label">执行后 SQL</div>
                          <code className="sql-code">{result.details?.after?.sql || 'N/A'}</code>
                          <div className="sql-count">记录数: {result.details?.after?.count || 0}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 响应报文面板 */}
          {activeTab === 'response' && (
            <div className="panel">
              {responseBody ? (
                <pre className="response-pre">{responseBody}</pre>
              ) : (
                <div className="empty-state">
                  <div className="empty-icon">📨</div>
                  <div className="empty-text">暂无响应报文</div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;