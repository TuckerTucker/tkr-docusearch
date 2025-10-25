import { useState } from 'react'
import './InferenceDebugPanel.css'

/**
 * InferenceDebugPanel - Display full LLM inference flow for debugging
 *
 * Shows:
 * - System prompt
 * - User prompt (formatted context + query)
 * - LLM request parameters
 * - Image URLs (if vision enabled)
 * - Raw LLM response
 * - Token usage and costs
 * - Timing breakdown
 */
export default function InferenceDebugPanel({ metadata }) {
  const [activeTab, setActiveTab] = useState('overview')

  if (!metadata) {
    return (
      <div className="inference-debug-panel">
        <div className="inference-debug-panel__empty">
          No inference data available. Submit a query to see the full LLM flow.
        </div>
      </div>
    )
  }

  // Calculate costs (approximate)
  const inputCost = metadata.llm_usage_details?.prompt_tokens
    ? (metadata.llm_usage_details.prompt_tokens / 1_000_000) * 10.0
    : 0
  const outputCost = metadata.llm_usage_details?.completion_tokens
    ? (metadata.llm_usage_details.completion_tokens / 1_000_000) * 30.0
    : 0
  const totalCost = inputCost + outputCost

  return (
    <div className="inference-debug-panel">
      <div className="inference-debug-panel__header">
        <h2>Inference Flow Debug</h2>
        <div className="inference-debug-panel__stats">
          <span className="stat">
            Model: <strong>{metadata.model_used}</strong>
          </span>
          <span className="stat">
            Total: <strong>{metadata.processing_time_ms}ms</strong>
          </span>
          <span className="stat">
            LLM: <strong>{metadata.llm_latency_ms}ms</strong>
          </span>
          <span className="stat">
            Cost: <strong>${totalCost.toFixed(4)}</strong>
          </span>
        </div>
      </div>

      <div className="inference-debug-panel__tabs">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`tab ${activeTab === 'system' ? 'active' : ''}`}
          onClick={() => setActiveTab('system')}
        >
          System Prompt
        </button>
        <button
          className={`tab ${activeTab === 'user' ? 'active' : ''}`}
          onClick={() => setActiveTab('user')}
        >
          User Prompt
        </button>
        <button
          className={`tab ${activeTab === 'context' ? 'active' : ''}`}
          onClick={() => setActiveTab('context')}
        >
          Context Only
        </button>
        {metadata.preprocessing_enabled && (
          <>
            <button
              className={`tab ${activeTab === 'preprocessing' ? 'active' : ''}`}
              onClick={() => setActiveTab('preprocessing')}
            >
              MLX Preprocessing
            </button>
            <button
              className={`tab ${activeTab === 'before-after' ? 'active' : ''}`}
              onClick={() => setActiveTab('before-after')}
            >
              Before/After
            </button>
          </>
        )}
        {metadata.image_urls_sent && (
          <button
            className={`tab ${activeTab === 'images' ? 'active' : ''}`}
            onClick={() => setActiveTab('images')}
          >
            Images ({metadata.images_sent})
          </button>
        )}
        <button
          className={`tab ${activeTab === 'response' ? 'active' : ''}`}
          onClick={() => setActiveTab('response')}
        >
          Raw Response
        </button>
        <button
          className={`tab ${activeTab === 'params' ? 'active' : ''}`}
          onClick={() => setActiveTab('params')}
        >
          Parameters
        </button>
      </div>

      <div className="inference-debug-panel__content">
        {activeTab === 'overview' && (
          <div className="overview-tab">
            <h3>Request Flow</h3>
            <div className="flow-steps">
              <div className="flow-step">
                <div className="step-number">1</div>
                <div className="step-content">
                  <h4>Search & Context Building</h4>
                  <p>
                    Retrieved {metadata.total_sources} sources in{' '}
                    {metadata.search_latency_ms}ms
                  </p>
                  <p>
                    Context: {metadata.context_tokens} tokens
                    {metadata.context_truncated && ' (truncated)'}
                  </p>
                </div>
              </div>

              {metadata.preprocessing_enabled && (
                <div className="flow-step">
                  <div className="step-number">2</div>
                  <div className="step-content">
                    <h4>Local LLM Preprocessing</h4>
                    <p>
                      Strategy: {metadata.preprocessing_strategy} (
                      {metadata.preprocessing_latency_ms}ms)
                    </p>
                    <p>
                      Token reduction: {metadata.token_reduction_percent.toFixed(1)}%
                    </p>
                  </div>
                </div>
              )}

              <div className="flow-step">
                <div className="step-number">
                  {metadata.preprocessing_enabled ? 3 : 2}
                </div>
                <div className="step-content">
                  <h4>Foundation LLM Request</h4>
                  <p>
                    Model: {metadata.model_used} (temp:{' '}
                    {metadata.llm_request_params?.temperature})
                  </p>
                  <p>
                    Input: {metadata.llm_usage_details?.prompt_tokens || 0} tokens
                    {metadata.vision_enabled &&
                      ` + ${metadata.images_sent} images (~${metadata.image_tokens} tokens)`}
                  </p>
                  <p>Latency: {metadata.llm_latency_ms}ms</p>
                </div>
              </div>

              <div className="flow-step">
                <div className="step-number">
                  {metadata.preprocessing_enabled ? 4 : 3}
                </div>
                <div className="step-content">
                  <h4>Response & Citation Parsing</h4>
                  <p>
                    Output: {metadata.llm_usage_details?.completion_tokens || 0}{' '}
                    tokens
                  </p>
                  <p>
                    Total tokens: {metadata.llm_usage_details?.total_tokens || 0}
                  </p>
                  <p>Cost: ${totalCost.toFixed(4)}</p>
                </div>
              </div>
            </div>

            <h3>Token Usage Breakdown</h3>
            <table className="usage-table">
              <thead>
                <tr>
                  <th>Component</th>
                  <th>Tokens</th>
                  <th>Cost</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Input (prompt + context)</td>
                  <td>{metadata.llm_usage_details?.prompt_tokens || 0}</td>
                  <td>${inputCost.toFixed(4)}</td>
                </tr>
                {metadata.vision_enabled && (
                  <tr>
                    <td>Images ({metadata.images_sent} pages)</td>
                    <td>~{metadata.image_tokens}</td>
                    <td>Included in input</td>
                  </tr>
                )}
                <tr>
                  <td>Output (completion)</td>
                  <td>{metadata.llm_usage_details?.completion_tokens || 0}</td>
                  <td>${outputCost.toFixed(4)}</td>
                </tr>
                <tr className="total-row">
                  <td>
                    <strong>Total</strong>
                  </td>
                  <td>
                    <strong>
                      {metadata.llm_usage_details?.total_tokens || 0}
                    </strong>
                  </td>
                  <td>
                    <strong>${totalCost.toFixed(4)}</strong>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'system' && (
          <div className="prompt-tab">
            <h3>System Prompt</h3>
            <p className="prompt-description">
              Instructions sent to the LLM to define its role and behavior
            </p>
            <pre className="prompt-content">{metadata.system_prompt}</pre>
          </div>
        )}

        {activeTab === 'user' && (
          <div className="prompt-tab">
            <h3>User Prompt</h3>
            <p className="prompt-description">
              Full prompt including formatted context and user query
            </p>
            <pre className="prompt-content">{metadata.user_prompt}</pre>
            <div className="prompt-stats">
              <span>
                Length: {metadata.user_prompt?.length.toLocaleString()} chars
              </span>
              <span>Tokens: ~{metadata.context_tokens}</span>
            </div>
          </div>
        )}

        {activeTab === 'context' && (
          <div className="prompt-tab">
            <h3>Formatted Context Only</h3>
            <p className="prompt-description">
              {metadata.preprocessing_enabled
                ? 'Final compressed context sent to foundation model (after MLX preprocessing)'
                : 'Retrieved document chunks formatted for the LLM (without query)'}
            </p>
            <pre className="prompt-content">{metadata.formatted_context}</pre>
            <div className="prompt-stats">
              <span>Sources: {metadata.total_sources}</span>
              <span>Tokens: {metadata.context_tokens}</span>
              {metadata.context_truncated && (
                <span className="warning">⚠️ Context was truncated</span>
              )}
              {metadata.preprocessing_enabled && (
                <span className="success">
                  ✓ Compressed by {metadata.preprocessing_model}
                </span>
              )}
            </div>
          </div>
        )}

        {activeTab === 'preprocessing' && metadata.preprocessing_enabled && (
          <div className="preprocessing-tab">
            <h3>Local MLX Preprocessing</h3>
            <div className="preprocessing-info">
              <div className="info-card">
                <div className="info-label">Model</div>
                <div className="info-value">{metadata.preprocessing_model}</div>
              </div>
              <div className="info-card">
                <div className="info-label">Strategy</div>
                <div className="info-value">{metadata.preprocessing_strategy}</div>
              </div>
              <div className="info-card">
                <div className="info-label">Latency</div>
                <div className="info-value">{metadata.preprocessing_latency_ms}ms</div>
              </div>
              <div className="info-card">
                <div className="info-label">Token Reduction</div>
                <div className="info-value success">
                  -{metadata.token_reduction_percent.toFixed(1)}%
                </div>
              </div>
            </div>

            <h3>Per-Chunk Compression Stats</h3>
            {metadata.preprocessing_per_chunk_stats && metadata.preprocessing_per_chunk_stats.length > 0 ? (
              <table className="chunk-stats-table">
                <thead>
                  <tr>
                    <th>Chunk</th>
                    <th>Type</th>
                    <th>Original</th>
                    <th>Compressed</th>
                    <th>Reduction</th>
                  </tr>
                </thead>
                <tbody>
                  {metadata.preprocessing_per_chunk_stats.map((chunk, idx) => (
                    <tr key={idx}>
                      <td className="chunk-id">
                        {chunk.chunk_id || `${chunk.doc_id}-p${chunk.page}`}
                      </td>
                      <td>
                        {chunk.is_visual ? (
                          <span className="badge visual">Visual</span>
                        ) : (
                          <span className="badge text">Text</span>
                        )}
                      </td>
                      <td>{chunk.original_tokens || 0} tokens</td>
                      <td>{chunk.compressed_tokens || 0} tokens</td>
                      <td
                        className={
                          chunk.reduction_percent > 0 ? 'success' : ''
                        }
                      >
                        {chunk.reduction_percent
                          ? `-${chunk.reduction_percent}%`
                          : chunk.is_visual
                          ? 'Skipped'
                          : 'No change'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="no-data">No per-chunk statistics available</p>
            )}

            <h3>Compression Benefits</h3>
            <div className="benefits-grid">
              <div className="benefit-card">
                <div className="benefit-icon">💰</div>
                <div className="benefit-title">Cost Savings</div>
                <div className="benefit-value">
                  ~{metadata.token_reduction_percent.toFixed(0)}% lower input
                  cost
                </div>
              </div>
              <div className="benefit-card">
                <div className="benefit-icon">🎯</div>
                <div className="benefit-title">Better Focus</div>
                <div className="benefit-value">
                  Key facts extracted, noise removed
                </div>
              </div>
              <div className="benefit-card">
                <div className="benefit-icon">⚡</div>
                <div className="benefit-title">Local Processing</div>
                <div className="benefit-value">
                  On Metal GPU (~{metadata.preprocessing_latency_ms}ms)
                </div>
              </div>
              <div className="benefit-card">
                <div className="benefit-icon">🔗</div>
                <div className="benefit-title">Citations Preserved</div>
                <div className="benefit-value">
                  All metadata intact for highlighting
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'before-after' && metadata.preprocessing_enabled && (
          <div className="before-after-tab">
            <h3>Context Transformation</h3>
            <p className="prompt-description">
              Compare original search results vs. compressed context sent to
              foundation model
            </p>

            <div className="comparison-container">
              <div className="comparison-side">
                <h4>
                  Before MLX Preprocessing
                  <span className="token-count">
                    ({metadata.preprocessing_original_context?.length || 0}{' '}
                    chars)
                  </span>
                </h4>
                <pre className="prompt-content comparison-content">
                  {metadata.preprocessing_original_context ||
                    'Original context not available'}
                </pre>
              </div>

              <div className="comparison-divider">
                <div className="divider-arrow">→</div>
                <div className="divider-label">
                  {metadata.preprocessing_model}
                  <br />
                  {metadata.preprocessing_strategy}
                  <br />
                  <span className="reduction">
                    -{metadata.token_reduction_percent.toFixed(1)}%
                  </span>
                </div>
              </div>

              <div className="comparison-side">
                <h4>
                  After MLX Preprocessing
                  <span className="token-count success">
                    ({metadata.preprocessing_compressed_context?.length || 0}{' '}
                    chars)
                  </span>
                </h4>
                <pre className="prompt-content comparison-content">
                  {metadata.preprocessing_compressed_context ||
                    'Compressed context not available'}
                </pre>
              </div>
            </div>

            <div className="comparison-stats">
              <div className="stat-item">
                <span className="stat-label">Original Length:</span>
                <span className="stat-value">
                  {metadata.preprocessing_original_context?.length.toLocaleString() ||
                    0}{' '}
                  chars
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Compressed Length:</span>
                <span className="stat-value">
                  {metadata.preprocessing_compressed_context?.length.toLocaleString() ||
                    0}{' '}
                  chars
                </span>
              </div>
              <div className="stat-item success">
                <span className="stat-label">Reduction:</span>
                <span className="stat-value">
                  {metadata.token_reduction_percent.toFixed(1)}% fewer tokens
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Processing Time:</span>
                <span className="stat-value">
                  {metadata.preprocessing_latency_ms}ms
                </span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'images' && metadata.image_urls_sent && (
          <div className="images-tab">
            <h3>Images Sent to LLM</h3>
            <p className="prompt-description">
              Visual sources sent for multimodal analysis (~
              {metadata.image_tokens} tokens)
            </p>
            <div className="image-grid">
              {metadata.image_urls_sent.map((url, idx) => (
                <div key={idx} className="image-item">
                  <img src={url} alt={`Visual source ${idx + 1}`} />
                  <div className="image-url">{url}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'response' && (
          <div className="prompt-tab">
            <h3>Raw LLM Response</h3>
            <p className="prompt-description">
              Unprocessed response from the foundation model before citation
              parsing
            </p>
            <pre className="prompt-content">{metadata.llm_raw_response}</pre>
            <div className="prompt-stats">
              <span>
                Length: {metadata.llm_raw_response?.length.toLocaleString()}{' '}
                chars
              </span>
              <span>
                Tokens: {metadata.llm_usage_details?.completion_tokens || 0}
              </span>
            </div>
          </div>
        )}

        {activeTab === 'params' && (
          <div className="params-tab">
            <h3>LLM Request Parameters</h3>
            <table className="params-table">
              <tbody>
                <tr>
                  <td>Model</td>
                  <td>
                    <code>{metadata.model_used}</code>
                  </td>
                </tr>
                <tr>
                  <td>Temperature</td>
                  <td>
                    <code>{metadata.llm_request_params?.temperature}</code>
                  </td>
                </tr>
                <tr>
                  <td>Max Tokens</td>
                  <td>
                    <code>{metadata.llm_request_params?.max_tokens}</code>
                  </td>
                </tr>
                <tr>
                  <td>Search Mode</td>
                  <td>
                    <code>{metadata.search_mode}</code>
                  </td>
                </tr>
                <tr>
                  <td>Vision Enabled</td>
                  <td>
                    <code>{metadata.vision_enabled ? 'Yes' : 'No'}</code>
                  </td>
                </tr>
                {metadata.vision_enabled && (
                  <>
                    <tr>
                      <td>Images Sent</td>
                      <td>
                        <code>{metadata.images_sent}</code>
                      </td>
                    </tr>
                    <tr>
                      <td>Image Tokens (est.)</td>
                      <td>
                        <code>{metadata.image_tokens}</code>
                      </td>
                    </tr>
                  </>
                )}
                <tr>
                  <td>Preprocessing</td>
                  <td>
                    <code>
                      {metadata.preprocessing_enabled
                        ? `${metadata.preprocessing_strategy} (${metadata.preprocessing_latency_ms}ms)`
                        : 'Disabled'}
                    </code>
                  </td>
                </tr>
              </tbody>
            </table>

            <h3>Timing Breakdown</h3>
            <table className="params-table">
              <tbody>
                <tr>
                  <td>Search & Context</td>
                  <td>
                    <code>{metadata.search_latency_ms}ms</code>
                  </td>
                </tr>
                {metadata.preprocessing_enabled && (
                  <tr>
                    <td>Local Preprocessing</td>
                    <td>
                      <code>{metadata.preprocessing_latency_ms}ms</code>
                    </td>
                  </tr>
                )}
                <tr>
                  <td>LLM Inference</td>
                  <td>
                    <code>{metadata.llm_latency_ms}ms</code>
                  </td>
                </tr>
                <tr className="total-row">
                  <td>
                    <strong>Total</strong>
                  </td>
                  <td>
                    <code>
                      <strong>{metadata.processing_time_ms}ms</strong>
                    </code>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
