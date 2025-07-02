from langgraph.graph import StateGraph
from typing import TypedDict, Optional
from langchain_core.runnables import RunnableConfig

from parser import parse_user_input
import api
import state as state_module


# ✅ Define graph state schema
class GraphState(TypedDict, total=False):  # all fields optional
    input: str
    parsed: dict
    response: str
    next: str
    confirmed: bool  # ✅ add this line


# ✅ LangGraph nodes

def parse_input_node(state: GraphState, config: Optional[RunnableConfig] = None) -> dict:
    user_input = state.get("input")

    if not user_input:
        state["response"] = "❌ Missing input."
        return dict(state, next="respond")

    # ✅ Skip parsing if already confirmed (bypasses accidental re-parsing of 'yes')
    if state.get("confirmed"):
        print("🔁 Skipping parse — using previously set 'parsed' intent (confirmed delete)")
        return dict(state, next="call_api")

    # ✅ Normal parse
    parsed = parse_user_input(user_input)
    state["parsed"] = parsed

    if parsed["intent"] == "delete":
        state_module.set_pending_delete(parsed["product_id"])
        state["response"] = f"⚠️ Are you sure you want to delete product ID {parsed['product_id']}? (yes/no)"
        return dict(state, next="confirm_delete")

    return dict(state, next="call_api")



def confirm_delete_node(state: GraphState, config: Optional[RunnableConfig] = None) -> dict:
    pending = state_module.get_pending_delete()
    if pending and pending["confirmed"]:
        return dict(state, next="call_api")
    return dict(state, next="respond")


def call_api_node(state: GraphState, config: Optional[RunnableConfig] = None) -> dict:
    parsed = state.get("parsed")
    if not parsed:
        state["response"] = "❌ No parsed data available."
        return dict(state, next="respond")

    try:
        intent = parsed["intent"]
        confirmed = state.get("confirmed", False)

        if intent == "list":
            products = api.get_all_products()
            if products:
                lines = [
                    f"[{p['id']}] {p['name']} - ${p['price']}" for p in products]
                state["response"] = "📦 Products:\n" + "\n".join(lines)
            else:
                state["response"] = "📦 No products found."

        elif intent == "create":
            product = api.create_product(
                name=parsed["name"],
                price=parsed["price"],
                description=parsed["description"]
            )
            state["response"] = f"✅ Created: {product}"

        elif intent == "update":
            updated = api.update_product(
                product_id=parsed["product_id"],
                name=parsed.get("name"),
                price=parsed.get("price"),
                description=parsed.get("description")
            )
            state["response"] = f"✅ Updated: {updated}"

        elif intent == "delete":
            print("🚨 ENTERED DELETE BRANCH in call_api_node")

            product_id = parsed["product_id"]
            if confirmed:
                success = api.delete_product(str(product_id))
                state["response"] = (
                    f"✅ Deleted product ID {product_id}"
                    if success else "❌ Deletion failed."
                )
                state_module.clear_pending_delete()
                # return dict(state, next="respond")

            else:
                state[
                    "response"] = f"⚠️ Are you sure you want to delete product ID {product_id}? (yes/no)"
                state_module.set_pending_delete(product_id)
                return dict(state, next="confirm_delete")

        elif intent == "get":
            product = api.get_product_by_id(parsed["product_id"])
            if product:
                state["response"] = f"🧾 {product['name']} - {product['price']} - {product['description']}"
            else:
                state["response"] = "❌ Product not found."

        else:
            state["response"] = "❓ Unknown intent."

    except Exception as e:
        state["response"] = f"❌ API Error: {str(e)}"

    return dict(state, next="respond")


def respond_node(state: GraphState, config: Optional[RunnableConfig] = None) -> dict:
    return dict(state)


# ✅ Graph compiler
def get_executor():
    builder = StateGraph(GraphState)

    builder.add_node("parse_input", parse_input_node)
    builder.add_node("confirm_delete", confirm_delete_node)
    builder.add_node("call_api", call_api_node)
    builder.add_node("respond", respond_node)

    builder.set_entry_point("parse_input")
    builder.set_finish_point("respond")

    # ✅ Dynamic edges based on 'next' field
    builder.add_conditional_edges("parse_input", lambda s: s["next"])
    builder.add_conditional_edges("confirm_delete", lambda s: s["next"])
    builder.add_conditional_edges("call_api", lambda s: s["next"])

    return builder.compile()
