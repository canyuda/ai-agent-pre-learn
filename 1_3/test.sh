#!/bin/bash
echo "===== txt 文件列表 ====="
for file in *.txt; do
    cp "$file" "${file%.txt}.md"
done