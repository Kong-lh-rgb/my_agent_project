# tools/code_interpreter.py
import docker
import uuid
import os
from pydantic import BaseModel, Field
from langchain.tools import tool
from docker.errors import ContainerError, ImageNotFound, APIError
from typing import Type

class CodeExecutionInput(BaseModel):
    language: str = Field(description="代码的编程语言，例如 'python', 'javascript', 'java', 'c'。")
    code: str = Field(description="要执行的源代码字符串。")


@tool(args_schema=CodeExecutionInput)
def execute_code(language: str, code: str) -> str:
    """
    在 Docker 容器中执代码并返回输出。
    """
    language = language.lower()

    shell_safe_code = code.replace('\\', '\\\\').replace("'", "'\\''")

    lang_map = {
        "python": ("python:3.10-slim", ["python", "-c", code]),
        "javascript": ("node:18-alpine", ["node", "-e", code]),
        "shell": ("alpine:latest", ["/bin/sh", "-c", code]),
        "c": ("gcc:latest", ["/bin/sh", "-c", f"echo '{shell_safe_code}' > main.c && gcc main.c -o main && ./main"]),
        "cpp": ("gcc:latest", ["/bin/sh", "-c", f"echo '{shell_safe_code}' > main.cpp && g++ main.cpp -o main && ./main"]),
        "java": ("openjdk:17-jdk-slim",["/bin/sh", "-c", f"echo '{shell_safe_code}' > Main.java && javac Main.java && java Main"]),
    }


    if language not in lang_map:
        return f"错误：不支持的语言 '{language}'。支持的语言包括：{list(lang_map.keys())}"

    image_name, command = lang_map[language]
    try:
        client = docker.from_env()

        try:
            client.images.get(image_name)
        except ImageNotFound:
            print(f"正在拉取镜像: {image_name}...")
            client.images.pull(image_name)
            print("镜像拉取完成。")


        container = client.containers.run(
            image=image_name,
            command=command,
            detach=True,
            working_dir="/app",
        )

        result = container.wait(timeout=60)

        # 分别获取标准输出和标准错误
        stdout = container.logs(stdout=True, stderr=False).decode('utf-8').strip()
        stderr = container.logs(stdout=False, stderr=True).decode('utf-8').strip()

        container.remove()

        if result['StatusCode'] == 0:
            if stdout:
                return f"代码执行成功，输出:\n---\n{stdout}"
            else:
                return "代码执行成功，但没有产生任何输出。"
        else:
            return f"代码执行出错，错误信息:\n---\n{stderr}"

    except ContainerError as e:
        return f"容器执行错误: {e}"
    except APIError as e:
        return f"Docker API 错误: {e}. 请确保 Docker 正在运行。"
    except Exception as e:
        if 'container' in locals() and container:
            try:
                container.stop()
                container.remove()
            except APIError:
                pass
        return f"执行时发生未知错误: {e}"
