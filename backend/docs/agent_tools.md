# Agent Tools Evaluation

## Vấn đề
Khi muốn đánh giá agent, ta cần biết agent sẽ gọi tools nào **mà không thực sự execute chúng** (để tiết kiệm chi phí, thời gian, tránh side-effects).

## Raw Agent vs AgentExecutor

### Raw Agent (`create_openai_functions_agent`)
```
Input: "What is wait time at hospital?"
         ↓
    [Agent quyết định]
         ↓
Output: {"tool": "Waits", "input": "Jordan Inc"}
```
- ✅ Chỉ **quyết định** gọi tool nào
- ✅ **KHÔNG execute** tools
- ✅ **Nhanh + rẻ**
- ❌ Chỉ lấy tool calls 1 lần, không lặp (chỉ dùng để test)

### AgentExecutor (wrapper)
```
Input: "What is wait time at hospital?"
  ↓
[Agent quyết định] → {"tool": "Waits", "input": "Jordan Inc"}
  ↓
[Execute tool thực tế] → wait_time = 30 phút
  ↓
[Agent quyết định tiếp] → trả về câu trả lời final
  ↓
Output: "Thời gian chờ tại hospital là 30 phút"
```
- ❌ **Thực sự execute** tools
- ❌ Lặp lại cho đến khi xong
- ❌ Chậm + tốn tiền
- ✅ Dùng cho production (lấy result thực tế)

## Cách sử dụng

### Đánh giá tools mà không execute
```python
from evaluator.agent_tools import AgentToolEvaluator

evaluator = AgentToolEvaluator(
    llm_model="openai",
    embedding_model="openai",
    user_id="test_user"
)

# Lấy tool calls mà không execute
result = evaluator.get_tool_calls("What is the wait time at hospital?")
print(result['tool_calls'])
# Output: [{'tool': 'Waits', 'input': 'Jordan Inc'}]
```

### Chạy agent thực tế (execute tools)
```python
from agents.hospital_rag_agent import HospitalRAGAgent

agent = HospitalRAGAgent(
    llm_model="openai",
    embedding_model="openai",
    user_id="test_user"
)

# Thực sự execute tools
result = agent.invoke("What is the wait time at hospital?")
print(result['output'])
# Output: "The wait time at Jordan Inc Hospital is 30 minutes"
```

## Các method trong AgentToolEvaluator

| Method | Mục đích |
|--------|---------|
| `get_tool_calls(query)` | Lấy tool calls cho 1 query (không execute) |
| `get_tool_calls_stream(query)` | Stream tool calls (không execute) |
| `compare_tool_selections(queries)` | So sánh tool selections giữa nhiều queries |

## Tóm tắt
- **Muốn test**: dùng `AgentToolEvaluator` + raw agent (nhanh, rẻ)
- **Muốn chạy thực tế**: dùng `HospitalRAGAgent` + `AgentExecutor` (slow, chi phí)
