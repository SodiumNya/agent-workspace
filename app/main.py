import argparse
from app.llm.factory import create_llm_client
from app.prompts.meeting import build_user_prompt, SYSTEM_PROMPR
from app.llm.schemas import RequestStatus


def main():
    paser = argparse.ArgumentParser(
        description="meeting_summary"
    )
    paser.add_argument("--text", type=str, required=True, help="meeting contents")

    args = paser.parse_args() # 获得参数

    # 拿到text
    meeting_content = args.text.strip()

    if meeting_content == "":
        raise ValueError("text is blank!")

    # 构造prompt
    prompt = build_user_prompt(meeting_content)
    # 发送请求
    llm_client = create_llm_client(mode="sdk")
    result = llm_client.generate(prompt=prompt, system_prompt=SYSTEM_PROMPR)
    # 显示结果
    if result.status == RequestStatus.SUCCESS:
        print("\n========== 整理结果 ==========\n")
        print(result.content)
    elif result.status == RequestStatus.FAILED:
        print("请求失败：", result.error)
        raise SystemExit(1)
    else:
        print("\n似乎遇到了一点问题呢, 执行状态未知\n")
        print(f"原因：{result.error}")
        raise SystemExit(1)

if __name__ == "__main__":
    main()