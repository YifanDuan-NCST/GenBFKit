#!/bin/bash
# Data_Preprocessing 目录快速安装脚本

echo "======================================"
echo "GenBFKit 数据预处理模块 - 安装脚本"
echo "======================================"
echo ""

# 检查 Python 版本
echo "1. 检查 Python 版本..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

echo "   Python 版本: $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo "   ❌ Python 版本过低，需要 Python 3.8 或更高版本"
    exit 1
fi

echo "   ✅ Python 版本符合要求"
echo ""

# 检查 pip
echo "2. 检查 pip..."
if ! command -v pip3 &> /dev/null; then
    echo "   ❌ 未找到 pip3"
    exit 1
fi
echo "   ✅ pip3 可用"
echo ""

# 安装依赖
echo "3. 安装依赖..."
echo "   这可能需要几分钟时间，请耐心等待..."

if pip3 install -r requirements.txt -q; then
    echo "   ✅ 依赖安装成功"
else
    echo "   ❌ 依赖安装失败"
    echo "   尝试使用国内镜像源..."
    if pip3 install -r requirements.txt -q -i https://pypi.tuna.tsinghua.edu.cn/simple; then
        echo "   ✅ 依赖安装成功（使用清华镜像）"
    else
        echo "   ❌ 依赖安装失败，请手动安装"
        exit 1
    fi
fi
echo ""

# 安装 Data_Preprocessing 包
echo "4. 安装 Data_Preprocessing 包为可编辑模式..."
if pip3 install -e . -q; then
    echo "   ✅ Data_Preprocessing 包安装成功"
else
    echo "   ❌ Data_Preprocessing 包安装失败"
    exit 1
fi
echo ""

# 验证安装
echo "5. 验证安装..."
python3 -c "from Data_Preprocessing import PreprocessingPipeline; print('   ✅ Data_Preprocessing 包导入成功')"

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✅ 安装完成！"
    echo "======================================"
    echo ""
    echo "你现在可以使用 Data_Preprocessing 模块了："
    echo ""
    echo "  from Data_Preprocessing import PreprocessingPipeline, PreprocessingConfig"
    echo "  pipeline = PreprocessingPipeline(PreprocessingConfig())"
    echo "  df_processed, stats = pipeline.preprocess_dataframe(df, steps=['missing_values', 'outlier_detection'])"
    echo ""
    echo "查看文档："
    echo "  - README.md: 完整使用指南"
    echo "  - USAGE_GUIDE.md: 使用说明"
    echo "  - example_usage.py: 使用示例"
    echo ""
    echo "运行示例："
    echo "  python example_usage.py"
    echo ""
else
    echo ""
    echo "❌ 安装验证失败"
    echo "请检查错误信息并重试"
    exit 1
fi
