from graph import get_executor
import state as state_module  # for confirmation tracking

executor = get_executor()

print("🤖 Welcome to the Product Manager Agent!")
print("Type your request (or type 'exit' to quit).")

while True:
    user_input = input("\n🧠 You: ").strip()

    if user_input.lower() in {"exit", "quit"}:
        print("👋 Goodbye!")
        break

    # ✅ Handle deletion confirmation
    if user_input.lower() == "yes" and state_module.has_pending_delete():
        print("✅ Confirmation received.")
        state_module.confirm_pending_delete()
        pending = state_module.get_pending_delete()

        if pending:
            output = executor.invoke({
                "input": "confirmed",  # dummy input
                "parsed": {
                    "intent": "delete",
                    "product_id": str(pending["product_id"])
                },
                "confirmed": True
            })

            # 👇 Force re-fetch updated product list
            output = executor.invoke({
                "input": "list all products",
                "parsed": {
                    "intent": "list"
                }
            })
        else:
            output = {"response": "❌ No pending deletion found."}

    elif user_input.lower() == "no" and state_module.has_pending_delete():
        state_module.clear_pending_delete()
        print("❌ Delete cancelled.")
        continue

    else:
        # Normal flow
        output = executor.invoke({"input": user_input})

    print("\n🤖 Agent:", output.get("response", "[No response]"))
