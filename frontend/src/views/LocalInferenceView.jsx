/**
 * Local Inference Test View
 *
 * Simple interface for testing MLX local inference directly
 * without search, preprocessing, or foundation model overhead.
 */

import { useState } from 'react'
import './LocalInferenceView.css'

export default function LocalInferenceView() {
  const [query, setQuery] = useState('')
  const [response, setResponse] = useState('')
  const [loading, setLoading] = useState(false)
  const [metadata, setMetadata] = useState(null)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!query.trim()) {
      setError('Please enter a query')
      return
    }

    setLoading(true)
    setError(null)
    setResponse('')
    setMetadata(null)

    try {
      const res = await fetch('/api/research/local-inference', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: query,
          max_tokens: 500,
          temperature: 0.3
        })
      })

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP ${res.status}`)
      }

      const data = await res.json()
      setResponse(data.content)
      setMetadata(data.metadata)
    } catch (err) {
      console.error('Local inference failed:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="local-inference-view">
      <div className="local-inference-header">
        <h1>Local MLX Inference Test</h1>
        <p className="subtitle">
          Direct gpt-oss-20b-4bit inference on Metal GPU
        </p>
      </div>

      <form onSubmit={handleSubmit} className="inference-form">
        <div className="form-group">
          <label htmlFor="query">Prompt</label>
          <textarea
            id="query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your prompt here..."
            rows={4}
            disabled={loading}
          />
        </div>

        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="submit-btn"
        >
          {loading ? 'Generating...' : 'Generate'}
        </button>
      </form>

      {error && (
        <div className="error-box">
          <strong>Error:</strong> {error}
        </div>
      )}

      {response && (
        <div className="response-section">
          <h2>Response</h2>
          <div className="response-box">
            {response}
          </div>

          {metadata && (
            <div className="metadata-box">
              <h3>Generation Metadata</h3>
              <table>
                <tbody>
                  <tr>
                    <td>Model</td>
                    <td>{metadata.model}</td>
                  </tr>
                  <tr>
                    <td>Latency</td>
                    <td>{metadata.latency_ms}ms ({(metadata.latency_ms / 1000).toFixed(2)}s)</td>
                  </tr>
                  <tr>
                    <td>Prompt Tokens</td>
                    <td>{metadata.usage?.prompt_tokens || 0}</td>
                  </tr>
                  <tr>
                    <td>Completion Tokens</td>
                    <td>{metadata.usage?.completion_tokens || 0}</td>
                  </tr>
                  <tr>
                    <td>Total Tokens</td>
                    <td>{metadata.usage?.total_tokens || 0}</td>
                  </tr>
                  <tr>
                    <td>Speed</td>
                    <td>
                      {metadata.usage?.completion_tokens && metadata.latency_ms
                        ? `${((metadata.usage.completion_tokens / metadata.latency_ms) * 1000).toFixed(2)} tokens/sec`
                        : 'N/A'}
                    </td>
                  </tr>
                  <tr>
                    <td>Finish Reason</td>
                    <td>{metadata.finish_reason}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
