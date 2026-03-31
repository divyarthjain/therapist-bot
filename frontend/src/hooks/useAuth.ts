import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import type { User, Session } from '@supabase/supabase-js'

const DUMMY_AUTH_STORAGE_KEY = 'serenity_dummy_auth'
const DUMMY_AUTH_EVENT = 'serenity-dummy-auth-change'

function createDummyUser(): User {
  return {
    id: 'dummy-123',
    email: 'local@serenity.dev',
  } as User
}

function readDummyAuthState(): boolean {
  if (typeof window === 'undefined') {
    return true
  }

  const stored = window.localStorage.getItem(DUMMY_AUTH_STORAGE_KEY)
  return stored !== 'signed_out'
}

function broadcastDummyAuthChange() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event(DUMMY_AUTH_EVENT))
  }
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  const isDummyConfig =
    !import.meta.env.VITE_SUPABASE_URL ||
    !import.meta.env.VITE_SUPABASE_ANON_KEY ||
    import.meta.env.VITE_SUPABASE_URL === 'https://xxxxx.supabase.co'

  useEffect(() => {
    if (isDummyConfig) {
      const syncDummyAuth = () => {
        setSession(null)
        setUser(readDummyAuthState() ? createDummyUser() : null)
        setLoading(false)
      }

      console.warn('Using Dummy Auth Config. Please provide VITE_SUPABASE_URL')
      syncDummyAuth()
      window.addEventListener(DUMMY_AUTH_EVENT, syncDummyAuth)
      window.addEventListener('storage', syncDummyAuth)

      return () => {
        window.removeEventListener(DUMMY_AUTH_EVENT, syncDummyAuth)
        window.removeEventListener('storage', syncDummyAuth)
      }
    }

    let isActive = true

    const loadSession = async () => {
      try {
        const { data: { session }, error } = await supabase.auth.getSession()
        if (!error && isActive) {
          setSession(session)
          setUser(session?.user ?? null)
        }
      } catch (e) {
        console.warn('Initial session fetch failed:', e)
      } finally {
        if (isActive) {
          setLoading(false)
        }
      }
    }

    loadSession()

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    return () => {
      isActive = false
      subscription.unsubscribe()
    }
  }, [isDummyConfig])

  const dummyLogin = () => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(DUMMY_AUTH_STORAGE_KEY, 'signed_in')
    }
    setUser(createDummyUser())
    broadcastDummyAuthChange()
  }

  const dummyLogout = () => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(DUMMY_AUTH_STORAGE_KEY, 'signed_out')
    }
    setUser(null)
    broadcastDummyAuthChange()
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
