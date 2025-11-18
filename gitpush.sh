#!/bin/bash
# Copyright (c) Nex-AGI. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Git 快捷推送脚本

# 检查是否提供了提交信息
if [ -z "$1" ]; then
    echo "错误: 请提供提交信息"
    echo "用法: ./gitpush.sh \"你的提交信息\""
    exit 1
fi

# 执行 git 操作
echo "📦 添加所有更改..."
git add .

echo "💬 提交更改: $1"
git commit -m "$1"

echo "🚀 推送到远程仓库..."
git push

echo "✅ 完成!"
