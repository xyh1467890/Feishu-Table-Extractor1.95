
import json
import re
from typing import TypedDict, Literal, Optional
from langgraph.graph import StateGraph, END
from langchain_ark import ChatArk
from prompts.business_reasoning_prompt import get_business_reasoning_prompt
from prompts.product_classification_prompt import get_product_classification_prompt
from prompts.multidimensional_table_prompt import get_multidimensional_table_prompt
from prompts.dashboard_prompt import get_dashboard_prompt
from prompts.workflow_prompt import get_workflow_prompt
from prompts.advanced_permission_prompt import get_advanced_permission_prompt
from prompts.comprehensive_evaluation_prompt import get_comprehensive_evaluation_prompt


class QueryState(TypedDict):
    query: str
    is_real_business_scenario: bool
    business_reason: str
    business_problem: str
    product_category: Literal["飞书多维表格", "仪表盘", "工作流", "高级权限"] | None
    within_ability_scope: bool
    ability_reason: str
    final_result: str
    final_reason: str


def parse_json_from_response(text: str) -> dict:
    """
    从模型响应中提取并解析 JSON，支持包含 markdown 代码块标记的情况
    """
    try:
        # 尝试直接解析
        return json.loads(text)
    except json.JSONDecodeError:
        # 尝试提取 ```json ... ``` 格式
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        # 尝试提取第一对大括号之间的内容
        brace_match = re.search(r'\{[\s\S]*\}', text)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass
        raise ValueError(f"无法解析响应: {text}")


