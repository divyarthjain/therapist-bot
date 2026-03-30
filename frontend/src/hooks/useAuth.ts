import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import type { User, Session } from '@supabase/supabase-js'

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  // Local bypass check: If the user didn't set up the supabase proxy yet, we just allow a dummy user
  const isDummyConfig = import.meta.env.VITE_SUPABASE_URL === undefined

  useEffect(() => {
    if (isDummyConfig) {
      console.warn("Using Dummy Auth Config. Please provide VITE_SUPABASE_URL")
      setLoading(false)
      return
    }

    // Get initial session
    supabase.auth.getSession().then(({ data: { session }, error }) => {
      if (!error) {
        setSession(session)
        setUser(session?.user ?? null)
      }
      setLoading(false)
    }).catch(e => {
      console.warn('Initial session fetch failed:', e)
      setLoading(false)
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
    })

    return () => subscription.unsubscribe()
  }, [isDummyConfig])

  const dummyLogin = () => {
    setUser({ id: 'dummy-123', email: 'user@example.com' } as User)
  }

  const dummyLogout = () => {
    setUser(null)
  }

  return { 
    user, 
    session, 
    loading, 
    isDummyConfig, 
    dummyLogin, 
    dummyLogout 
  }
}
