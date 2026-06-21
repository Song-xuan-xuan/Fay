"""
This script is an example of using the OpenAI API to create various interactions with a ChatGLM3 model.
It includes functions to:

1. Conduct a basic chat session, asking about weather conditions in multiple cities.
2. Initiate a simple chat in Chinese, asking the model to tell a short story.
3. Retrieve and print embeddings for a given text input.

Each function demonstrates a different aspect of the API's capabilities, showcasing how to make requests
and handle responses.
"""

from openai import OpenAI

base_url = "http://127.0.0.1:8000/v1/"
client = OpenAI(api_key="EMPTY", base_url=base_url)


def function_chat():
    messages = [{"role": "user", "content": "What's the weather like in San Francisco, Tokyo, and Paris?"}]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
            },
        }
    ]

    response = client.chat.completions.create(
        model="chatglm3",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    if response:
        content = response.choices[0].message.content
        print(content)
    else:
        print("Error:", response.status_code)


def chat(text):
    # 定义API请求的数据
    data = {
        "model": "chatglm3-6b",
        "prompt": text,
        "temperature": 0.5,  # 控制输出结果的随机性，范围从0.0到1.0，越高越随机
        "max_tokens": 75,    # 控制输出文本的长度
        "top_p": 1,          # 一个更复杂的参数，与temperature类似但更加精细控制
        "n": 1,              # 要返回的最完整的文本段落数
        "stream": False      # 是否以流的形式返回输出
    }
    # 发送API请求
    response = client.chat.completions.create(**data)
    # 打印响应结果
    print(response.get("choices")[0]["text"])

def chat2(text):
    messages = [
        {
            "role": "user",
            "content": text
        }
    ]
    response = client.chat.completions.create(
        model="chatglm3-6b",
        prompt=messages,
        stream=False,
        max_tokens=256,
        temperature=0.8,
        presence_penalty=1.1,
        top_p=0.8)
    if response:
        if False:
            for chunk in response:
                print(chunk.choices[0].delta.content)
        else:
            content = response.choices[0].message.content
            print(content)
    else:
        print("Error:", response.status_code)

def simple_chat(use_stream=True):
    messages = [
        {
            "role": "system",
            "content": "You are ChatGLM3, a large language model trained by Zhipu.AI. Follow the user's "
                       "instructions carefully. Respond using markdown.",
        },
        {
            "role": "user",
            "content": "你好，请你用生动的话语给我讲一个猫和狗的小故事吧"
        }
    ]
    response = client.chat.completions.create(
        model="chatglm3-6b",
        messages=messages,
        stream=use_stream,
        max_tokens=256,
        temperature=0.8,
        presence_penalty=1.1,
        top_p=0.8)
    if response:
        if use_stream:
            for chunk in response:
                print(chunk.choices[0].delta.content)
        else:
            content = response.choices[0].message.content
            print(content)
    else:
        print("Error:", response.status_code)
def chat3(text):
    history = [['你好', '你好，有什么帮到你呢？'],['你好，给我讲一个七仙女的故事，大概20字', '七个仙女下凡,来到人间,遇见了王子,经历了许多冒险和考验,最终爱情获胜']]
    messages=[]
    if history is not None:
        for string in history:
            # 打印字符串
            print(string)
            # for his in string:
            #     print(his)
            i = 0
            for his in string:
                print(his)
                if i==0:
                    dialogue={
                        "role": "user",
                        "content": his
                    }
                elif i==1:
                    dialogue={
                        "role": "assistant",
                        "content": his
                    }
                messages.append(dialogue)
                i = 1
    current = {
            "role": "user",
            "content": text
    }
    messages.append(current)
    print("===============messages=========================")
    print(messages)
    print("===============messages=========================")
    # messages = [
        
    #     {
    #         "role": "user",
    #         "content": text
    #     }
    # ]
    response = client.chat.completions.create(
        model="chatglm3-6b",
        messages=messages,
        stream=False,
        max_tokens=256,
        temperature=0.8,
        presence_penalty=1.1,
        top_p=0.8)
    if response:
        if False:
            for chunk in response:
                print(chunk.choices[0].delta.content)
        else:
            content = response.choices[0].message.content
            print(content)
    else:
        print("Error:", response.status_code)



def embedding():
    response = client.embeddings.create(
        model="BAAI/bge-m3",
        input=["你好，给我讲一个故事，大概100字"],
    )
    embeddings = response.data[0].embedding
    print("嵌入完成，维度：", len(embeddings))


if __name__ == "__main__":
    chat3("你好，给我讲楚汉相争的故事，大概20字")
    # simple_chat(use_stream=False)
    # simple_chat(use_stream=True)
    # embedding()
    # function_chat()

#     curl -X POST "http://127.0.0.1:8000/v1/chat/completions" \
# -H "Content-Type: application/json" \
# -d "{\"model\": \"chatglm3-6b\", \"messages\": [{\"role\": \"system\", \"content\": \"You are ChatGLM3, a large language model trained by Zhipu.AI. Follow the user's instructions carefully. Respond using markdown.\"}, {\"role\": \"user\", \"content\": \"你好，给我讲一个故事，大概100字\"}], \"stream\": false, \"max_tokens\": 100, \"temperature\": 0.8, \"top_p\": 0.8}"

# curl -X POST "http://127.0.0.1:8000/v1/completions" \
#      -H 'Content-Type: application/json' \
#      -d '{"prompt": "请用20字内回复我.你今年多大了", "history": []}'
    
# curl -X POST "http://127.0.0.1:8000/v1/completions" \
#      -H 'Content-Type: application/json' \
#      -d '{"prompt": "请用20字内回复我.你今年多大了", "history": [{"你好","你好👋！我是人工智能助手 ChatGLM-6B，很高兴见到你，欢迎问我任何问题。"}]}'


# curl -X POST "http://127.0.0.1:8000/v1/completions" \
#      -H 'Content-Type: application/json' \
#      -d '{"prompt": "请用20字内回复我.你今年多大了", "history": [["你好","你好👋！我是人工智能助手 ChatGLM-6B，很高兴见到你，欢迎问我任何问题。"]]}'


# curl -X POST "http://127.0.0.1:8000/v1/completions" \
#      -H 'Content-Type: application/json' \
#      -d '{"prompt": "请用20字内回复我.你今年多大了", "history": ["你好"]}'
    
    
