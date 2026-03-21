# TASK: 查询源扩展

> 分支: `feature/query-sources`
> 并行组: 第一组
> 优先级: 🟡 高
> 预计时间: 2-3 天
> 依赖: 无

***

## 一、目标

增加更多查询来源，降低被检测风险，提高搜索词多样性。

***

## 二、背景

### 2.1 API 验证结果

| API | 状态 | 备注 |
|-----|------|------|
| Bing Suggestions | ✅ 可用 | 已有实现 |
| Wikipedia Top Views | ✅ 可用 | 响应慢，需缓存 |
| Reddit Popular | ❌ 不可用 | API 政策变更 |
| Google Trends | ⚠️ 格式复杂 | 暂缓实现 |

### 2.2 现有实现

- `src/search/query_sources/bing_suggestions_source.py` - Bing 建议
- `src/search/query_sources/duckduckgo_source.py` - DuckDuckGo
- `src/search/query_sources/wikipedia_source.py` - Wikipedia 随机
- `src/search/query_sources/local_file_source.py` - 本地文件

***

## 三、任务清单

### 3.1 WikipediaTopViewsSource 实现

- [ ] 创建 `src/search/query_sources/wikipedia_top_views_source.py`
  - [ ] `fetch_queries()` - 获取热门文章
  - [ ] `get_source_name()` - 返回源名称
  - [ ] `is_available()` - 检查源可用性

### 3.2 API 端点

```
GET https://wikimedia.org/api/rest_v1/metrics/pageviews/top/{lang}.wikipedia/all-access/{yyyy}/{mm}/{dd}
```

### 3.3 缓存机制

- [ ] 实现带 TTL 的缓存（建议 6 小时）
- [ ] 缓存热门查询词列表
- [ ] 添加缓存命中率统计

### 3.4 查询源优先级

- [ ] 实现源优先级机制
- [ ] 配置默认优先级顺序

### 3.5 测试

- [ ] 创建 `tests/unit/test_wikipedia_top_views_source.py`
- [ ] 测试缓存机制
- [ ] 测试 API 超时处理

***

## 四、参考资源

### 4.1 现有查询源实现

```python
class QuerySource(ABC):
    @abstractmethod
    async def fetch_queries(self, count: int) -> list[str]:
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass
```

### 4.2 Wikipedia API 响应示例

```json
{
  "items": [{
    "articles": [
      {"article": "Main_Page", "views": 7246434, "rank": 1},
      {"article": "Special:Search", "views": 907420, "rank": 2}
    ]
  }]
}
```

***

## 五、验收标准

- [ ] WikipediaTopViewsSource 可成功获取热门文章
- [ ] 缓存机制正常工作
- [ ] 响应时间 < 5 秒（使用缓存）
- [ ] 单元测试覆盖率 > 80%

***

## 六、合并条件

- [ ] 所有测试通过
- [ ] Code Review 通过
- [ ] 无性能退化
