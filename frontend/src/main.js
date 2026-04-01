import { createApp } from 'vue'
import App from './App.vue'

const nativeFetch = window.fetch.bind(window)
window.fetch = (input, init = {}) => {
  const token = localStorage.getItem('token')
  const headers = new Headers(init.headers || {})
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  return nativeFetch(input, { ...init, headers })
}

createApp(App).mount('#app')
