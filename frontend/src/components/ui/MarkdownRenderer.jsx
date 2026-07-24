import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

/**
 * Markdown 渲染组件
 * 封装 react-markdown + remark-gfm，支持 GFM 语法
 * 通过 className 传递 CSS Module 样式
 */
export default function MarkdownRenderer({ content, className }) {
  if (!content || (typeof content === 'string' && !content.trim())) return null

  return (
    <div className={className}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          pre: ({ node, ...props }) => <pre {...props} />,
          code: ({ node, inline, ...props }) =>
            inline
              ? <code {...props} />
              : <code {...props} />,
          a: ({ node, ...props }) => <a target="_blank" rel="noopener noreferrer" {...props} />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
