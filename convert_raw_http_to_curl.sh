#!/bin/bash

# 将HTTP请求原始数据转换为curl命令的脚本

convert_to_curl() {
    local input_file="$1"
    local output_file="$2"
    
    # 如果没有提供输入文件，则从标准输入读取
    if [[ -z "$input_file" ]]; then
        input_data=$(cat)
    else
        input_data=$(cat "$input_file")
    fi
    
    # 提取请求行
    request_line=$(echo "$input_data" | head -n 1)
    method=$(echo "$request_line" | awk '{print $1}')
    url=$(echo "$request_line" | awk '{print $2}')
    http_version=$(echo "$request_line" | awk '{print $3}')
    
    # 提取headers
    headers=$(echo "$input_data" | awk 'NR>1 && /^$/ {exit} NR>1')
    
    # 提取请求体（空行后的内容）
    body=$(echo "$input_data" | awk 'x==1 {print} /^$/ {x=1}')
    
    # 构建curl命令
    curl_cmd="curl -X $method"
    
    # 添加URL
    curl_cmd="$curl_cmd \"$url\""
    
    # 添加headers
    while IFS= read -r line; do
        if [[ -n "$line" && "$line" =~ : ]]; then
            header_name=$(echo "$line" | cut -d: -f1)
            header_value=$(echo "$line" | cut -d: -f2- | sed 's/^[[:space:]]*//')
            # 跳过Content-Length头，因为curl会自动处理
            if [[ "$header_name" != "Content-Length" && "$header_name" != "Host" && "$header_name" != "Connection" ]]; then
                curl_cmd="$curl_cmd -H \"$header_name: $header_value\""
            fi
        fi
    done <<< "$headers"
    
    # 添加请求体
    if [[ -n "$body" ]]; then
        curl_cmd="$curl_cmd -d '$body'"
    fi
    
    # 输出结果
    if [[ -n "$output_file" ]]; then
        echo "$curl_cmd" > "$output_file"
        echo "curl命令已保存到: $output_file"
    else
        echo "$curl_cmd"
    fi
}

# 使用示例函数
main() {
    local input_file=""
    local output_file=""
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--input)
                input_file="$2"
                shift 2
                ;;
            -o|--output)
                output_file="$2"
                shift 2
                ;;
            -h|--help)
                echo "用法: $0 [-i input_file] [-o output_file]"
                echo "如果没有提供输入文件，则从标准输入读取"
                echo "示例:"
                echo "  $0 -i http_request.txt -o curl_command.sh"
                echo "  echo 'HTTP请求数据' | $0"
                return 0
                ;;
            *)
                echo "未知参数: $1"
                return 1
                ;;
        esac
    done
    
    convert_to_curl "$input_file" "$output_file"
}

# 如果直接运行脚本，则执行main函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
