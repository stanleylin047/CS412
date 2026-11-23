import { Platform } from 'react-native';

const defaultOrigin = Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://127.0.0.1:8000';
const apiUrl = (process.env.EXPO_PUBLIC_API_URL || defaultOrigin + '/mini_insta/api').replace(/\/+$/, '');

function errorMessage(data) {
  if (typeof data?.detail === 'string') return data.detail;
  const messages = Object.entries(data ?? {}).flatMap(([field, value]) => {
    if (!Array.isArray(value)) return [];
    return value.map(message => field === 'non_field_errors' ? message : field + ': ' + message);
  });
  return messages.join('\n');
}

export async function request(path, { token, body, signal } = {}) {
  const headers = { Accept: 'application/json' };
  if (token) headers.Authorization = 'Token ' + token;
  if (body && !(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(body);
  }
  const response = await fetch(apiUrl + path, {
    method: body ? 'POST' : 'GET',
    headers,
    body,
    signal,
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const error = new Error(errorMessage(data) || 'Request failed (' + response.status + ').');
    error.status = response.status;
    throw error;
  }
  if (data === null) throw new Error('The server returned an empty or invalid response.');
  return data;
}
