from openai import OpenAI
import httpx
http_client = httpx.Client(verify=False)
client = OpenAI(
    base_url="https://api.aimlapi.com/v1",
    api_key="fde37bf6e2ca4282a1609dcf25c9a062",
    http_client=http_client
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Write a one-sentence story about numbers."}]
)

print(response.choices[0].message.content)
