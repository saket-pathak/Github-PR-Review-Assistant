import { useState, useEffect } from 'react';

interface Review {
  id: number;
  platform: 'github' | 'gitlab' | 'bitbucket';
  repo: string;
  pr_number: number;
  status: 'success' | 'failure';
  summary: string;
  comments_posted: number;
  created_at: string;
}

export default function App() {
  const [history, setHistory] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [platform, setPlatform] = useState<'github' | 'gitlab' | 'bitbucket'>('github');
  const [repo, setRepo] = useState('');
  const [prNumber, setPrNumber] = useState('');
  const [selectedReview, setSelectedReview] = useState<Review | null>(null);
  
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Fetch reviews history
  const fetchHistory = async () => {
    try {
      const res = await fetch('/api/history');
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (err) {
      console.error('Failed to fetch history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  // Trigger manual review
  const handleTriggerReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repo || !prNumber) {
      setError('Please fill in all fields.');
      return;
    }

    setError(null);
    setSuccess(null);
    setSubmitting(true);

    try {
      const res = await fetch('/review', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          repo,
          pr_number: parseInt(prNumber, 10),
          platform,
        }),
      });

      const result = await res.json();

      if (res.ok && result.status !== 'mocked') {
        setSuccess(`Review successfully completed! Summary: ${result.summary.slice(0, 100)}...`);
        setRepo('');
        setPrNumber('');
        fetchHistory();
      } else if (result.status === 'mocked') {
        setError(`Warning: Review was run but return status is mocked: ${result.summary}`);
        fetchHistory();
      } else {
        setError(result.detail || 'Failed to trigger review.');
      }
    } catch (err) {
      setError('Connection failed. Verify if the FastAPI backend is running.');
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  // Compute metrics
  const totalReviewed = history.length;
  const totalComments = history.reduce((sum, item) => sum + item.comments_posted, 0);
  const successReviews = history.filter(item => item.status === 'success').length;
  const successRate = totalReviewed > 0 ? Math.round((successReviews / totalReviewed) * 100) : 100;
  const uniqueRepos = new Set(history.map(item => item.repo)).size;

  // SVG Icons
  const GitIcon = ({ type }: { type: 'github' | 'gitlab' | 'bitbucket' }) => {
    if (type === 'github') {
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" style={{ marginRight: '6px' }}>
          <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
        </svg>
      );
    }
    if (type === 'gitlab') {
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="#FC6D26" style={{ marginRight: '6px' }}>
          <path d="M23.953 13.072l-1.66-5.11a.48.48 0 0 0-.18-.255.485.485 0 0 0-.306-.06.486.486 0 0 0-.276.136L12 16.515 2.47 7.783a.483.483 0 0 0-.276-.135.484.484 0 0 0-.306.06.48.48 0 0 0-.18.256L.047 13.072a.852.852 0 0 0 .307.945l11.17 8.125a.81.81 0 0 0 .953 0l11.17-8.125a.852.852 0 0 0 .306-.945z" />
        </svg>
      );
    }
    return (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="#0052CC" style={{ marginRight: '6px' }}>
        <path d="M22.5 0h-21C.672 0 0 .672 0 1.5v21c0 .828.672 1.5 1.5 1.5h21c.828 0 1.5-.672 1.5-1.5v-21c0-.828-.672-1.5-1.5-1.5zm-1.748 11.238l-4.148 4.29a.91.91 0 0 1-.652.274H8.718a.91.91 0 0 1-.652-.274l-4.148-4.29a.952.952 0 0 1-.22-.924.965.965 0 0 1 .632-.693l6.556-2.176a.915.915 0 0 1 .586 0l6.556 2.176c.294.1.488.375.534.693a.952.952 0 0 1-.22.924z"/>
      </svg>
    );
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '40px 20px' }}>
      
      {/* Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '40px' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '32px', display: 'flex', alignItems: 'center', letterSpacing: '-0.8px' }}>
            <span style={{ color: 'var(--primary)', marginRight: '10px' }}>⚡</span> Antigravity Review Assistant
          </h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: '4px', fontSize: '15px' }}>
            Interactive AI code review pipeline & stats control
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', background: 'var(--bg-card)', padding: '10px 16px', borderRadius: '12px', border: '1px solid var(--border-glow)' }}>
          <span style={{ display: 'inline-block', width: '10px', height: '10px', backgroundColor: 'var(--status-success)', borderRadius: '50%', marginRight: '8px', boxShadow: '0 0 8px var(--status-success)' }}></span>
          <span style={{ fontSize: '14px', fontWeight: 600 }}>System Connected</span>
        </div>
      </header>

      {/* KPI Cards Grid */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', marginBottom: '40px' }}>
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '13px', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 600 }}>Total Reviewed</div>
          <div style={{ fontSize: '42px', fontWeight: 800, marginTop: '8px', color: 'var(--primary)' }}>{totalReviewed}</div>
        </div>
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '13px', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 600 }}>Comments Posted</div>
          <div style={{ fontSize: '42px', fontWeight: 800, marginTop: '8px', color: 'var(--text-primary)' }}>{totalComments}</div>
        </div>
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '13px', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 600 }}>Success Rate</div>
          <div style={{ fontSize: '42px', fontWeight: 800, marginTop: '8px', color: 'var(--status-success)' }}>{successRate}%</div>
        </div>
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '13px', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 600 }}>Monitored Repos</div>
          <div style={{ fontSize: '42px', fontWeight: 800, marginTop: '8px', color: 'var(--accent)' }}>{uniqueRepos}</div>
        </div>
      </section>

      {/* Form and Quick Actions */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '30px', marginBottom: '40px' }}>
        
        {/* Trigger Review Form */}
        <div className="glass-card" style={{ padding: '32px' }}>
          <h2 style={{ fontSize: '20px', marginBottom: '20px', display: 'flex', alignItems: 'center' }}>
            <span style={{ color: 'var(--primary)', marginRight: '8px' }}>🚀</span> Trigger Review Manually
          </h2>
          
          <form onSubmit={handleTriggerReview} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            
            {/* Platform Selection */}
            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '14px', color: 'var(--text-secondary)', fontWeight: 600 }}>Select VCS Platform</label>
              <div style={{ display: 'flex', gap: '10px' }}>
                {(['github', 'gitlab', 'bitbucket'] as const).map(p => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setPlatform(p)}
                    style={{
                      flex: 1,
                      padding: '12px 8px',
                      borderRadius: '8px',
                      border: platform === p ? '1px solid var(--primary)' : '1px solid var(--border-glow)',
                      backgroundColor: platform === p ? 'rgba(102, 252, 241, 0.08)' : 'transparent',
                      color: platform === p ? 'var(--primary)' : 'var(--text-secondary)',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 600,
                      textTransform: 'capitalize',
                      transition: 'all 0.2s',
                    }}
                  >
                    <GitIcon type={p} />
                    {p}
                  </button>
                ))}
              </div>
            </div>

            {/* Repo Field */}
            <div>
              <label htmlFor="repo" style={{ display: 'block', marginBottom: '6px', fontSize: '14px', color: 'var(--text-secondary)', fontWeight: 600 }}>Repository Path</label>
              <input
                id="repo"
                type="text"
                placeholder={platform === 'gitlab' ? 'gitlab-org/gitlab' : 'owner/repo'}
                value={repo}
                onChange={e => setRepo(e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-glow)',
                  backgroundColor: 'var(--bg-input)',
                  color: '#fff',
                  fontSize: '15px',
                  outline: 'none',
                }}
              />
            </div>

            {/* PR Number */}
            <div>
              <label htmlFor="prNumber" style={{ display: 'block', marginBottom: '6px', fontSize: '14px', color: 'var(--text-secondary)', fontWeight: 600 }}>
                {platform === 'gitlab' ? 'Merge Request ID' : 'Pull Request Number'}
              </label>
              <input
                id="prNumber"
                type="number"
                placeholder="42"
                value={prNumber}
                onChange={e => setPrNumber(e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-glow)',
                  backgroundColor: 'var(--bg-input)',
                  color: '#fff',
                  fontSize: '15px',
                  outline: 'none',
                }}
              />
            </div>

            {/* Feedback Alerts */}
            {error && (
              <div style={{ backgroundColor: 'var(--status-failure-bg)', border: '1px solid var(--status-failure)', color: '#fff', padding: '12px 16px', borderRadius: '8px', fontSize: '14px' }}>
                <strong>Error:</strong> {error}
              </div>
            )}
            {success && (
              <div style={{ backgroundColor: 'var(--status-success-bg)', border: '1px solid var(--status-success)', color: '#fff', padding: '12px 16px', borderRadius: '8px', fontSize: '14px' }}>
                <strong>Success:</strong> {success}
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={submitting}
              style={{
                padding: '14px',
                borderRadius: '8px',
                border: 'none',
                backgroundColor: submitting ? 'var(--bg-input)' : 'var(--primary)',
                color: '#000',
                fontWeight: 700,
                fontSize: '15px',
                cursor: submitting ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px',
                transition: 'background-color 0.2s',
              }}
            >
              {submitting ? (
                <>
                  <span className="spinner"></span> Running AI Review...
                </>
              ) : (
                'Trigger Pipeline Review'
              )}
            </button>

          </form>
        </div>

        {/* Integration Instructions Card */}
        <div className="glass-card" style={{ padding: '32px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <h2 style={{ fontSize: '20px', marginBottom: '20px' }}>⚙️ Integration Reference</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px', lineHeight: 1.6, marginBottom: '16px' }}>
              The Antigravity PR Review Assistant automatically records webhook triggers and manual runs. Make sure your environment configurations are set:
            </p>
            <ul style={{ color: 'var(--text-muted)', fontSize: '13px', paddingLeft: '20px', lineHeight: 1.8 }}>
              <li><code>GITHUB_TOKEN</code> set for GitHub comments</li>
              <li><code>GITLAB_TOKEN</code> set for GitLab comments</li>
              <li><code>BITBUCKET_TOKEN</code> / <code>BITBUCKET_USERNAME</code> set for Bitbucket comments</li>
              <li><code>LLM_PROVIDER</code> (anthropic, openai) set to your preference</li>
            </ul>
          </div>

          <div style={{ borderTop: '1px solid var(--border-glow)', paddingTop: '20px', marginTop: '20px' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>CACHE STORAGE:</div>
            <div style={{ fontSize: '14px', fontFamily: 'var(--font-mono)', color: 'var(--primary)', marginTop: '4px' }}>
              sqlite3://.review_cache.db
            </div>
          </div>
        </div>

      </section>

      {/* History Log Section */}
      <section className="glass-card" style={{ padding: '32px', overflowX: 'auto' }}>
        <h2 style={{ fontSize: '20px', marginBottom: '20px', display: 'flex', alignItems: 'center' }}>
          <span style={{ color: 'var(--accent)', marginRight: '8px' }}>🕒</span> Execution History Log
        </h2>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <span className="spinner" style={{ width: '2.5rem', height: '2.5rem' }}></span>
            <p style={{ color: 'var(--text-muted)', marginTop: '16px' }}>Loading runs history...</p>
          </div>
        ) : history.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
            No code reviews have been run yet. Use the trigger panel above or raise a PR to start.
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: '700px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-glow)' }}>
                <th style={{ padding: '12px', color: 'var(--text-muted)', fontSize: '13px', textTransform: 'uppercase' }}>Platform</th>
                <th style={{ padding: '12px', color: 'var(--text-muted)', fontSize: '13px', textTransform: 'uppercase' }}>Repository</th>
                <th style={{ padding: '12px', color: 'var(--text-muted)', fontSize: '13px', textTransform: 'uppercase' }}>PR / MR #</th>
                <th style={{ padding: '12px', color: 'var(--text-muted)', fontSize: '13px', textTransform: 'uppercase' }}>Status</th>
                <th style={{ padding: '12px', color: 'var(--text-muted)', fontSize: '13px', textTransform: 'uppercase' }}>Comments</th>
                <th style={{ padding: '12px', color: 'var(--text-muted)', fontSize: '13px', textTransform: 'uppercase' }}>Completed At</th>
                <th style={{ padding: '12px', color: 'var(--text-muted)', fontSize: '13px', textTransform: 'uppercase', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {history.map(item => (
                <tr key={item.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.03)' }}>
                  <td style={{ padding: '16px 12px', display: 'flex', alignItems: 'center', textTransform: 'uppercase', fontSize: '13px', fontWeight: 700 }}>
                    <GitIcon type={item.platform} /> {item.platform}
                  </td>
                  <td style={{ padding: '16px 12px', fontWeight: 600 }}>{item.repo}</td>
                  <td style={{ padding: '16px 12px', fontFamily: 'var(--font-mono)' }}>#{item.pr_number}</td>
                  <td style={{ padding: '16px 12px' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '4px 10px',
                      borderRadius: '20px',
                      fontSize: '12px',
                      fontWeight: 700,
                      backgroundColor: item.status === 'success' ? 'var(--status-success-bg)' : 'var(--status-failure-bg)',
                      color: item.status === 'success' ? 'var(--status-success)' : 'var(--status-failure)',
                      boxShadow: item.status === 'success' ? '0 0 6px rgba(46, 204, 113, 0.1)' : '0 0 6px rgba(231, 76, 60, 0.1)',
                    }}>
                      {item.status}
                    </span>
                  </td>
                  <td style={{ padding: '16px 12px', fontWeight: 600 }}>{item.comments_posted}</td>
                  <td style={{ padding: '16px 12px', color: 'var(--text-muted)', fontSize: '14px' }}>
                    {new Date(item.created_at).toLocaleString()}
                  </td>
                  <td style={{ padding: '16px 12px', textAlign: 'right' }}>
                    <button
                      onClick={() => setSelectedReview(item)}
                      style={{
                        padding: '6px 12px',
                        borderRadius: '6px',
                        border: '1px solid var(--primary)',
                        backgroundColor: 'transparent',
                        color: 'var(--primary)',
                        cursor: 'pointer',
                        fontSize: '13px',
                        fontWeight: 600,
                        transition: 'all 0.2s',
                      }}
                      onMouseEnter={e => {
                        e.currentTarget.style.backgroundColor = 'var(--primary)';
                        e.currentTarget.style.color = '#000';
                      }}
                      onMouseLeave={e => {
                        e.currentTarget.style.backgroundColor = 'transparent';
                        e.currentTarget.style.color = 'var(--primary)';
                      }}
                    >
                      View Report
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {/* Review Details Modal */}
      {selectedReview && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundColor: 'rgba(0,0,0,0.85)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000,
          backdropFilter: 'blur(8px)',
        }}>
          <div className="glass-card" style={{
            width: '80%',
            maxWidth: '800px',
            maxHeight: '85vh',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            border: '1px solid var(--primary)',
            boxShadow: '0 0 30px rgba(102, 252, 241, 0.15)',
          }}>
            {/* Modal Header */}
            <div style={{
              padding: '24px 32px',
              borderBottom: '1px solid var(--border-glow)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '20px', display: 'flex', alignItems: 'center' }}>
                  <GitIcon type={selectedReview.platform} />
                  {selectedReview.repo} | PR #{selectedReview.pr_number} Review
                </h3>
                <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                  ID: #{selectedReview.id} | Ran on {new Date(selectedReview.created_at).toLocaleString()}
                </span>
              </div>
              <button
                onClick={() => setSelectedReview(null)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-secondary)',
                  fontSize: '24px',
                  cursor: 'pointer',
                }}
              >
                &times;
              </button>
            </div>

            {/* Modal Content */}
            <div style={{ padding: '32px', overflowY: 'auto', flex: 1 }}>
              <h4 style={{ margin: '0 0 10px', fontSize: '16px', color: 'var(--primary)' }}>🤖 Summary Report</h4>
              <div style={{
                backgroundColor: 'var(--bg-input)',
                padding: '20px',
                borderRadius: '8px',
                fontSize: '15px',
                lineHeight: 1.6,
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-sans)',
                whiteSpace: 'pre-wrap',
                border: '1px solid var(--border-glow)',
                marginBottom: '20px',
              }}>
                {selectedReview.summary}
              </div>

              <div style={{ display: 'flex', gap: '20px', fontSize: '14px', borderTop: '1px solid var(--border-glow)', paddingTop: '20px' }}>
                <div>
                  <strong style={{ color: 'var(--text-muted)' }}>Status: </strong>
                  <span style={{ color: selectedReview.status === 'success' ? 'var(--status-success)' : 'var(--status-failure)' }}>
                    {selectedReview.status.toUpperCase()}
                  </span>
                </div>
                <div>
                  <strong style={{ color: 'var(--text-muted)' }}>Inline Comments Placed: </strong>
                  <span>{selectedReview.comments_posted}</span>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div style={{
              padding: '16px 32px',
              borderTop: '1px solid var(--border-glow)',
              textAlign: 'right',
              backgroundColor: 'rgba(25, 26, 33, 0.4)',
            }}>
              <button
                onClick={() => setSelectedReview(null)}
                style={{
                  padding: '10px 20px',
                  borderRadius: '6px',
                  border: 'none',
                  backgroundColor: 'var(--primary)',
                  color: '#000',
                  fontWeight: 700,
                  cursor: 'pointer',
                }}
              >
                Close Report
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
