import json
from core.query_evaluator import evaluate_query


def main():
    print("自动化 Query 评测系统")
    print("=" * 50)
    
    while True:
        query = input("\n请输入要评测的 Query（输入 'quit' 退出）：").strip()
        
        if query.lower() == 'quit':
            print("再见！")
            break
        
        if not query:
            print("请输入有效的 Query！")
            continue
        
        result = evaluate_query(query)
        
        print("\n" + "-" * 50)
        print("评测结果：")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("-" * 50)


if __name__ == "__main__":
    main()
