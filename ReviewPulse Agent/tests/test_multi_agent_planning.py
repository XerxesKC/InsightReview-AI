import pytest
from app.agents.chat.state import ChatGraphState
from app.agents.chat.graph import ChatGraphCallbacks, build_chat_graph

@pytest.mark.asyncio
async def test_complex_planning_route():
    async def noop(state): return {}
    
    async def router_node(state):
        return {"intent": "complex_planning", "is_complex_task": True}
    
    async def planner_node(state):
        return {"plan": ["step1", "step2"], "current_step_index": 0, "past_steps": []}
        
    async def executor_node(state):
        plan = state.get("plan", [])
        curr = state.get("current_step_index", 0)
        past_steps = state.get("past_steps", [])
        if curr < len(plan):
            past_steps.append((plan[curr], "done"))
        return {"current_step_index": curr + 1, "past_steps": past_steps}
        
    async def synthesizer_node(state):
        return {"answer": "synthesized"}

    callbacks = ChatGraphCallbacks(
        input_process=noop,
        guardrails=noop,
        history=noop,
        rewrite=noop,
        router=router_node,
        retrieve=noop,
        rerank=noop,
        rag_gen=noop,
        chat_gen=noop,
        direct_rep=noop,
        tool_agent=noop,
        tool_output=noop,
        audit=noop,
        planner=planner_node,
        executor=executor_node,
        synthesizer=synthesizer_node,
    )
    
    graph = build_chat_graph(callbacks)
    
    mermaid = graph.get_graph().draw_mermaid()
    assert "planner" in mermaid
    assert "executor" in mermaid
    assert "synthesizer" in mermaid
    
    state = {
        "user_text": "hello",
        "last_message": "hello",
        "intent": "complex_planning",
    }
    result = await graph.ainvoke(state)
    
    assert result["answer"] == "synthesized"
    assert result["current_step_index"] == 2
    assert len(result["past_steps"]) == 2
    assert result["past_steps"][0] == ("step1", "done")
    assert result["past_steps"][1] == ("step2", "done")
