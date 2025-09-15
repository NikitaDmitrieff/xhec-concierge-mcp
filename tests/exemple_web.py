from mistralai import Mistral

client = Mistral(api_key="Ry2yuGs2RqXlNWnxJDvtBK8xQjBIv9lI")

agent = client.beta.agents.create(
    model="mistral-medium-2505",
    name="Websearch Agent",
    description="Agent able to search info over the web",
    instructions="You can use `web_search` to find up-to-date information.",
    tools=[{"type": "web_search"}],
    completion_args={"temperature": 0.3, "top_p": 0.95},
)

resp = client.beta.conversations.start(
    agent_id=agent.id, inputs="Who won the last European Football cup?"
)

answer = " ".join(
    c.text
    for o in resp.outputs
    if o.type == "message.output"
    for c in o.content
    if c.type == "text"
)

print("Answer:", answer)
