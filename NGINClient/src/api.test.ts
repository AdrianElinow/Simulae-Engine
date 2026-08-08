import { describe, expect, it, vi } from 'vitest'

import { fetchApiIndex, invokeApiEndpoint } from './api'

describe('NGIN API client', () => {
  it('loads the API definition from the proxy route', async () => {
    const fetcher = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          message: 'NGIN Campaign Generator API is running.',
          endpoints: [{ method: 'GET', path: '/api/generate_campaign', summary: 'Generate a campaign.' }],
        }),
        { status: 200 },
      ),
    )

    const apiIndex = await fetchApiIndex(fetcher)

    expect(fetcher).toHaveBeenCalledWith('/api')
    expect(apiIndex.endpoints[0]?.path).toBe('/api/generate_campaign')
  })

  it('returns status and parsed JSON for an endpoint request', async () => {
    const fetcher = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ID: 'state' }), { status: 200, statusText: 'OK' }),
    )

    const response = await invokeApiEndpoint(
      { method: 'GET', path: '/api/generate_campaign', summary: 'Generate a campaign.' },
      fetcher,
    )

    expect(fetcher).toHaveBeenCalledWith('/api/generate_campaign', { method: 'GET' })
    expect(response).toEqual({ status: 200, statusText: 'OK', data: { ID: 'state' } })
  })
})
