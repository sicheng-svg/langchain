import os

def generate_masonry_svg():
    # 画布整体尺寸
    width = 800
    height = 400
    
    # 动画设置：25秒滚动一圈
    duration = "25s"
    
    # 定义你要展示的内容 (模拟从 GitHub Issues 抓取的数据)
    # 分为三行，贴合你图2的交错设计
    row1_items = [
        {"type": "text", "width": 280, "date": "2026-03-17", "title": "优化博客 Vercel 部署与 Cloudflare 路由配置"},
        {"type": "text", "width": 220, "date": "2026-03-16", "title": "CGO 中间件 Debug 完成"},
        {"type": "text", "width": 260, "date": "2026-03-15", "title": "LeetCode 树结构算法复盘"},
    ]
    
    row2_items = [
        {"type": "text", "width": 200, "date": "2026-03-14", "title": "测试 3X-UI 节点连通性"},
        # 如果是图片，你需要将其转换为 Base64，或者直接使用图床 URL (需要外网可访问)
        {"type": "image", "width": 180, "url": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"},
        {"type": "text", "width": 300, "date": "2026-03-12", "title": "研究 Claude Code 终端 Agent 工作流"},
    ]
    
    row3_items = [
        {"type": "text", "width": 300, "date": "2026-03-10", "title": "Redis-MongoDB 分层存储压测通过"},
        {"type": "text", "width": 250, "date": "2026-03-08", "title": "整理 miHoYo 后端开发面经"},
        {"type": "text", "width": 220, "date": "2026-03-05", "title": "看中一台成色不错的马自达 6"},
    ]

    # 行高与间距设置
    row_y_positions = [20, 150, 280] # 三行的 Y 坐标
    box_height = 110
    gap = 15

    def build_row_svg(items, start_y):
        svg_elements = ""
        current_x = 0
        for item in items:
            # 绘制外框
            svg_elements += f'<rect x="{current_x}" y="{start_y}" width="{item["width"]}" height="{box_height}" class="box"/>\n'
            
            # 绘制内容
            if item["type"] == "text":
                svg_elements += f'<text x="{current_x + 15}" y="{start_y + 30}" class="date">[{item["date"]}]</text>\n'
                # 简单处理文本换行（实际应用中可能需要根据字数自动折行）
                svg_elements += f'<text x="{current_x + 15}" y="{start_y + 60}" class="text">{item["title"][:15]}...</text>\n'
            elif item["type"] == "image":
                # 图片渲染，保持长宽比填满方框中心
                svg_elements += f'<image x="{current_x + 10}" y="{start_y + 10}" width="{item["width"] - 20}" height="{box_height - 20}" href="{item["url"]}" preserveAspectRatio="xMidYMid slice" />\n'
            
            current_x += item["width"] + gap
        
        # 返回该行的 SVG 元素和总宽度
        return svg_elements, current_x

    row1_svg, w1 = build_row_svg(row1_items, row_y_positions[0])
    row2_svg, w2 = build_row_svg(row2_items, row_y_positions[1])
    row3_svg, w3 = build_row_svg(row3_items, row_y_positions[2])

    # 找出最长的一行作为整体循环的平移基准跨度
    max_width = max(w1, w2, w3)

    # SVG 模板拼接
    svg_content = f"""<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <style>
        .box {{ fill: #161b22; stroke: #30363d; stroke-width: 1.5px; rx: 8px; }}
        .text {{ font-family: 'Fira Code', monospace, 'Microsoft YaHei'; font-size: 14px; fill: #c9d1d9; font-weight: bold; }}
        .date {{ font-family: 'Fira Code', monospace; font-size: 12px; fill: #58A6FF; }}
    </style>
    
    <rect width="100%" height="100%" fill="#0d1117" rx="8"/>
    
    <g>
        <animateTransform attributeName="transform" type="translate" from="0 0" to="-{max_width} 0" begin="0s" dur="{duration}" repeatCount="indefinite" />
        
        <g>
            {row1_svg}
            {row2_svg}
            {row3_svg}
        </g>
        
        <g transform="translate({max_width}, 0)">
            {row1_svg}
            {row2_svg}
            {row3_svg}
        </g>
    </g>
</svg>"""

    with open("dynamic-stream.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("生成成功！请在浏览器中打开 dynamic-stream.svg 预览多行交错效果。")

if __name__ == "__main__":
    generate_masonry_svg()