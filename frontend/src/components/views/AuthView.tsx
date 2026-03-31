import { useState } from 'react'
import { supabase } from '../../lib/supabase'
import { useAuth } from '../../hooks/useAuth'
import './AuthView.css'

export function AuthView() {
  const { isDummyConfig, dummyLogin } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isSignUp, setIsSignUp] = useState(false)
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg(null)
    setLoading(true)

    try {
      if (isDummyConfig) {
        // Fallback to local dev login simulation if Supabase keys aren't provided
        dummyLogin()
        return
      }

      if (isSignUp) {
        const { error } = await supabase.auth.signUp({ email, password })
        if (error) throw error
        alert('Check your email for the confirmation link!')
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password })
        if (error) throw error
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  const handleGithubAuth = async () => {
    setErrorMsg(null)
    if (isDummyConfig) {
      dummyLogin()
      return
    }

    try {
      const { error } = await supabase.auth.signInWithOAuth({ provider: 'github' })
      if (error) throw error
    } catch (err: any) {
      setErrorMsg(err.message || 'GitHub Auth failed')
    }
  }

  return (
    <div className="auth-view flex-center">
      <div className="card text-center" style={{ width: '100%', maxWidth: '360px' }}>
        <h1 className="title-large" style={{ color: 'var(--color-primary-dark)' }}>
          Serenity
        </h1>
        <p className="text-body mb-4" style={{ fontSize: '13px' }}>
          Your AI Therapeutic Companion
        </p>

        {errorMsg && <div className="error-banner">{errorMsg}</div>}
        {isDummyConfig && (
          <div className="warning-banner mb-3" style={{ fontSize: '12px', background: '#FFF3CD', color: '#856404', padding: '8px', borderRadius: '8px' }}>
            Running in Local Mode (Mock Authentication). Provide VITE_SUPABASE_URL to wire real Auth.
          </div>
        )}

        {isDummyConfig && (
          <button
            type="button"
            className="btn-primary auth-local-btn"
            onClick={dummyLogin}
          >
            Enter Therapist Bot
          </button>
        )}

        <form onSubmit={handleAuth} className="auth-form">
          <input 
            type="email" 
            placeholder="Email (e.g. test@example.com)" 
            value={email}
            onChange={e => setEmail(e.target.value)}
            className="auth-input"
            required={!isDummyConfig}
          />
          <input 
            type="password" 
            placeholder="Password" 
            value={password}
            onChange={e => setPassword(e.target.value)}
            className="auth-input"
            required={!isDummyConfig}
          />
          
          <button type="submit" className="btn-primary mt-2" disabled={loading}>
            {loading ? 'Processing...' : (isSignUp ? 'Sign Up' : 'Log In')}
          </button>
        </form>

        {!isDummyConfig && (
          <div className="auth-divider">
            <span>OR</span>
          </div>
        )}

        {!isDummyConfig && (
          <button className="btn-secondary auth-github-btn" onClick={handleGithubAuth} disabled={loading}>
             <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" alt="GitHub" width="20" height="20" style={{ filter: 'invert(100%)' }} />
             Continue with GitHub
          </button>
        )}

        <p className="text-body mt-4" style={{ fontSize: '13px' }}>
           {isSignUp ? "Already have an account? " : "Don't have an account? "}
           <button 
             className="auth-link-btn"
             onClick={() => setIsSignUp(!isSignUp)}
             type="button"
           >
             {isSignUp ? "Log In" : "Sign Up"}
           </button>
        </p>

      </div>
    </div>
  )
}
