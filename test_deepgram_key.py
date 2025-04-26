"""
Deepgram API 密钥测试脚本

这个脚本用于测试 Deepgram API 密钥是否有效。
它会尝试使用提供的 API 密钥建立与 Deepgram 服务的连接，
并返回连接状态和详细信息。

使用方法:
1. 确保已安装 deepgram-sdk: pip install deepgram-sdk
2. 运行脚本: python test_deepgram_key.py
"""

import os
from dotenv import load_dotenv
from deepgram import DeepgramClient

def test_deepgram_key():
    """
    测试 Deepgram API 密钥是否有效
    
    返回:
        bool: 密钥是否有效
    """
    # 加载环境变量
    load_dotenv()
    
    # 获取API密钥
    api_key = os.getenv("DEEPGRAM_API_KEY")
    
    if not api_key:
        print("错误: 未找到 DEEPGRAM_API_KEY 环境变量")
        print("请确保在 .env 文件中设置了 DEEPGRAM_API_KEY=您的密钥")
        return False
    
    print(f"找到 API 密钥，长度为 {len(api_key)} 个字符")
    
    try:
        # 初始化 Deepgram 客户端
        client = DeepgramClient(api_key=api_key)
        
        # 尝试获取项目信息来验证密钥
        # 这是一个简单的 API 调用，不会产生费用
        print("正在验证 API 密钥...")
        
        # 获取余额信息 (这是一个轻量级调用)
        response = client.manage.get_balance()
        
        print("API 密钥有效!")
        print(f"账户余额信息: {response}")
        return True
        
    except Exception as e:
        print(f"API 密钥验证失败: {str(e)}")
        
        # 提供更详细的错误信息
        if "401" in str(e):
            print("错误 401: 未授权。这通常意味着 API 密钥无效或已过期。")
        elif "403" in str(e):
            print("错误 403: 禁止访问。这通常意味着 API 密钥没有足够的权限。")
        
        return False

if __name__ == "__main__":
    print("===== Deepgram API 密钥测试 =====")
    result = test_deepgram_key()
    
    if result:
        print("\n✅ 测试通过: API 密钥有效")
    else:
        print("\n❌ 测试失败: API 密钥无效或配置错误")
        
    print("\n如果您需要获取新的 API 密钥，请访问 https://console.deepgram.com/")