def create_graph(api_key: str, api_base: Optional[str] = None, model_id: Optional[str] = None) -> StateGraph:
    """
    创建 LangGraph 流程图，支持动态传入 API Key 和 API Base
    
    Args:
        api_key: API Key
        api_base: API Base URL（可选）
        model_id: 模型 ID（可选）
    """
    model_config = {
        "api_key": api_key,
        "model": model_id or "ep-20260227203635-hrbjq",
        "temperature": 0.1
    }
    if api_base:
        model_config["base_url"] = api_base
    
    llm = ChatArk(**model_config)

    graph = StateGraph(QueryState)
    
    # 添加节点
    def business_reasoning_node(state: QueryState) -> QueryState:
        query = state["query"]
        prompt = get_business_reasoning_prompt(query)
        response = llm.invoke(prompt)
        result = parse_json_from_response(response.content)
        return {
            **state,
            "is_real_business_scenario": result["is_real_business_scenario"],
            "business_reason": result["reason"],
            "business_problem": result.get("problem", "")
        }
    
    def product_classification_node(state: QueryState) -> QueryState:
        query = state["query"]
        prompt = get_product_classification_prompt(query)
        response = llm.invoke(prompt)
        result = parse_json_from_response(response.content)
        return {
            **state,
            "product_category": result["product_category"]
        }
    
    def comprehensive_evaluation_node(state: QueryState) -> QueryState:
        query = state["query"]
        is_real = state["is_real_business_scenario"]
        category = state["product_category"]
        within_scope = state["within_ability_scope"]
        
        if is_real and within_scope:
            final_result = "合理且可执行"
        elif not is_real:
            final_result = "不符合业务场景"
        elif not within_scope:
            final_result = "超出能力范围"
        else:
            final_result = "无法判断"
        
        reason_prompt = get_comprehensive_evaluation_prompt(
            query=query,
            is_real=is_real,
            category=category,
            within_scope=within_scope,
            final_result=final_result
        )
        reason_response = llm.invoke(reason_prompt)
        result = parse_json_from_response(reason_response.content)
        return {
            **state,
            "final_result": result["final_result"],
            "final_reason": result["reason"]
        }
    
    # 能力边界判断节点
    def multidimensional_table_boundary(state: QueryState) -> QueryState:
        query = state["query"]
        prompt = get_multidimensional_table_prompt(query)
        response = llm.invoke(prompt)
        result = parse_json_from_response(response.content)
        return {
            **state,
            "within_ability_scope": result["within_ability_scope"],
            "ability_reason": result["reason"]
        }
    
    def dashboard_boundary(state: QueryState) -> QueryState:
        query = state["query"]
        prompt = get_dashboard_prompt(query)
        response = llm.invoke(prompt)
        result = parse_json_from_response(response.content)
        return {
            **state,
            "within_ability_scope": result["within_ability_scope"],
            "ability_reason": result["reason"]
        }
    
    def workflow_boundary(state: QueryState) -> QueryState:
        query = state["query"]
        prompt = get_workflow_prompt(query)
        response = llm.invoke(prompt)
        result = parse_json_from_response(response.content)
        return {
            **state,
            "within_ability_scope": result["within_ability_scope"],
            "ability_reason": result["reason"]
        }
    
    def advanced_permission_boundary(state: QueryState) -> QueryState:
        query = state["query"]
        prompt = get_advanced_permission_prompt(query)
        response = llm.invoke(prompt)
        result = parse_json_from_response(response.content)
        return {
            **state,
            "within_ability_scope": result["within_ability_scope"],
            "ability_reason": result["reason"]
        }
    
    graph.add_node("business_reasoning", business_reasoning_node)
    graph.add_node("product_classification", product_classification_node)
    graph.add_node("multidimensional_table_boundary", multidimensional_table_boundary)
    graph.add_node("dashboard_boundary", dashboard_boundary)
    graph.add_node("workflow_boundary", workflow_boundary)
    graph.add_node("advanced_permission_boundary", advanced_permission_boundary)
    graph.add_node("comprehensive_evaluation", comprehensive_evaluation_node)
    
    graph.set_entry_point("business_reasoning")
    graph.add_edge("business_reasoning", "product_classification")
    
    def route_by_category(state: QueryState) -> str:
        category = state["product_category"]
        if category == "飞书多维表格":
            return "multidimensional_table_boundary"
        elif category == "仪表盘":
            return "dashboard_boundary"
        elif category == "工作流":
            return "workflow_boundary"
        elif category == "高级权限":
            return "advanced_permission_boundary"
        else:
            return END
    
    graph.add_conditional_edges(
        "product_classification",
        route_by_category,
        {
            "multidimensional_table_boundary": "multidimensional_table_boundary",
            "dashboard_boundary": "dashboard_boundary",
            "workflow_boundary": "workflow_boundary",
            "advanced_permission_boundary": "advanced_permission_boundary",
            END: END
        }
    )
    
    graph.add_edge("multidimensional_table_boundary", "comprehensive_evaluation")
    graph.add_edge("dashboard_boundary", "comprehensive_evaluation")
    graph.add_edge("workflow_boundary", "comprehensive_evaluation")
    graph.add_edge("advanced_permission_boundary", "comprehensive_evaluation")
    graph.add_edge("comprehensive_evaluation", END)
    
    return graph.compile()


def evaluate_query(query: str, api_key: str, api_base: Optional[str] = None, 
                  model_id: Optional[str] = None, verbose: bool = False) -> dict:
    """
    评测一个 Query 的主入口函数，支持动态传入 API 配置
    
    Args:
        query: 待评测的 Query
        api_key: API Key
        api_base: API Base URL（可选）
        model_id: 模型 ID（可选）
        verbose: 是否打印中间过程
    
    Returns:
        评测结果字典
    """
    if verbose:
        print(f"开始评测 Query: {query}")
        print("=" * 60)
    
    app = create_graph(api_key, api_base, model_id)
    
    initial_state: QueryState = {
        "query": query,
        "is_real_business_scenario": False,
        "business_reason": "",
        "business_problem": "",
        "product_category": None,
        "within_ability_scope": False,
        "ability_reason": "",
        "final_result": "",
        "final_reason": ""
    }
    
    result = app.invoke(initial_state)
    
    if verbose:
        print("评测完成！")
        print("=" * 60)
    
    return {
        "query": result["query"],
        "is_real_business_scenario": result["is_real_business_scenario"],
        "business_reason": result["business_reason"],
        "business_problem": result["business_problem"],
        "product_category": result["product_category"],
        "within_ability_scope": result["within_ability_scope"],
        "ability_reason": result["ability_reason"],
        "final_result": result["final_result"],
        "reason": result["final_reason"]
    }
