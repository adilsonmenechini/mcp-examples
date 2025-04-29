
from mcp.types import Input, Output

def execute(input: Input, context: dict) -> Output:
    plan_prompt = open("prompts/plan.txt").read()
    plan_context = {"prompt": plan_prompt, "input": input.text}
    plan_result = context["tool"].call(plan_context)

    exec_prompt = open("prompts/execute.txt").read()
    exec_context = {
        "prompt": exec_prompt,
        "input": input.text,
        "plan": plan_result["response"]
    }
    exec_result = context["tool"].call(exec_context)

    review_prompt = open("prompts/review.txt").read()
    review_context = {
        "prompt": review_prompt,
        "execution": exec_result["response"]
    }
    final_result = context["tool"].call(review_context)

    return Output(text=final_result["response"])
