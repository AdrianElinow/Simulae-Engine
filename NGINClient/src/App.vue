<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { fetchApiIndex, invokeApiEndpoint, type ApiEndpoint, type ApiResponse } from './api'

const defaultEndpoint: ApiEndpoint = {
  method: 'GET',
  path: '/api/generate_campaign',
  summary: 'Generate a new campaign world state.',
}
const fallbackEndpoints: ApiEndpoint[] = [defaultEndpoint]

const apiMessage = ref('Loading API definition…')
const endpoints = ref<ApiEndpoint[]>(fallbackEndpoints)
const selectedPath = ref(defaultEndpoint.path)
const isLoadingDefinition = ref(false)
const isSendingRequest = ref(false)
const error = ref('')
const response = ref<ApiResponse | null>(null)

const selectedEndpoint = computed<ApiEndpoint>(
  () => endpoints.value.find((endpoint) => endpoint.path === selectedPath.value) ?? defaultEndpoint,
)

const formattedResponse = computed(() => (
  response.value ? JSON.stringify(response.value.data, null, 2) : 'Send a request to view the response body.'
))

async function loadApiDefinition() {
  isLoadingDefinition.value = true
  error.value = ''

  try {
    const apiIndex = await fetchApiIndex()
    apiMessage.value = apiIndex.message
    endpoints.value = apiIndex.endpoints.length ? apiIndex.endpoints : fallbackEndpoints
    selectedPath.value = endpoints.value[0]?.path ?? defaultEndpoint.path
  } catch (caughtError) {
    error.value = caughtError instanceof Error ? caughtError.message : 'Unable to load API definition.'
    apiMessage.value = 'Using the built-in API definition.'
  } finally {
    isLoadingDefinition.value = false
  }
}

async function sendRequest() {
  isSendingRequest.value = true
  error.value = ''

  try {
    response.value = await invokeApiEndpoint(selectedEndpoint.value)
  } catch (caughtError) {
    error.value = caughtError instanceof Error ? caughtError.message : 'Request failed.'
    response.value = null
  } finally {
    isSendingRequest.value = false
  }
}

onMounted(loadApiDefinition)
</script>

<template>
  <main class="api-console">
    <header class="hero">
      <p class="eyebrow">NGIN Campaign Generator</p>
      <h1>API Explorer</h1>
      <p>{{ apiMessage }}</p>
    </header>

    <section class="endpoint-card" aria-labelledby="endpoint-heading">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Available operation</p>
          <h2 id="endpoint-heading">Send a campaign request</h2>
        </div>
        <button type="button" class="secondary-button" :disabled="isLoadingDefinition" @click="loadApiDefinition">
          {{ isLoadingDefinition ? 'Refreshing…' : 'Refresh definition' }}
        </button>
      </div>

      <label class="endpoint-picker" for="api-endpoint">
        <span>Endpoint</span>
        <select id="api-endpoint" v-model="selectedPath" :disabled="isSendingRequest">
          <option v-for="endpoint in endpoints" :key="endpoint.path" :value="endpoint.path">
            {{ endpoint.method }} {{ endpoint.path }}
          </option>
        </select>
      </label>

      <div class="operation-summary">
        <span class="method">{{ selectedEndpoint.method }}</span>
        <code>{{ selectedEndpoint.path }}</code>
        <span>{{ selectedEndpoint.summary }}</span>
      </div>

      <button type="button" class="send-button" :disabled="isSendingRequest" @click="sendRequest">
        {{ isSendingRequest ? 'Generating campaign…' : 'Send request' }}
      </button>
    </section>

    <section class="response-card" aria-labelledby="response-heading">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Response</p>
          <h2 id="response-heading">Server output</h2>
        </div>
        <span v-if="response" class="status" :class="{ failed: response.status >= 400 }">
          {{ response.status }} {{ response.statusText }}
        </span>
      </div>

      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <pre aria-live="polite">{{ formattedResponse }}</pre>
    </section>
  </main>
</template>
