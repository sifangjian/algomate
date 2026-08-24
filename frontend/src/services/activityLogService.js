import api from './api'

const activityLogService = {
  /**
   * 获取活动日志列表
   * @param {Object} params
   * @param {string} params.dateStr - 日期 YYYY-MM-DD，默认今天
   * @param {string} params.startDate - 起始日期 YYYY-MM-DD
   * @param {string} params.endDate - 结束日期 YYYY-MM-DD
   * @param {string} params.type - 日志类型筛选
   * @param {string} params.sortOrder - 排序: asc/desc
   * @param {number} params.limit - 返回条数上限
   * @returns {Promise<Array>}
   */
  getLogs: async (params = {}) => {
    const queryParams = {}
    if (params.dateStr) queryParams.date_str = params.dateStr
    if (params.startDate) queryParams.start_date = params.startDate
    if (params.endDate) queryParams.end_date = params.endDate
    if (params.type) queryParams.log_type = params.type
    if (params.sortOrder) queryParams.sort_order = params.sortOrder
    if (params.limit) queryParams.limit = params.limit
    return api.get('/v1/activity-logs', { params: queryParams })
  },

  /**
   * 手动添加日志
   * @param {string} content - 日志内容
   * @returns {Promise<Object>}
   */
  createManualLog: async (content) => {
    return api.post('/v1/activity-logs', { content })
  },
}

export { activityLogService }