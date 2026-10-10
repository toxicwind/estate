import { useState, useEffect } from 'react'

export default function Benchmarks() {
  const [data, setData] = useState(null)
  const [sortKey, setSortKey] = useState('rank')
  const [sortDir, setSortDir] = useState(1)
  const [filterProvider, setFilterProvider] = useState('all')

  useEffect(() => {
    fetch('/benchmarks.json').then(r => r.json()).then(setData)
  }, [])

  if (!data) return <div style={{padding: 40}}>Loading benchmarks...</div>

  const providers = ['all', ...new Set(data.results.map(r => r.provider))]
  
  let rows = data.results.filter(r => 
    filterProvider === 'all' || r.provider === filterProvider
  )
  
  rows = [...rows].sort((a, b) => {
    const va = a[sortKey], vb = b[sortKey]
    return (va > vb ? 1 : va < vb ? -1 : 0) * sortDir
  })

  const th = (key, label) => (
    <th onClick={() => {
      if (sortKey === key) setSortDir(-sortDir)
      else { setSortKey(key); setSortDir(1) }
    }} style={{cursor: 'pointer', padding: '12px', textAlign: 'left', borderBottom: '2px solid #333', userSelect: 'none'}}>
      {label} {sortKey === key ? (sortDir > 0 ? '↑' : '↓') : ''}
    </th>
  )

  return (
    <div style={{padding: '24px', maxWidth: 1200, margin: '0 auto'}}>
      <h1 style={{fontSize: '2rem', marginBottom: 8}}>Roundup Benchmarks</h1>
      <p style={{color: '#888', marginBottom: 24}}>
        {data.count} models ranked · updated {data.updated} · 
        sort by clicking column headers
      </p>
      
      <div style={{marginBottom: 16}}>
        <label>Provider: </label>
        <select value={filterProvider} onChange={e => setFilterProvider(e.target.value)}
          style={{padding: '6px 12px', borderRadius: 6, background: '#1a1a1a', color: '#fff', border: '1px solid #333'}}>
          {providers.map(p => <option key={p} value={p}>{p}</option>)}
        </select>
      </div>

      <div style={{overflowX: 'auto'}}>
      <table style={{width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem'}}>
        <thead><tr>
          {th('rank', '#')}
          {th('model', 'Model')}
          {th('provider', 'Provider')}
          {th('quality', 'Quality')}
          {th('tps', 'TPS')}
          {th('ttft_ms', 'TTFT ms')}
          {th('p50_ms', 'P50 ms')}
          {th('err', 'Err')}
        </tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} style={{borderBottom: '1px solid #222', background: i % 2 ? '#111' : 'transparent'}}>
              <td style={{padding: '10px 12px', fontWeight: 'bold'}}>{r.rank}</td>
              <td style={{padding: '10px 12px', fontFamily: 'monospace'}}>{r.model}</td>
              <td style={{padding: '10px 12px'}}>
                <span style={{padding: '2px 8px', borderRadius: 4, background: r.provider === 'herd' ? '#1a3a1a' : '#1a1a3a', fontSize: '0.8rem'}}>
                  {r.provider}
                </span>
              </td>
              <td style={{padding: '10px 12px'}}>{r.quality.toFixed(2)}</td>
              <td style={{padding: '10px 12px'}}>{r.tps.toFixed(1)}</td>
              <td style={{padding: '10px 12px'}}>{r.ttft_ms}</td>
              <td style={{padding: '10px 12px'}}>{r.p50_ms}</td>
              <td style={{padding: '10px 12px'}}>{(r.err * 100).toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  )
}
