export interface ApiEndpoint {
  method: 'GET'
  path: string
  summary: string
}

export interface ApiIndex {
  message: string
  endpoints: ApiEndpoint[]
}

export interface ApiResponse {
  status: number
  statusText: string
  data: unknown
}

type Fetcher = typeof fetch

async function parseResponse(response: Response): Promise<unknown> {
  const text = await response.text()

  if (!text) {
    return null
  }

  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

export async function fetchApiIndex(fetcher: Fetcher = fetch): Promise<ApiIndex> {
  const response = await fetcher('/api')
  const data = await parseResponse(response)

  if (!response.ok) {
    throw new Error(`Unable to load API definition (${response.status})`)
  }

  return data as ApiIndex
}

export async function invokeApiEndpoint(
  endpoint: ApiEndpoint,
  fetcher: Fetcher = fetch,
): Promise<ApiResponse> {
  const response = await fetcher(endpoint.path, { method: endpoint.method })

  return {
    status: response.status,
    statusText: response.statusText,
    data: await parseResponse(response),
  }
}
