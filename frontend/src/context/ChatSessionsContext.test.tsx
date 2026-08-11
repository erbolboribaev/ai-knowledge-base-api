import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { ChatSessionsProvider, useChatSessions } from './ChatSessionsContext'

describe('ChatSessionsContext', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('starts with one default session', () => {
    const { result } = renderHook(() => useChatSessions(), {
      wrapper: ChatSessionsProvider,
    })
    expect(result.current.sessions).toHaveLength(1)
    expect(result.current.sessions[0].title).toBe('New chat')
  })

  it('adds a new session to the front of the list', () => {
    const { result } = renderHook(() => useChatSessions(), {
      wrapper: ChatSessionsProvider,
    })

    act(() => {
      result.current.newSession()
    })

    expect(result.current.sessions).toHaveLength(2)
  })

  it('caps sessions at 10, dropping the oldest', () => {
    const { result } = renderHook(() => useChatSessions(), {
      wrapper: ChatSessionsProvider,
    })

    act(() => {
      for (let i = 0; i < 15; i++) {
        result.current.newSession()
      }
    })

    expect(result.current.sessions).toHaveLength(10)
  })

  it('updateSession only modifies the matching session', () => {
    const { result } = renderHook(() => useChatSessions(), {
      wrapper: ChatSessionsProvider,
    })

    const firstId = result.current.sessions[0].id

    act(() => {
      result.current.updateSession(firstId, (s) => ({ ...s, title: 'Renamed' }))
    })

    expect(result.current.getSession(firstId)?.title).toBe('Renamed')
  })
})
