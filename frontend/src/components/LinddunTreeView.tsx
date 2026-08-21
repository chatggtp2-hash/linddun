import React, { useMemo, useState, useCallback } from 'react'
import ReactFlow, {
  Node, Edge, Background, Controls, MiniMap, useNodesState, useEdgesState, Handle, Position,
} from 'reactflow'
import 'reactflow/dist/style.css'
import type { TreeNode } from '../types'

const RISK_COLOR: Record<string, string> = {
  LOW: '#16a34a', MEDIUM: '#ca8a04', HIGH: '#ea580c', CRITICAL: '#dc2626', NONE: '#94a3b8',
}

function TreeNodeCard({ data }: { data: any }) {
  const color = RISK_COLOR[data.risk] || RISK_COLOR.NONE
  return (
    <div
      style={{
        border: `2px solid ${color}`,
        background: '#fff',
        borderRadius: 10,
        padding: '8px 12px',
        minWidth: 170,
        fontSize: 12,
        cursor: 'pointer',
      }}
      onClick={() => data.onClick?.(data)}
    >
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      <div style={{ fontWeight: 700, marginBottom: 4 }}>{data.name}</div>
      <div style={{ display: 'flex', justifyContent: 'space-between', color: '#6b7280' }}>
        <span style={{ color, fontWeight: 600 }}>{data.risk}</span>
        <span>Score: {data.score}</span>
      </div>
      <div style={{ color: '#9ca3af', marginTop: 2 }}>
        Q: {data.question_count} · Evidence: {data.evidence_count}
      </div>
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </div>
  )
}

const nodeTypes = { treeNode: TreeNodeCard }

// Simple auto-layout: BFS levels, spread siblings horizontally.
function layoutTree(categories: TreeNode[]) {
  const nodes: Node[] = []
  const edges: Edge[] = []
  let globalX = 0
  const LEVEL_HEIGHT = 130
  const NODE_WIDTH = 200

  function place(node: TreeNode, depth: number, parentId: string | null): number {
    if (!node.children || node.children.length === 0) {
      const x = globalX * NODE_WIDTH
      globalX += 1
      nodes.push({
        id: node.id,
        type: 'treeNode',
        position: { x, y: depth * LEVEL_HEIGHT },
        data: node,
      })
      if (parentId) edges.push({ id: `${parentId}-${node.id}`, source: parentId, target: node.id })
      return x
    }
    const childXs = node.children.map((c) => place(c, depth + 1, node.id))
    const x = childXs.reduce((a, b) => a + b, 0) / childXs.length
    nodes.push({
      id: node.id,
      type: 'treeNode',
      position: { x, y: depth * LEVEL_HEIGHT },
      data: node,
    })
    if (parentId) edges.push({ id: `${parentId}-${node.id}`, source: parentId, target: node.id })
    return x
  }

  categories.forEach((cat) => {
    place(cat, 0, null)
  })

  return { nodes, edges }
}

export default function LinddunTreeView({ tree }: { tree: TreeNode[] }) {
  const [selected, setSelected] = useState<TreeNode | null>(null)
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => layoutTree(tree), [tree])

  const nodesWithClick = useMemo(
    () => initialNodes.map((n) => ({ ...n, data: { ...n.data, onClick: setSelected } })),
    [initialNodes]
  )

  const [nodes, , onNodesChange] = useNodesState(nodesWithClick)
  const [edges, , onEdgesChange] = useEdgesState(initialEdges)

  if (!tree || tree.length === 0) {
    return <div className="empty-state">No tree data yet — the tree renders automatically once the framework is seeded.</div>
  }

  return (
    <div style={{ display: 'flex', gap: 16 }}>
      <div style={{ height: 520, flex: 1, border: '1px solid #e0e4e8', borderRadius: 8 }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          minZoom={0.3}
        >
          <Background />
          <Controls />
          <MiniMap pannable zoomable />
        </ReactFlow>
      </div>
      {selected && (
        <div className="card" style={{ width: 260 }}>
          <h4 style={{ marginTop: 0 }}>{selected.name}</h4>
          <div style={{ fontSize: 12, color: '#6b7280' }}>Code: {selected.code}</div>
          <div style={{ marginTop: 8 }}>
            <span className={`badge badge-${selected.risk}`}>{selected.risk}</span>
          </div>
          <div style={{ marginTop: 10, fontSize: 13 }}>
            <div>Score: {selected.score}</div>
            <div>Mapped questions: {selected.question_count}</div>
            <div>Evidence attached: {selected.evidence_count}</div>
          </div>
        </div>
      )}
    </div>
  )
}
